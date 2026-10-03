"""Contract implemented by every local or cloud LLM provider."""

from abc import ABC, abstractmethod

from core.models.llm import LLMRequest, LLMResponse
from core.models.provider import ModelInfo, ProviderHealth


class LLMProvider(ABC):
    id: str
    display_name: str
    is_local: bool
    requires_api_key: bool

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Return connection and configuration state without exposing secrets."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return models that support text generation."""

    @abstractmethod
    async def generate(self, model: str, request: LLMRequest) -> LLMResponse:
        """Generate a provider-neutral response."""
