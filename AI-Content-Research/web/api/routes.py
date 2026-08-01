"""
FastAPI routes for the AI Content Research Framework.

Endpoints:
  POST /api/search   - Search YouTube and return raw videos
  POST /api/analyze  - Search + run both LLM analyzers, stream progress via SSE
  GET  /api/info     - Return current system config (models, Ollama URL)
"""

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config.settings import get_settings
from core.models import Platform, TaskType, AnalysisRequest
from platforms.youtube import YouTubePlatform
from analysis.youtube import YouTubeTitleAnalyzer, YouTubeTrendAnalyzer
from infrastructure.storage import FileStorage
from infrastructure.logging import setup_logging

setup_logging()
router = APIRouter()


# ── Request schemas ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10


class AnalyzeRequest(BaseModel):
    query: str
    max_results: int = 10


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_info():
    """Return current system configuration."""
    s = get_settings()
    return {
        "ollama_host": s.ollama.base_url,
        "extraction_model": s.models.extraction_model,
        "reasoning_model": s.models.reasoning_model,
        "browser_headless": s.browser.headless,
        "output_dir": s.storage.output_dir,
    }


@router.post("/search")
async def search_youtube(req: SearchRequest):
    """Search YouTube and return a list of extracted videos."""
    platform = YouTubePlatform()
    items = await platform.search(query=req.query, max_results=req.max_results)
    return {
        "query": req.query,
        "total": len(items),
        "videos": [
            {
                "id": v.id,
                "title": v.title,
                "url": v.url,
                "channel": v.author_name,
                "views": v.get_meta("view_count", 0),
                "duration_text": v.get_meta("duration_text", ""),
                "duration_seconds": v.get_meta("duration_seconds", 0),
                "is_short": v.get_meta("is_short", False),
            }
            for v in items
        ],
    }


@router.post("/analyze")
async def analyze_youtube(req: AnalyzeRequest):
    """
    Full pipeline: scrape YouTube → analyze titles (Qwen3) → analyze trends (DeepSeek R1).
    Returns a Server-Sent Events stream of progress messages followed by results.
    """

    async def event_stream() -> AsyncIterator[str]:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        try:
            # Phase 1: Scraping
            yield sse("progress", {"phase": 1, "message": f"🔍 Scraping YouTube for '{req.query}'..."})
            platform = YouTubePlatform()
            items = await platform.search(query=req.query, max_results=req.max_results)

            if not items:
                yield sse("error", {"message": "No videos found. Try a different query."})
                return

            videos_payload = [
                {
                    "id": v.id,
                    "title": v.title,
                    "url": v.url,
                    "channel": v.author_name,
                    "views": v.get_meta("view_count", 0),
                    "duration_text": v.get_meta("duration_text", ""),
                    "duration_seconds": v.get_meta("duration_seconds", 0),
                    "is_short": v.get_meta("is_short", False),
                }
                for v in items
            ]
            yield sse("videos", {"videos": videos_payload, "total": len(items)})

            analysis_req = AnalysisRequest(
                query=req.query,
                platform=Platform.YOUTUBE,
                task_types=[TaskType.CLASSIFICATION, TaskType.TREND_ANALYSIS],
                max_items=len(items),
            )

            # Phase 2: Title Analysis (Qwen3)
            yield sse("progress", {"phase": 2, "message": "🧠 Analyzing title patterns with Qwen3 14B..."})
            title_result = await YouTubeTitleAnalyzer().analyze(analysis_req, items)
            title_text = title_result.findings[0].description if title_result.findings else ""
            yield sse("title_analysis", {"content": title_text})

            # Phase 3: Trend Analysis (DeepSeek R1)
            yield sse("progress", {"phase": 3, "message": "🔬 Reasoning market trends with DeepSeek R1 8B..."})
            trend_result = await YouTubeTrendAnalyzer().analyze(analysis_req, items)
            trend_text = trend_result.findings[0].description if trend_result.findings else ""
            yield sse("trend_analysis", {"content": trend_text})

            # Save reports
            storage = FileStorage()
            path1 = await storage.save_analysis(title_result)
            path2 = await storage.save_analysis(trend_result)

            yield sse("done", {
                "message": "✅ Analysis complete!",
                "report_paths": [str(path1), str(path2)],
            })

        except Exception as e:
            yield sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
