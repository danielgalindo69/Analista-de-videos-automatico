"""
LLM Router — Selects the correct model based on TaskType.

Design decision: Model selection logic lives in ONE place.
No other module should contain "if task == REASONING: use deepseek" logic.
When adding a new model or reassigning task categories, only this file changes.

The router is stateless — it reads from settings and returns model names.

Extending:
    1. Add a new TaskType to core/models/llm.py
    2. Add the mapping in _build_map() below
    3. Done — no other files need to change
"""

import time

from loguru import logger

from config.settings import get_settings
from core.models.llm import TaskType, LLMRequest, LLMResponse
from core.exceptions import LLMError
from infrastructure.llm.ollama_client import OllamaClient


class LLMRouter:
    """
    Routes LLM requests to the appropriate model based on TaskType.

    Usage:
        router = LLMRouter()
        async with OllamaClient() as client:
            response = await router.route(request, client)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._extraction_model = settings.models.extraction_model
        self._reasoning_model = settings.models.reasoning_model
        self._task_model_map: dict[TaskType, str] = self._build_map()

    def _build_map(self) -> dict[TaskType, str]:
        """
        Maps each TaskType to a model name.

        Qwen3 14B  → extraction, classification, summarization,
                      tool calling, comparison, report generation
        DeepSeek R1 8B → reasoning, pattern detection,
                          hypothesis validation, trend analysis
        """
        return {
            # Qwen3 14B — fast extraction and structured output
            TaskType.EXTRACTION: self._extraction_model,
            TaskType.CLASSIFICATION: self._extraction_model,
            TaskType.SUMMARIZATION: self._extraction_model,
            TaskType.TOOL_CALLING: self._extraction_model,
            TaskType.COMPARISON: self._extraction_model,
            TaskType.REPORT_GENERATION: self._extraction_model,
            # DeepSeek R1 8B — deep reasoning and pattern analysis
            TaskType.REASONING: self._reasoning_model,
            TaskType.PATTERN_DETECTION: self._reasoning_model,
            TaskType.HYPOTHESIS_VALIDATION: self._reasoning_model,
            TaskType.TREND_ANALYSIS: self._reasoning_model,
        }

    def resolve_model(self, task_type: TaskType) -> str:
        """
        Return the model name for the given TaskType.

        Raises:
            LLMError: If task_type has no mapping defined in _build_map()
        """
        model = self._task_model_map.get(task_type)
        if not model:
            raise LLMError(
                f"No model mapping for TaskType '{task_type}'. "
                "Add it to LLMRouter._build_map().",
                context={"task_type": task_type},
            )
        logger.debug(
            "LLMRouter | task={task} → model={model}",
            task=task_type,
            model=model,
        )
        return model

    async def route(self, request: LLMRequest, client: OllamaClient) -> LLMResponse:
        """
        Primary entry point for all LLM calls in the framework.
        Resolves the model and executes the request via the given client.

        Callers should never call OllamaClient directly — always go through route().

        Args:
            request: LLMRequest with task_type and prompt
            client: Active OllamaClient (must be inside async context manager)

        Returns:
            LLMResponse from the resolved model
        """
        model = self.resolve_model(request.task_type)
        payload = client._build_generate_payload(model, request)

        start_ms = int(time.monotonic() * 1000)
        raw = await client._post_with_retry("/api/generate", payload)
        duration_ms = int(time.monotonic() * 1000) - start_ms

        return LLMResponse(
            content=raw.get("response", ""),
            model_used=model,
            task_type=request.task_type,
            tokens_prompt=raw.get("prompt_eval_count", 0),
            tokens_completion=raw.get("eval_count", 0),
            duration_ms=duration_ms,
            request_id=request.request_id,
        )

    def get_model_summary(self) -> dict[str, list[str]]:
        """
        Returns which tasks each model handles.
        Used by CLI diagnostics and health checks.
        """
        summary: dict[str, list[str]] = {}
        for task, model in self._task_model_map.items():
            summary.setdefault(model, []).append(task)
        return summary
