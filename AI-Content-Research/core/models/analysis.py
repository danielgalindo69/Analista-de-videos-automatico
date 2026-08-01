"""
Analysis data models.

These models represent the inputs and outputs of the analysis pipeline,
independent of any specific platform or LLM implementation.
"""

from datetime import datetime
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass
from pydantic import BaseModel, Field

from core.models.content import ContentItem, Platform
from core.models.llm import TaskType


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(BaseModel):
    """
    Describes what needs to be analyzed.

    A single AnalysisRequest can span multiple content items,
    enabling comparison and cross-content pattern detection.
    """

    model_config = {"frozen": True}

    query: str = Field(description="Natural language query from the user")
    platform: Platform
    task_types: list[TaskType] = Field(
        description="Which analysis tasks to perform. Drives model routing."
    )
    content_ids: list[str] = Field(
        default_factory=list,
        description="Specific content IDs to analyze. Empty = use search.",
    )
    max_items: int = Field(default=20, ge=1, le=200)
    request_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class Finding(BaseModel):
    """A single insight extracted from the analysis."""

    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0, description="0.0 = speculative, 1.0 = certain")
    evidence: list[str] = Field(default_factory=list, description="Supporting data points")
    tags: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Complete output of an analysis pipeline run."""

    request_id: str | None = None
    query: str
    platform: Platform
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    items_analyzed: int = 0
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    raw_llm_outputs: list[str] = Field(
        default_factory=list,
        description="Raw LLM responses for debugging and auditing",
    )
    content_items: list[ContentItem] = Field(
        default_factory=list,
        description="Source content items used in the analysis",
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
