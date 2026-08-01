"""
YouTube Trend Analyzer — Market gap & competition reasoning using DeepSeek R1 8B.
"""

from loguru import logger

from core.interfaces.base_analyzer import BaseAnalyzer
from core.models.analysis import AnalysisRequest, AnalysisResult, Finding, AnalysisStatus
from core.models.content import ContentItem
from core.models.llm import TaskType, LLMRequest
from infrastructure.llm.ollama_client import OllamaClient
from infrastructure.llm.router import LLMRouter
from prompts.registry import PromptRegistry


class YouTubeTrendAnalyzer(BaseAnalyzer):
    """
    Detects market gaps, competition density, and growth opportunities using DeepSeek R1 8B.
    """

    def __init__(
        self,
        router: LLMRouter | None = None,
        prompts: PromptRegistry | None = None,
    ) -> None:
        self._router = router or LLMRouter()
        self._prompts = prompts or PromptRegistry()

    @property
    def analyzer_name(self) -> str:
        return "YouTube Trend & Opportunity Analyzer"

    async def analyze(
        self,
        request: AnalysisRequest,
        content: list[ContentItem],
    ) -> AnalysisResult:
        """
        Perform deep reasoning on YouTube market dataset.
        """
        if not content:
            return AnalysisResult(
                request_id=request.request_id,
                query=request.query,
                platform=request.platform,
                status=AnalysisStatus.FAILED,
                error_message="No content items provided for trend analysis",
            )

        logger.info("TrendAnalyzer | Reasoning over {count} items for query='{q}'", count=len(content), q=request.query)

        videos_formatted = []
        for i, item in enumerate(content, 1):
            views = item.get_meta("view_count", 0)
            duration = item.get_meta("duration_text", "N/A")
            author = item.author_name or "Unknown"
            videos_formatted.append(
                f"{i}. Title: \"{item.title}\" | Channel: {author} | Views: {views:,} | Duration: {duration}"
            )

        videos_data_str = "\n".join(videos_formatted)

        prompt_text = self._prompts.get(
            "youtube/analyze_trends",
            query=request.query,
            videos_data=videos_data_str,
        )

        system_prompt = self._prompts.get("system_base")

        llm_req = LLMRequest(
            task_type=TaskType.TREND_ANALYSIS,  # Routes to DeepSeek R1 8B
            prompt=prompt_text,
            system_prompt=system_prompt,
            temperature=0.4,
        )

        async with OllamaClient() as client:
            llm_resp = await self._router.route(llm_req, client)

        finding = Finding(
            title="Market Trends & Niche Opportunities",
            description=llm_resp.content,
            confidence=0.90,
            evidence=[f"{len(content)} video market samples analyzed"],
            tags=["trends", "competition", "opportunity", "deepseek-r1"],
        )

        return AnalysisResult(
            request_id=request.request_id,
            query=request.query,
            platform=request.platform,
            status=AnalysisStatus.COMPLETED,
            items_analyzed=len(content),
            findings=[finding],
            raw_llm_outputs=[llm_resp.content],
            content_items=content,
        )
