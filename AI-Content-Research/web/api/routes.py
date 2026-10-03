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

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, SecretStr

from config.settings import get_settings
from core.models import Platform, TaskType, AnalysisRequest
from core.models.provider import LLMRoutingConfig
from core.exceptions import LLMError
from platforms.youtube import YouTubePlatform
from analysis.youtube import YouTubeTitleAnalyzer, YouTubeTrendAnalyzer
from infrastructure.storage import FileStorage
from infrastructure.logging import setup_logging
from infrastructure.llm.runtime import get_llm_configuration, get_provider_registry

setup_logging()
router = APIRouter()


# ── Request schemas ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10


class AnalyzeRequest(BaseModel):
    query: str
    max_results: int = 10


class ProviderConnectRequest(BaseModel):
    api_key: SecretStr


def serialize_video(video) -> dict:
    """Stable API representation shared by search and streaming analysis."""
    return {
        "id": str(video.id),
        "title": str(video.title),
        "url": str(video.url) if video.url else "",
        "channel": str(video.author_name or ""),
        "views": video.get_meta("view_count", 0),
        "published_at": video.published_at.isoformat() if video.published_at else None,
        "published_text": video.get_meta("published_text"),
        "age_days": video.get_meta("age_days"),
        "views_per_day": video.get_meta("views_per_day"),
        "duration_text": str(video.get_meta("duration_text", "")),
        "duration_seconds": video.get_meta("duration_seconds", 0),
        "is_short": bool(video.get_meta("is_short", False)),
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_info():
    """Return current system configuration."""
    s = get_settings()
    registry = get_provider_registry()
    routes = get_llm_configuration().get()
    provider_names = {item["id"]: item["name"] for item in registry.descriptors()}
    providers_used = {routes.extraction.provider_id, routes.reasoning.provider_id}
    provider_label = (
        provider_names.get(routes.extraction.provider_id, routes.extraction.provider_id)
        if len(providers_used) == 1
        else "Configuración mixta"
    )
    return {
        "ollama_host": s.ollama.base_url,
        "extraction_provider": routes.extraction.provider_id,
        "extraction_provider_name": provider_names.get(routes.extraction.provider_id, routes.extraction.provider_id),
        "extraction_model": routes.extraction.model,
        "reasoning_provider": routes.reasoning.provider_id,
        "reasoning_provider_name": provider_names.get(routes.reasoning.provider_id, routes.reasoning.provider_id),
        "reasoning_model": routes.reasoning.model,
        "provider_label": provider_label,
        "processing_local": all(provider_id == "ollama" for provider_id in providers_used),
        "browser_headless": s.browser.headless,
        "output_dir": s.storage.output_dir,
    }


@router.get("/providers")
async def list_providers():
    """Return supported providers and the process-local routing configuration."""
    return {
        "providers": get_provider_registry().descriptors(),
        "routes": get_llm_configuration().get().model_dump(),
        "credential_storage": "session",
    }


@router.get("/providers/{provider_id}/models")
async def list_provider_models(provider_id: str):
    try:
        provider = get_provider_registry().get(provider_id)
        models = await provider.list_models()
        return {"provider_id": provider_id, "models": [model.model_dump() for model in models]}
    except LLMError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/providers/{provider_id}/connect")
async def connect_provider(provider_id: str, req: ProviderConnectRequest):
    """Validate a key and retain it only in backend memory for this process."""
    registry = get_provider_registry()
    try:
        credential = req.api_key.get_secret_value()
        provider = registry.create_with_credential(provider_id, credential)
        models = await provider.list_models()
        if not models:
            raise LLMError(
                "El proveedor no devolvió modelos compatibles con generación de texto.",
                context={"provider": provider_id},
            )
        registry.set_credential(provider_id, credential)
        return {
            "provider_id": provider_id,
            "configured": True,
            "models": [model.model_dump() for model in models],
        }
    except (LLMError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/providers/{provider_id}/credential")
async def disconnect_provider(provider_id: str):
    registry = get_provider_registry()
    if provider_id == "ollama":
        raise HTTPException(status_code=400, detail="Ollama no utiliza una credencial de sesión.")
    registry.delete_credential(provider_id)
    still_configured = registry.is_configured(provider_id)
    routes = (
        get_llm_configuration().get()
        if still_configured
        else get_llm_configuration().reset_provider(provider_id)
    )
    return {
        "provider_id": provider_id,
        "configured": still_configured,
        "credential_source": "environment" if still_configured else None,
        "routes": routes.model_dump(),
    }


@router.put("/providers/configuration/routes")
async def update_provider_routes(config: LLMRoutingConfig):
    registry = get_provider_registry()
    try:
        model_cache: dict[str, set[str]] = {}
        for route in (config.extraction, config.reasoning):
            if route.provider_id not in registry.supported_ids:
                raise LLMError(f"Proveedor no soportado: {route.provider_id}")
            if not registry.is_configured(route.provider_id):
                raise LLMError(f"El proveedor {route.provider_id} no está configurado.")
            if route.provider_id not in model_cache:
                provider_models = await registry.get(route.provider_id).list_models()
                model_cache[route.provider_id] = {model.id for model in provider_models}
            if route.model not in model_cache[route.provider_id]:
                raise LLMError(
                    f"El modelo {route.model} no está disponible en {route.provider_id}."
                )
        saved = get_llm_configuration().set(config)
        return {"routes": saved.model_dump()}
    except LLMError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/search")
async def search_youtube(req: SearchRequest):
    """Search YouTube and return a list of extracted videos."""
    platform = YouTubePlatform()
    items = await platform.search(query=req.query, max_results=req.max_results)
    return {
        "query": req.query,
        "total": len(items),
        "videos": [serialize_video(video) for video in items],
    }


@router.post("/analyze")
async def analyze_youtube(req: AnalyzeRequest):
    """
    Full pipeline: scrape YouTube → analyze titles (Qwen3) → analyze trends (DeepSeek R1).
    Returns a Server-Sent Events stream of progress messages followed by results.
    """

    async def event_stream() -> AsyncIterator[str]:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

        try:
            routes = get_llm_configuration().get()
            provider_names = {
                item["id"]: item["name"] for item in get_provider_registry().descriptors()
            }
            # Phase 1: Scraping
            yield sse("progress", {"phase": 1, "message": f"Explorando YouTube para '{req.query}'..."})
            platform = YouTubePlatform()
            items = await platform.search(query=req.query, max_results=req.max_results)

            if not items:
                yield sse("error", {"message": "No videos found. Try a different query."})
                return

            videos_payload = [serialize_video(video) for video in items]
            yield sse("videos", {"videos": videos_payload, "total": len(items)})

            analysis_req = AnalysisRequest(
                query=req.query,
                platform=Platform.YOUTUBE,
                task_types=[TaskType.CLASSIFICATION, TaskType.TREND_ANALYSIS],
                max_items=len(items),
            )

            # Phase 2: Title Analysis (Qwen3)
            yield sse("progress", {
                "phase": 2,
                "message": (
                    f"Analizando patrones con "
                    f"{provider_names.get(routes.extraction.provider_id, routes.extraction.provider_id)} "
                    f"· {routes.extraction.model}..."
                ),
            })
            title_result = await YouTubeTitleAnalyzer().analyze(analysis_req, items)
            title_text = title_result.findings[0].description if title_result.findings else ""
            yield sse("title_analysis", {"content": title_text})

            # Phase 3: Trend Analysis (DeepSeek R1)
            yield sse("progress", {
                "phase": 3,
                "message": (
                    f"Detectando oportunidades con "
                    f"{provider_names.get(routes.reasoning.provider_id, routes.reasoning.provider_id)} "
                    f"· {routes.reasoning.model}..."
                ),
            })
            trend_result = await YouTubeTrendAnalyzer().analyze(analysis_req, items)
            trend_text = trend_result.findings[0].description if trend_result.findings else ""
            yield sse("trend_analysis", {"content": trend_text})

            # Save reports
            storage = FileStorage()
            path1 = await storage.save_analysis(title_result)
            path2 = await storage.save_analysis(trend_result)

            yield sse("done", {
                "message": "Análisis completado.",
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
