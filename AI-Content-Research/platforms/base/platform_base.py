"""
PlatformBase — Concrete base class for all platform implementations.

This sits between BasePlatform (ABC, zero dependencies) and the specific
platform implementations (e.g., YouTubePlatform).

It provides shared infrastructure that every platform needs:
- Access to the browser manager
- Access to the LLM router
- Access to the prompt registry
- Access to the storage system
- Shared logging with platform name prefix

Platform implementations inherit from this class, NOT from BasePlatform directly.

Design decision: Dependency injection via constructor arguments.
All dependencies are optional with sensible defaults, enabling
isolated unit testing by passing mock objects.
"""

from typing import Generic, TypeVar
from loguru import logger

from core.interfaces.base_platform import BasePlatform
from core.models.content import ContentItem, Platform
from infrastructure.browser.playwright_manager import PlaywrightManager
from infrastructure.llm.ollama_client import OllamaClient
from infrastructure.llm.router import LLMRouter
from infrastructure.storage.file_storage import FileStorage
from prompts.registry import PromptRegistry

T = TypeVar("T", bound=ContentItem)


class PlatformBase(BasePlatform[T], Generic[T]):
    """
    Concrete base for all platform modules.
    Provides shared infrastructure via dependency injection.

    Usage (in a platform implementation):

        class YouTubePlatform(PlatformBase):
            @property
            def platform_name(self) -> str:
                return "YouTube"

            async def search(self, query: str, max_results: int = 20):
                async with self.browser as b:
                    page = await b.get_page()
                    await b.navigate(page, f"https://youtube.com/results?search_query={query}")
                    # ... extraction logic
    """

    def __init__(
        self,
        browser: PlaywrightManager | None = None,
        llm_client: OllamaClient | None = None,
        router: LLMRouter | None = None,
        storage: FileStorage | None = None,
        prompts: PromptRegistry | None = None,
    ) -> None:
        # Lazy-initialized defaults: only created if not injected
        self._browser = browser or PlaywrightManager()
        self._llm_client = llm_client or OllamaClient()
        self._router = router or LLMRouter()
        self._storage = storage or FileStorage()
        self._prompts = prompts or PromptRegistry()

    # ------------------------------------------------------------------
    # Convenience properties (typed shortcuts for subclasses)
    # ------------------------------------------------------------------

    @property
    def browser(self) -> PlaywrightManager:
        return self._browser

    @property
    def router(self) -> LLMRouter:
        return self._router

    @property
    def storage(self) -> FileStorage:
        return self._storage

    @property
    def prompts(self) -> PromptRegistry:
        return self._prompts

    # ------------------------------------------------------------------
    # Shared logging helper
    # ------------------------------------------------------------------

    def log(self, level: str, message: str, **kwargs) -> None:
        """
        Emit a log entry prefixed with the platform name.
        Simplifies logging in subclasses without boilerplate.

        Usage:
            self.log("info", "Found {count} videos", count=42)
        """
        prefixed = f"[{self.platform_name}] {message}"
        getattr(logger, level)(prefixed, **kwargs)

    # ------------------------------------------------------------------
    # Default implementations (subclasses may override)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Verify platform is reachable by checking LLM and browser availability.
        Subclasses can override to add platform-specific URL checks.
        """
        async with OllamaClient() as client:
            llm_ok = await client.health_check()
        if not llm_ok:
            self.log("warning", "LLM health check failed")
            return False
        self.log("debug", "Health check passed")
        return True

    async def get_trending(self, max_results: int = 20) -> list[ContentItem]:
        """
        Default implementation raises NotImplementedError.
        Override in platforms that support trending content discovery.
        """
        raise NotImplementedError(
            f"{self.platform_name} does not implement get_trending(). "
            "Override this method in the platform class."
        )
