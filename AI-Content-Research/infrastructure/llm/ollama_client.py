"""
Async Ollama client built on httpx.

Design decisions:
- Uses httpx.AsyncClient directly instead of the `ollama` Python SDK.
  Reason: gives full control over timeouts, retries, and streaming behavior
  without being tied to SDK version constraints.
- Retry logic with exponential backoff for transient network failures.
- Streaming support for long LLM responses (avoids timeout on large outputs).
- health_check() and list_models() allow the system to validate state at startup.

All public methods accept LLMRequest and return LLMResponse,
keeping the caller decoupled from the HTTP transport layer.
"""

import time
import asyncio
from typing import AsyncIterator

import httpx
from loguru import logger

from config.settings import get_settings
from core.exceptions import LLMConnectionError, LLMModelNotFoundError, LLMError
from core.models.llm import LLMRequest, LLMResponse


_MAX_RETRIES = 3
_RETRY_BASE_DELAY_S = 1.0  # First retry after 1s, then 2s, then 4s


class OllamaClient:
    """
    Async HTTP client for the Ollama local inference server.

    Usage:
        async with OllamaClient() as client:
            response = await client.generate(request)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama.base_url
        self._timeout = settings.ollama.timeout_seconds
        self._num_gpu_layers = settings.ollama.num_gpu_layers
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        return self

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            raise LLMError(
                "OllamaClient must be used as an async context manager. "
                "Use: async with OllamaClient() as client: ..."
            )
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a completion for the given request (non-streaming).

        Args:
            request: Typed LLMRequest with prompt, model, and parameters

        Returns:
            LLMResponse with content, token counts, and duration

        Raises:
            LLMConnectionError: If Ollama service is unreachable
            LLMModelNotFoundError: If the requested model is not available
            LLMError: For other LLM-related failures
        """
        model = request.model_used if hasattr(request, "model_used") else None  # type: ignore[attr-defined]
        # model is injected by the router before calling generate()
        if not model:
            raise LLMError("No model specified in request. Use LLMRouter to route requests.")

        payload = self._build_generate_payload(model, request)
        logger.debug(
            "LLM generate | model={model} task={task} prompt_chars={chars}",
            model=model,
            task=request.task_type,
            chars=len(request.prompt),
        )

        start_ms = int(time.monotonic() * 1000)
        raw = await self._post_with_retry("/api/generate", payload)
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

    async def generate_stream(self, model: str, request: LLMRequest) -> AsyncIterator[str]:
        """
        Generate a completion with streaming. Yields text chunks as they arrive.
        Useful for long responses where non-streaming would timeout.

        Args:
            model: Model name to use
            request: Typed LLMRequest

        Yields:
            Text chunks from the model response
        """
        payload = {**self._build_generate_payload(model, request), "stream": True}

        async with self._http.stream("POST", "/api/generate", json=payload) as response:
            self._raise_for_ollama_status(response)
            async for line in response.aiter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if token := chunk.get("response"):
                        yield token
                    if chunk.get("done"):
                        break

    async def health_check(self) -> bool:
        """
        Verify Ollama service is reachable and responsive.

        Returns:
            True if healthy, False otherwise (never raises)
        """
        try:
            response = await self._http.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning("Ollama health check failed: {error}", error=str(e))
            return False

    async def list_models(self) -> list[str]:
        """
        List all models currently available in Ollama.

        Returns:
            List of model name strings (e.g., ['qwen3:14b', 'deepseek-r1:8b'])
        """
        try:
            response = await self._http.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Cannot reach Ollama at {self._base_url}. Is Ollama running?",
                context={"url": self._base_url},
            ) from e

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_generate_payload(self, model: str, request: LLMRequest) -> dict:
        """Build the JSON payload for /api/generate."""
        payload: dict = {
            "model": model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_gpu": self._num_gpu_layers,
            },
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens
        return payload

    async def _post_with_retry(self, endpoint: str, payload: dict) -> dict:
        """
        POST to an Ollama endpoint with exponential backoff retry.

        Raises:
            LLMConnectionError: After all retries exhausted due to network error
            LLMModelNotFoundError: If 404 received (model not pulled)
            LLMError: For other non-retryable HTTP errors
        """
        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._http.post(endpoint, json=payload)
                self._raise_for_ollama_status(response)
                return response.json()

            except LLMModelNotFoundError:
                raise  # Never retry on missing model

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY_S * (2 ** (attempt - 1))
                    logger.warning(
                        "Ollama request failed (attempt {attempt}/{max}). "
                        "Retrying in {delay}s. Error: {error}",
                        attempt=attempt,
                        max=_MAX_RETRIES,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

        raise LLMConnectionError(
            f"Ollama unreachable after {_MAX_RETRIES} attempts.",
            context={"url": self._base_url},
        ) from last_error

    @staticmethod
    def _raise_for_ollama_status(response: httpx.Response) -> None:
        """Translate HTTP errors into typed framework exceptions."""
        if response.status_code == 404:
            # Extract model name from request body if available
            raise LLMModelNotFoundError(model="<unknown>")
        if response.status_code >= 400:
            raise LLMError(
                f"Ollama returned HTTP {response.status_code}: {response.text}",
                context={"status_code": response.status_code},
            )
