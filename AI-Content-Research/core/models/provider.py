"""Provider-neutral models used by the LLM infrastructure and API."""

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str | None = None
    input_token_limit: int | None = None
    output_token_limit: int | None = None


class ProviderHealth(BaseModel):
    provider_id: str
    available: bool
    configured: bool
    latency_ms: int | None = None
    detail: str | None = None


class ProviderRoute(BaseModel):
    provider_id: str = Field(min_length=1)
    model: str = Field(min_length=1)


class LLMRoutingConfig(BaseModel):
    extraction: ProviderRoute
    reasoning: ProviderRoute
