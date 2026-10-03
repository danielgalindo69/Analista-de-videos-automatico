"""
YouTube Title Analyzer — Extracts title patterns and hooks using Qwen3 14B.
"""

from loguru import logger

from core.interfaces.base_analyzer import BaseAnalyzer
from core.models.analysis import AnalysisRequest, AnalysisResult, Finding, AnalysisStatus
from core.models.content import ContentItem
from core.models.llm import TaskType, LLMRequest
from infrastructure.llm.router import LLMRouter
from prompts.registry import PromptRegistry


class YouTubeTitleAnalyzer(BaseAnalyzer):
    """
    Analyzes title structures, hooks, and keyword patterns using Qwen3 14B.
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
        return "YouTube Title Analyzer"

    async def analyze(
        self,
        request: AnalysisRequest,
        content: list[ContentItem],
    ) -> AnalysisResult:
        """
        Analyze titles of provided YouTube videos.
        """
        if not content:
            return AnalysisResult(
                request_id=request.request_id,
                query=request.query,
                platform=request.platform,
                status=AnalysisStatus.FAILED,
                error_message="No content items provided for title analysis",
            )

        logger.info("TitleAnalyzer | Analyzing {count} titles for query='{q}'", count=len(content), q=request.query)

        # Prepare input data block for prompt
        videos_formatted = []
        for i, item in enumerate(content, 1):
            views = item.get_meta("view_count", 0)
            author = item.author_name or "Unknown"
            published = item.get_meta("published_text", "Unknown")
            views_per_day = item.get_meta("views_per_day")
            velocity = f"{views_per_day:,.0f}/day" if views_per_day is not None else "Unknown"
            videos_formatted.append(
                f"{i}. Title: \"{item.title}\" | Channel: {author} | Views: {views:,} "
                f"| Published: {published} | Views/day: {velocity}"
            )
        
        videos_data_str = "\n".join(videos_formatted)

        # Render prompt template
        prompt_text = self._prompts.get(
            "youtube/analyze_titles",
            query=request.query,
            videos_data=videos_data_str,
        )

        system_prompt = self._prompts.get("system_base")

        llm_req = LLMRequest(
            task_type=TaskType.CLASSIFICATION,  # Routes to Qwen3 14B
            prompt=prompt_text,
            system_prompt=system_prompt,
            temperature=0.3,
        )

        llm_resp = await self._router.route(llm_req)

        finding = Finding(
            title="Title & Hook Patterns",
            description=llm_resp.content,
            confidence=0.85,
            evidence=[f"{len(content)} video titles analyzed"],
            tags=["titles", "hooks", "clickbait"],
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
