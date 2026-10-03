"""Gemini REST provider using the same neutral contracts as Ollama."""

import time
from urllib.parse import quote

import httpx

from config.settings import get_settings
from core.exceptions import LLMAuthenticationError, LLMConnectionError, LLMError
from core.interfaces.llm_provider import LLMProvider
from core.models.llm import LLMRequest, LLMResponse
from core.models.provider import ModelInfo, ProviderHealth


class GeminiProvider(LLMProvider):
    id = "gemini"
    display_name = "Google Gemini"
    is_local = False
    requires_api_key = True

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key cannot be empty")
        settings = get_settings().gemini
        self._api_key = api_key.strip()
        self._base_url = settings.base_url.rstrip("/")
        self._timeout = settings.timeout_seconds

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={"x-goog-api-key": self._api_key},
            timeout=httpx.Timeout(connect=10, read=self._timeout, write=30, pool=10),
        )

    async def health(self) -> ProviderHealth:
        started = time.monotonic()
        try:
            await self.list_models()
            return ProviderHealth(
                provider_id=self.id,
                available=True,
                configured=True,
                latency_ms=int((time.monotonic() - started) * 1_000),
            )
        except LLMError as error:
            return ProviderHealth(
                provider_id=self.id,
                available=False,
                configured=True,
                latency_ms=int((time.monotonic() - started) * 1_000),
                detail=str(error),
            )

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with self._client() as client:
                response = await client.get("models", params={"pageSize": 1000})
            self._raise_for_status(response)
        except httpx.RequestError as error:
            raise LLMConnectionError(
                "No se pudo conectar con Gemini.",
                context={"provider": self.id},
            ) from error

        models = []
        for item in response.json().get("models", []):
            methods = item.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            model_id = item.get("name", "").removeprefix("models/")
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    id=model_id,
                    name=item.get("displayName") or model_id,
                    description=item.get("description"),
                    input_token_limit=item.get("inputTokenLimit"),
                    output_token_limit=item.get("outputTokenLimit"),
                )
            )
        return sorted(models, key=lambda model: model.name.lower())

    async def generate(self, model: str, request: LLMRequest) -> LLMResponse:
        model_id = model.removeprefix("models/")
        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
            "generationConfig": {"temperature": request.temperature},
        }
        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        started = time.monotonic()
        try:
            async with self._client() as client:
                response = await client.post(
                    f"models/{quote(model_id, safe='')}:generateContent",
                    json=payload,
                )
            self._raise_for_status(response)
        except httpx.RequestError as error:
            raise LLMConnectionError(
                "No se pudo conectar con Gemini durante la generación.",
                context={"provider": self.id, "model": model_id},
            ) from error

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            raise LLMError(
                "Gemini no devolvió contenido.",
                context={"provider": self.id, "model": model_id, "block_reason": block_reason},
            )

        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in parts if part.get("text"))
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            content=content,
            provider_used=self.id,
            model_used=model_id,
            task_type=request.task_type,
            tokens_prompt=usage.get("promptTokenCount", 0),
            tokens_completion=usage.get("candidatesTokenCount", 0),
            duration_ms=int((time.monotonic() - started) * 1_000),
            finish_reason=candidate.get("finishReason"),
            request_id=request.request_id,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise LLMAuthenticationError(
                "Gemini rechazó la API key.",
                context={"provider": self.id, "status_code": response.status_code},
            )
        if response.status_code >= 400:
            try:
                message = response.json().get("error", {}).get("message")
            except ValueError:
                message = None
            raise LLMError(
                message or f"Gemini devolvió HTTP {response.status_code}.",
                context={"provider": self.id, "status_code": response.status_code},
            )
