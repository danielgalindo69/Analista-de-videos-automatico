"""
YouTube Channel Extractor — Extracting channel profile and videos.
"""

from loguru import logger
from playwright.async_api import Page

from platforms.youtube.models import YouTubeChannel, YouTubeVideo
from platforms.youtube.extractors.search_extractor import YouTubeSearchExtractor, parse_view_count


class YouTubeChannelExtractor:
    """
    Extracts profile metadata and videos from a YouTube channel page.
    """

    def __init__(self) -> None:
        self._search_extractor = YouTubeSearchExtractor()

    async def extract_channel(
        self,
        page: Page,
        channel_identifier: str,
        max_videos: int = 15,
    ) -> YouTubeChannel:
        """
        Extract channel overview and recent videos.
        channel_identifier can be a channel ID ('UC...'), handle ('@username'), or URL.
        """
        if channel_identifier.startswith("http"):
            url = channel_identifier
        elif channel_identifier.startswith("@"):
            url = f"https://www.youtube.com/{channel_identifier}"
        else:
            url = f"https://www.youtube.com/channel/{channel_identifier}"

        videos_url = f"{url.rstrip('/')}/videos"
        logger.debug("YouTubeChannelExtractor | Navigating channel videos url={url}", url=videos_url)

        await page.goto(videos_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        # Header info
        title_elem = await page.query_selector("yt-dynamic-sized-trimmed-text, #channel-name #text")
        channel_name = (await title_elem.inner_text()).strip() if title_elem else channel_identifier

        sub_elem = await page.query_selector("#subscriber-count, yt-formatted-string#subscriber-count")
        sub_text = (await sub_elem.inner_text()).strip() if sub_elem else ""
        subscribers_count = parse_view_count(sub_text)

        # Extract videos listed on videos tab using shared node parser
        video_nodes = await page.query_selector_all("ytd-rich-grid-media, ytd-grid-video-renderer")
        recent_videos: list[YouTubeVideo] = []
        for node in video_nodes[:max_videos]:
            v = await self._search_extractor._parse_video_node(node)
            if v:
                recent_videos.append(v)

        return YouTubeChannel(
            channel_id=channel_identifier,
            name=channel_name,
            url=url,
            subscribers_count=subscribers_count,
            subscribers_text=sub_text,
            recent_videos=recent_videos,
        )
