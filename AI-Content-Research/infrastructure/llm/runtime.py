"""Singleton runtime services for provider configuration and routing."""

from functools import lru_cache

from infrastructure.llm.configuration import LLMConfigurationStore
from infrastructure.llm.credential_store import SessionCredentialStore
from infrastructure.llm.provider_registry import ProviderRegistry


@lru_cache(maxsize=1)
def get_credential_store() -> SessionCredentialStore:
    return SessionCredentialStore()


@lru_cache(maxsize=1)
def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(get_credential_store())


@lru_cache(maxsize=1)
def get_llm_configuration() -> LLMConfigurationStore:
    return LLMConfigurationStore()
