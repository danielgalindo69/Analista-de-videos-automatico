"""Provider-neutral routing of LLM tasks to configured models."""

from loguru import logger

from core.models.llm import LLMRequest, LLMResponse, TaskType
from core.models.provider import ProviderRoute
from infrastructure.llm.configuration import LLMConfigurationStore
from infrastructure.llm.provider_registry import ProviderRegistry
from infrastructure.llm.runtime import get_llm_configuration, get_provider_registry


class LLMRouter:
    """Resolve task routes without leaking provider details into analyzers."""

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        configuration: LLMConfigurationStore | None = None,
    ) -> None:
        self._registry = registry or get_provider_registry()
        self._configuration = configuration or get_llm_configuration()

    def resolve_route(self, task_type: TaskType) -> ProviderRoute:
        route = self._configuration.resolve(task_type)
        logger.debug(
            "LLMRouter | task={task} provider={provider} model={model}",
            task=task_type,
            provider=route.provider_id,
            model=route.model,
        )
        return route

    def resolve_model(self, task_type: TaskType) -> str:
        """Compatibility shortcut used by diagnostics."""
        return self.resolve_route(task_type).model

    async def route(self, request: LLMRequest) -> LLMResponse:
        route = self.resolve_route(request.task_type)
        provider = self._registry.get(route.provider_id)
        return await provider.generate(route.model, request)

    async def health_check(self) -> bool:
        route = self.resolve_route(TaskType.EXTRACTION)
        health = await self._registry.get(route.provider_id).health()
        return health.available

    def get_model_summary(self) -> dict[str, list[str]]:
        summary: dict[str, list[str]] = {}
        for task in TaskType:
            route = self.resolve_route(task)
            key = f"{route.provider_id}:{route.model}"
            summary.setdefault(key, []).append(task.value)
        return summary
