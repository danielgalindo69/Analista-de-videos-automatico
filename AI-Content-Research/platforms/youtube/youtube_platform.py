"""
YouTubePlatform — Concrete implementation of PlatformBase for YouTube.

Binds PlaywrightManager, YouTubeSearchExtractor, YouTubeVideoExtractor,
and YouTubeChannelExtractor together into a clean, typed API.
"""

from loguru import logger

from platforms.base.platform_base import PlatformBase
from platforms.youtube.models import YouTubeVideo, YouTubeChannel
from platforms.youtube.extractors import (
    YouTubeSearchExtractor,
    YouTubeVideoExtractor,
    YouTubeChannelExtractor,
)


class YouTubePlatform(PlatformBase[YouTubeVideo]):
    """
    YouTube platform module.

    Usage:
        platform = YouTubePlatform()
        videos = await platform.search("Five Nights at Freddy's", max_results=10)
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._search_extractor = YouTubeSearchExtractor()
        self._video_extractor = YouTubeVideoExtractor()
        self._channel_extractor = YouTubeChannelExtractor()

    @property
    def platform_name(self) -> str:
        return "YouTube"

    async def search(self, query: str, max_results: int = 20) -> list[YouTubeVideo]:
        """
        Search YouTube for query and return parsed YouTubeVideo list.
        """
        self.log("info", "Searching YouTube for '{query}' (max={max_results})", query=query, max_results=max_results)
        async with self.browser as mgr:
            page = await mgr.get_page()
            items = await self._search_extractor.extract_search_results(
                page=page,
                query=query,
                max_results=max_results,
            )

        # Save raw extracted items to storage
        await self.storage.save_content_items(
            items=items,
            platform=self.platform_name.lower(),
            label=f"search_{query}",
        )
        return items

    async def get_item(self, item_id: str) -> YouTubeVideo:
        """
        Retrieve detailed metadata for a single YouTube video by video_id.
        """
        self.log("info", "Extracting video details for id={item_id}", item_id=item_id)
        async with self.browser as mgr:
            page = await mgr.get_page()
            video = await self._video_extractor.extract_video_details(
                page=page,
                video_id=item_id,
            )
        return video

    async def get_trending(self, max_results: int = 20) -> list[YouTubeVideo]:
        """
        Extract currently trending videos on YouTube.
        """
        self.log("info", "Extracting YouTube trending videos (max={max_results})", max_results=max_results)
        async with self.browser as mgr:
            page = await mgr.get_page()
            await page.goto("https://www.youtube.com/feed/trending", wait_until="domcontentloaded")
            items = await self._search_extractor.extract_search_results(
                page=page,
                query="",
                max_results=max_results,
            )
        return items

    async def get_channel(self, channel_identifier: str, max_videos: int = 15) -> YouTubeChannel:
        """
        Extract profile statistics and recent videos for a channel.
        """
        self.log("info", "Extracting channel statistics for '{channel}'", channel=channel_identifier)
        async with self.browser as mgr:
            page = await mgr.get_page()
            channel = await self._channel_extractor.extract_channel(
                page=page,
                channel_identifier=channel_identifier,
                max_videos=max_videos,
            )
        return channel
