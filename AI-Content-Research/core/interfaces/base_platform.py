"""
BasePlatform — Abstract contract for all platform modules.

Every platform (YouTube, TikTok, Steam, etc.) MUST implement this interface.
This guarantees that the analysis pipeline can work with any platform
without knowing its internal implementation details (Liskov Substitution).

Design decisions:
- All methods are async — platform operations are I/O bound (browser, HTTP)
- Generic TypeVar `T` lets each platform define its own ContentItem subtype
  while still satisfying the base contract
- `search()` and `get_item()` are the two fundamental operations;
  everything else in a platform builds on top of these
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from core.models.content import ContentItem

T = TypeVar("T", bound=ContentItem)


class BasePlatform(ABC, Generic[T]):
    """Abstract base class for all platform extractors."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name. Used in logging and reports."""
        ...

    @abstractmethod
    async def search(self, query: str, max_results: int = 20) -> list[T]:
        """
        Search the platform for content matching the query.

        Args:
            query: Natural language or platform-native search query
            max_results: Maximum number of items to return

        Returns:
            List of ContentItem subtype instances
        """
        ...

    @abstractmethod
    async def get_item(self, item_id: str) -> T:
        """
        Retrieve a single content item by its platform-native ID.

        Args:
            item_id: Platform-native unique identifier

        Returns:
            Single ContentItem subtype instance
        """
        ...

    @abstractmethod
    async def get_trending(self, max_results: int = 20) -> list[T]:
        """
        Retrieve currently trending content on the platform.

        Args:
            max_results: Maximum number of items to return

        Returns:
            List of ContentItem subtype instances ordered by trend score
        """
        ...

    async def health_check(self) -> bool:
        """
        Verify the platform is reachable and operational.
        Override in platform implementations for platform-specific checks.
        Default implementation returns True.
        """
        return True
