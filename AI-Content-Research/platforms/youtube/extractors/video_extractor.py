"""
YouTube Video Extractor — Extracting detailed video page metadata.
"""

import json
import re
from datetime import datetime
from loguru import logger
from playwright.async_api import Page

from core.models.content import ContentType, Platform
from platforms.youtube.models import YouTubeVideo
from platforms.youtube.extractors.search_extractor import parse_view_count, parse_duration_seconds


class YouTubeVideoExtractor:
    """
    Extracts detailed metadata from an individual YouTube video page.
    """

    async def extract_video_details(self, page: Page, video_id: str) -> YouTubeVideo:
        """
        Navigate to YouTube video watch page and extract full metadata.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        logger.debug("YouTubeVideoExtractor | Navigating url={url}", url=url)

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        # Title
        title_elem = await page.query_selector("h1.ytd-watch-metadata, meta[name='title']")
        title = ""
        if title_elem:
            title = (await title_elem.inner_text()).strip() if hasattr(title_elem, "inner_text") else ""
        if not title:
            meta_title = await page.query_selector("meta[name='title']")
            title = await meta_title.get_attribute("content") if meta_title else video_id

        # Meta tags / Keywords
        meta_keywords = await page.query_selector("meta[name='keywords']")
        keywords_str = await meta_keywords.get_attribute("content") if meta_keywords else ""
        tags = [k.strip() for k in keywords_str.split(",") if k.strip()]

        # Channel name
        channel_elem = await page.query_selector("#channel-name a, ytd-channel-name a")
        channel_name = (await channel_elem.inner_text()).strip() if channel_elem else ""
        channel_href = await channel_elem.get_attribute("href") if channel_elem else ""
        channel_url = f"https://www.youtube.com{channel_href}" if channel_href else ""

        # Description
        description = ""
        desc_elem = await page.query_selector("#description-inline-expander, meta[name='description']")
        if desc_elem:
            description = (await desc_elem.inner_text()).strip() if hasattr(desc_elem, "inner_text") else ""

        # Views & Upload Date
        info_elem = await page.query_selector("#info-container, #description")
        info_text = (await info_elem.inner_text()) if info_elem else ""
        view_count = parse_view_count(info_text)

        return YouTubeVideo(
            id=video_id,
            platform=Platform.YOUTUBE,
            content_type=ContentType.VIDEO,
            title=title,
            url=url,
            author_name=channel_name,
            raw_text=description,
            metadata={
                "view_count": view_count,
                "channel_name": channel_name,
                "channel_url": channel_url,
                "tags": tags,
                "description": description,
            },
        )
