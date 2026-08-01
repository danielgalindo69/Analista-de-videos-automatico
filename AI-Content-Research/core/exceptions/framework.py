"""
Framework-specific exception hierarchy.

Design decision: All exceptions inherit from FrameworkError so callers
can catch the entire framework surface with a single except clause when needed,
while still being able to catch specific errors for granular handling.

Hierarchy:
    FrameworkError
    ├── ConfigurationError      — Invalid or missing settings
    ├── BrowserError            — Playwright failures
    ├── LLMError                — Ollama / LLM failures
    │   ├── LLMConnectionError  — Cannot reach Ollama service
    │   └── LLMModelNotFoundError — Requested model not available
    ├── StorageError            — File I/O failures
    ├── PlatformError           — Platform scraping failures
    │   └── ExtractionError     — Data extraction failures within a platform
    ├── AnalysisError           — Analysis pipeline failures
    └── PromptNotFoundError     — Requested prompt template not found
"""


class FrameworkError(Exception):
    """Base exception for the AI Content Research Framework."""

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.context: dict = context or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.context:
            ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{base} [{ctx}]"
        return base


class ConfigurationError(FrameworkError):
    """Raised when required configuration is missing or invalid."""


class BrowserError(FrameworkError):
    """Raised when Playwright browser operations fail."""


class LLMError(FrameworkError):
    """Base exception for all LLM-related failures."""


class LLMConnectionError(LLMError):
    """Raised when the Ollama service cannot be reached."""


class LLMModelNotFoundError(LLMError):
    """Raised when the requested model is not available in Ollama."""

    def __init__(self, model: str) -> None:
        super().__init__(
            f"Model '{model}' not found in Ollama. Run: ollama pull {model}",
            context={"model": model},
        )
        self.model = model


class StorageError(FrameworkError):
    """Raised when file system read/write operations fail."""


class PlatformError(FrameworkError):
    """Raised when platform-specific operations fail."""

    def __init__(self, message: str, platform: str, context: dict | None = None) -> None:
        ctx = {"platform": platform, **(context or {})}
        super().__init__(message, context=ctx)
        self.platform = platform


class ExtractionError(PlatformError):
    """Raised when data extraction from a platform fails."""


class AnalysisError(FrameworkError):
    """Raised when the analysis pipeline encounters an unrecoverable error."""


class PromptNotFoundError(FrameworkError):
    """Raised when a requested prompt template does not exist."""

    def __init__(self, prompt_name: str) -> None:
        super().__init__(
            f"Prompt template '{prompt_name}' not found.",
            context={"prompt_name": prompt_name},
        )
        self.prompt_name = prompt_name
