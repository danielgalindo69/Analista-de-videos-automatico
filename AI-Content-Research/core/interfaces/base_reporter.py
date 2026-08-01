"""
BaseReporter — Abstract contract for all report generators.

Reporters consume AnalysisResults and produce output artifacts
(Markdown files, JSON files, PDF, etc.).

Design decision: Output format is determined by the concrete implementation,
not the caller. Adding a new format (e.g., HTML, CSV) only requires
creating a new Reporter class — no changes to the analysis pipeline.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from core.models.analysis import AnalysisResult


class BaseReporter(ABC):
    """Abstract base class for all report generators."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Output format identifier (e.g., 'markdown', 'json', 'pdf')."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for generated reports (e.g., '.md', '.json')."""
        ...

    @abstractmethod
    async def generate(
        self,
        result: AnalysisResult,
        output_dir: Path,
    ) -> Path:
        """
        Generate a report from an AnalysisResult.

        Args:
            result: Completed analysis result to render
            output_dir: Directory where the report file will be saved

        Returns:
            Path to the generated report file
        """
        ...
