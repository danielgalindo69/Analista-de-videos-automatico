"""
BaseAnalyzer — Abstract contract for all content analyzers.

Analyzers consume ContentItems and produce AnalysisResults.
They are decoupled from platforms: a trend analyzer can work
on YouTube videos, TikTok posts, or any other ContentItem.

Design decision: Analyzers are stateless. They receive all input
via method parameters and return structured output. This makes
them easily testable and composable.
"""

from abc import ABC, abstractmethod

from core.models.analysis import AnalysisRequest, AnalysisResult
from core.models.content import ContentItem


class BaseAnalyzer(ABC):
    """Abstract base class for all content analyzers."""

    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """Unique name identifying this analyzer. Used in reports."""
        ...

    @abstractmethod
    async def analyze(
        self,
        request: AnalysisRequest,
        content: list[ContentItem],
    ) -> AnalysisResult:
        """
        Perform analysis on a list of content items.

        Args:
            request: Describes what to analyze and how
            content: Source content items to analyze

        Returns:
            Structured AnalysisResult with findings and recommendations
        """
        ...

    async def can_handle(self, request: AnalysisRequest) -> bool:
        """
        Check if this analyzer can handle the given request.
        Override to add platform or task_type filtering logic.
        Default: always returns True.
        """
        return True
