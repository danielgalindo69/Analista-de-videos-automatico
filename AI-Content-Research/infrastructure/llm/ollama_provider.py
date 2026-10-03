"""Provider adapter for the local Ollama runtime."""

import time

from core.interfaces.llm_provider import LLMProvider
from core.models.llm import LLMRequest, LLMResponse
from core.models.provider import ModelInfo, ProviderHealth
from infrastructure.llm.ollama_client import OllamaClient


class OllamaProvider(LLMProvider):
    id = "ollama"
    display_name = "Ollama"
    is_local = True
    requires_api_key = False

    async def health(self) -> ProviderHealth:
        started = time.monotonic()
        async with OllamaClient() as client:
            available = await client.health_check()
        return ProviderHealth(
            provider_id=self.id,
            available=available,
            configured=True,
            latency_ms=int((time.monotonic() - started) * 1_000),
            detail=None if available else "No se pudo conectar con Ollama.",
        )

    async def list_models(self) -> list[ModelInfo]:
        async with OllamaClient() as client:
            names = await client.list_models()
        return [ModelInfo(id=name, name=name) for name in names]

    async def generate(self, model: str, request: LLMRequest) -> LLMResponse:
        async with OllamaClient() as client:
            return await client.generate(model, request)
