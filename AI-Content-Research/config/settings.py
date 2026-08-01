"""
Centralized configuration using Pydantic Settings.

Design decision: Pydantic Settings is used instead of python-dotenv because it:
- Reads .env files natively (no redundant dependency)
- Validates types at startup and raises descriptive errors
- Provides IDE autocomplete for all settings
- Supports nested models for logical grouping

All settings are immutable after initialization (frozen=True).
"""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaSettings(BaseSettings):
    """Ollama service and model configuration."""

    model_config = SettingsConfigDict(env_prefix="OLLAMA_", extra="ignore")

    host: str = Field(default="localhost", description="Ollama service host")
    port: int = Field(default=11434, description="Ollama service port")
    num_gpu_layers: int = Field(
        default=30,
        description=(
            "GPU layers for model offload. "
            "RTX 5050 8GB: qwen3:14b needs ~30-35 layers. "
            "Set lower if VRAM OOM errors occur."
        ),
    )
    timeout_seconds: int = Field(default=120, description="Request timeout in seconds")

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class LLMModelSettings(BaseSettings):
    """Which model handles which task category."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    extraction_model: str = Field(
        default="qwen3:14b",
        description="Model for extraction, classification, summarization, tool calling",
    )
    reasoning_model: str = Field(
        default="deepseek-r1:8b",
        description="Model for reasoning, pattern detection, hypothesis validation",
    )


class BrowserSettings(BaseSettings):
    """Playwright browser configuration. Chromium only."""

    model_config = SettingsConfigDict(env_prefix="BROWSER_", extra="ignore")

    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout_ms: int = Field(default=30_000, description="Page navigation timeout (ms)")
    viewport_width: int = Field(default=1280)
    viewport_height: int = Field(default=720)


class StorageSettings(BaseSettings):
    """File system output configuration."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")

    output_dir: str = Field(
        default="./output",
        description="Base directory for all generated reports and data",
    )


class LoggingSettings(BaseSettings):
    """Loguru logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")

    level: str = Field(default="INFO", description="Log level: DEBUG|INFO|WARNING|ERROR")
    dir: str = Field(default="./logs", description="Directory for log files")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper


class AppSettings(BaseSettings):
    """
    Root settings object. Groups all sub-settings.

    Usage:
        from config.settings import get_settings
        settings = get_settings()
        print(settings.ollama.base_url)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,  # Immutable after creation — prevents accidental mutation
    )

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    models: LLMModelSettings = Field(default_factory=LLMModelSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Returns the singleton AppSettings instance.
    Cached with lru_cache — reads .env only once per process.
    """
    return AppSettings()
