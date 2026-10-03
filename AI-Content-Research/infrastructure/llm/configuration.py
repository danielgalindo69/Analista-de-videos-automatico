"""Runtime routing configuration shared by every analyzer instance."""

from threading import RLock

from config.settings import get_settings
from core.models.llm import TaskType
from core.models.provider import LLMRoutingConfig, ProviderRoute


_REASONING_TASKS = {
    TaskType.REASONING,
    TaskType.PATTERN_DETECTION,
    TaskType.HYPOTHESIS_VALIDATION,
    TaskType.TREND_ANALYSIS,
}


class LLMConfigurationStore:
    """Process-local provider and model routing configuration."""

    def __init__(self) -> None:
        settings = get_settings()
        self._default = LLMRoutingConfig(
            extraction=ProviderRoute(
                provider_id="ollama",
                model=settings.models.extraction_model,
            ),
            reasoning=ProviderRoute(
                provider_id="ollama",
                model=settings.models.reasoning_model,
            ),
        )
        self._config = self._default.model_copy(deep=True)
        self._lock = RLock()

    def get(self) -> LLMRoutingConfig:
        with self._lock:
            return self._config.model_copy(deep=True)

    def set(self, config: LLMRoutingConfig) -> LLMRoutingConfig:
        with self._lock:
            self._config = config.model_copy(deep=True)
            return self._config.model_copy(deep=True)

    def resolve(self, task_type: TaskType) -> ProviderRoute:
        config = self.get()
        return config.reasoning if task_type in _REASONING_TASKS else config.extraction

    def reset_provider(self, provider_id: str) -> LLMRoutingConfig:
        with self._lock:
            extraction = self._config.extraction
            reasoning = self._config.reasoning
            if extraction.provider_id == provider_id:
                extraction = self._default.extraction
            if reasoning.provider_id == provider_id:
                reasoning = self._default.reasoning
            self._config = LLMRoutingConfig(extraction=extraction, reasoning=reasoning)
            return self._config.model_copy(deep=True)
