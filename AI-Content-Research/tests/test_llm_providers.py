"""Focused tests for provider routing and Gemini response translation."""

import asyncio
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models.llm import LLMRequest, LLMResponse, TaskType
from core.models.provider import LLMRoutingConfig, ProviderRoute
from infrastructure.llm.configuration import LLMConfigurationStore
from infrastructure.llm.gemini_provider import GeminiProvider
from infrastructure.llm.router import LLMRouter


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, LLMRequest]] = []

    async def generate(self, model: str, request: LLMRequest) -> LLMResponse:
        self.calls.append((model, request))
        return LLMResponse(
            content="respuesta",
            provider_used="gemini",
            model_used=model,
            task_type=request.task_type,
        )


class FakeRegistry:
    def __init__(self, provider: FakeProvider) -> None:
        self.provider = provider

    def get(self, provider_id: str) -> FakeProvider:
        assert provider_id == "gemini"
        return self.provider


class TestGeminiProvider(GeminiProvider):
    __test__ = False

    def __init__(self, transport: httpx.AsyncBaseTransport) -> None:
        super().__init__("test-key")
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            headers={"x-goog-api-key": self._api_key},
            transport=self._transport,
        )


async def test_router_uses_configured_provider_and_model() -> None:
    provider = FakeProvider()
    configuration = LLMConfigurationStore()
    configuration.set(
        LLMRoutingConfig(
            extraction=ProviderRoute(provider_id="gemini", model="gemini-fast"),
            reasoning=ProviderRoute(provider_id="gemini", model="gemini-pro"),
        )
    )
    router = LLMRouter(registry=FakeRegistry(provider), configuration=configuration)

    response = await router.route(
        LLMRequest(task_type=TaskType.TREND_ANALYSIS, prompt="Analiza esta tendencia")
    )

    assert response.provider_used == "gemini"
    assert response.model_used == "gemini-pro"
    assert provider.calls[0][0] == "gemini-pro"


async def test_gemini_lists_models_and_translates_generation() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "models/gemini-test",
                            "displayName": "Gemini Test",
                            "supportedGenerationMethods": ["generateContent"],
                        },
                        {
                            "name": "models/embedding-test",
                            "supportedGenerationMethods": ["embedContent"],
                        },
                    ]
                },
            )
        assert request.url.path.endswith("/models/gemini-test:generateContent")
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "resultado"}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3},
            },
        )

    provider = TestGeminiProvider(httpx.MockTransport(handler))
    models = await provider.list_models()
    response = await provider.generate(
        "gemini-test",
        LLMRequest(task_type=TaskType.EXTRACTION, prompt="Extrae patrones"),
    )

    assert [model.id for model in models] == ["gemini-test"]
    assert response.content == "resultado"
    assert response.total_tokens == 8
    assert response.finish_reason == "STOP"


if __name__ == "__main__":
    asyncio.run(test_router_uses_configured_provider_and_model())
    asyncio.run(test_gemini_lists_models_and_translates_generation())
    print("ALL PROVIDER TESTS PASSED SUCCESSFULLY!")
