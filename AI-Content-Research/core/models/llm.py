"""
LLM-related data models.

TaskType drives the LLMRouter to select the correct model.
Adding a new task category only requires adding a new enum member
and updating the router mapping — no other changes needed.
"""

from datetime import datetime
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass
from pydantic import BaseModel, Field


class TaskType(StrEnum):
    """
    Categorizes the type of work being requested from the LLM.
    The LLMRouter maps each TaskType to the appropriate model.

    Extraction/Classification/Summarization → Qwen3 14B
    Reasoning/Pattern detection            → DeepSeek R1 8B
    """

    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    TOOL_CALLING = "tool_calling"
    REASONING = "reasoning"
    PATTERN_DETECTION = "pattern_detection"
    HYPOTHESIS_VALIDATION = "hypothesis_validation"
    COMPARISON = "comparison"
    TREND_ANALYSIS = "trend_analysis"
    REPORT_GENERATION = "report_generation"


class LLMRequest(BaseModel):
    """Represents a single request to an LLM."""

    model_config = {"frozen": True}

    task_type: TaskType
    prompt: str
    system_prompt: str | None = None
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    # Context passed through for tracing — not sent to the model
    request_id: str | None = None


class LLMResponse(BaseModel):
    """Represents the response from an LLM call."""

    content: str
    model_used: str
    task_type: TaskType
    tokens_prompt: int = 0
    tokens_completion: int = 0
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.tokens_prompt + self.tokens_completion
