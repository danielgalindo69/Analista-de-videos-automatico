"""Factory and metadata registry for supported LLM providers."""

from config.settings import get_settings
from core.exceptions import ProviderNotConfiguredError
from core.interfaces.llm_provider import LLMProvider
from infrastructure.llm.credential_store import SessionCredentialStore
from infrastructure.llm.gemini_provider import GeminiProvider
from infrastructure.llm.ollama_provider import OllamaProvider


class ProviderRegistry:
    def __init__(self, credentials: SessionCredentialStore) -> None:
        self._credentials = credentials

    @property
    def supported_ids(self) -> set[str]:
        return {"ollama", "gemini"}

    def is_configured(self, provider_id: str) -> bool:
        if provider_id == "ollama":
            return True
        if provider_id == "gemini":
            return bool(self._gemini_key())
        return False

    def get(self, provider_id: str) -> LLMProvider:
        if provider_id == "ollama":
            return OllamaProvider()
        if provider_id == "gemini":
            api_key = self._gemini_key()
            if not api_key:
                raise ProviderNotConfiguredError(
                    "Gemini no está configurado. Conecta una API key primero.",
                    context={"provider": provider_id},
                )
            return GeminiProvider(api_key)
        raise ProviderNotConfiguredError(
            f"Proveedor no soportado: {provider_id}",
            context={"provider": provider_id},
        )

    def create_with_credential(self, provider_id: str, credential: str) -> LLMProvider:
        if provider_id == "gemini":
            return GeminiProvider(credential)
        if provider_id == "ollama":
            return OllamaProvider()
        raise ProviderNotConfiguredError(
            f"Proveedor no soportado: {provider_id}",
            context={"provider": provider_id},
        )

    def set_credential(self, provider_id: str, credential: str) -> None:
        if provider_id not in self.supported_ids or provider_id == "ollama":
            raise ProviderNotConfiguredError(
                f"El proveedor {provider_id} no acepta credenciales de sesión.",
                context={"provider": provider_id},
            )
        self._credentials.set(provider_id, credential)

    def delete_credential(self, provider_id: str) -> None:
        self._credentials.delete(provider_id)

    def descriptors(self) -> list[dict]:
        return [
            {
                "id": "ollama",
                "name": "Ollama",
                "is_local": True,
                "requires_api_key": False,
                "configured": True,
                "privacy": "local",
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "is_local": False,
                "requires_api_key": True,
                "configured": self.is_configured("gemini"),
                "privacy": "cloud",
            },
        ]

    def _gemini_key(self) -> str | None:
        session_key = self._credentials.get("gemini")
        if session_key:
            return session_key
        configured = get_settings().gemini.api_key
        return configured.get_secret_value() if configured else None
