"""
YouTube Search Extractor — Scraping search results using Playwright.

Design decision:
Uses Playwright to render search result DOM (`ytd-video-renderer`).
Parses video ID, title, channel name, relative views, duration text, and URL.
Helper functions convert text durations ('10:45', '1:02:15') to integer seconds
and relative view counts ('1.5M views', '250K views') to numbers.
"""

import re
from loguru import logger
from playwright.async_api import Page

from core.exceptions import ExtractionError
from core.models.content import ContentType, Platform
from platforms.youtube.models import YouTubeVideo


class YouTubeSearchExtractor:
    """
    Extracts YouTubeVideo list from a search results page.
    """

    async def extract_search_results(
        self,
        page: Page,
        query: str,
        max_results: int = 20,
    ) -> list[YouTubeVideo]:
        """
        Navigate to YouTube search and parse up to max_results videos.
        """
        url = f"https://www.youtube.com/results?search_query={query}"
        logger.debug("YouTubeExtractor | Navigating search url={url}", url=url)

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self._dismiss_consent(page)
            await page.wait_for_selector("ytd-video-renderer", timeout=15000)
        except Exception as e:
            logger.warning("YouTubeExtractor | Search load issue: {e}", e=str(e))
            # Even if selector wait times out, try extracting whatever is in DOM

        # Scroll to load requested items
        scroll_steps = max(1, min(max_results // 5, 8))
        for _ in range(scroll_steps):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

        video_nodes = await page.query_selector_all("ytd-video-renderer")
        logger.debug("YouTubeExtractor | Found {count} raw video nodes", count=len(video_nodes))

        results: list[YouTubeVideo] = []
        for node in video_nodes:
            if len(results) >= max_results:
                break
            video = await self._parse_video_node(node)
            if video:
                results.append(video)

        logger.info(
            "YouTubeExtractor | Search query='{q}' | extracted={count}",
            q=query,
            count=len(results),
        )
        return results

    async def _dismiss_consent(self, page: Page) -> None:
        """Dismiss YouTube cookie consent dialogs if present."""
        try:
            button = await page.query_selector('button[aria-label*="Reject"], button[aria-label*="Accept"], ytd-button-renderer button')
            if button and await button.is_visible():
                await button.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

    async def _parse_video_node(self, node) -> YouTubeVideo | None:
        """Parse a single ytd-video-renderer element into a YouTubeVideo model."""
        try:
            title_elem = await node.query_selector("a#video-title")
            if not title_elem:
                return None

            title = (await title_elem.inner_text()).strip()
            href = await title_elem.get_attribute("href") or ""
            
            if not href or "/watch?v=" not in href:
                return None

            video_id = href.split("/watch?v=")[1].split("&")[0]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Channel info
            channel_elem = await node.query_selector("#channel-info #text a, ytd-channel-name a")
            channel_name = (await channel_elem.inner_text()).strip() if channel_elem else ""
            channel_href = (await channel_elem.get_attribute("href")) if channel_elem else ""
            channel_url = f"https://www.youtube.com{channel_href}" if channel_href else ""

            # Views and time text metadata
            meta_line = await node.query_selector("#metadata-line")
            meta_text = (await meta_line.inner_text()) if meta_line else ""

            view_count = parse_view_count(meta_text)
            
            # Duration badge
            badge_elem = await node.query_selector("ytd-thumbnail-overlay-time-status-renderer, #length")
            duration_text = (await badge_elem.inner_text()).strip() if badge_elem else ""
            duration_seconds = parse_duration_seconds(duration_text)
            is_short = "SHORT" in duration_text.upper() or (0 < duration_seconds <= 60)

            return YouTubeVideo(
                id=video_id,
                platform=Platform.YOUTUBE,
                content_type=ContentType.VIDEO,
                title=title,
                url=video_url,
                author_name=channel_name,
                metadata={
                    "view_count": view_count,
                    "duration_seconds": duration_seconds,
                    "duration_text": duration_text,
                    "channel_name": channel_name,
                    "channel_url": channel_url,
                    "is_short": is_short,
                    "raw_meta_text": meta_text,
                },
            )
        except Exception as e:
            logger.debug("YouTubeExtractor | Node parse error: {e}", e=str(e))
            return None


def parse_view_count(text: str) -> int:
    """Extract view count from strings like '1.5M views', '450K vistas', '1,234 views'."""
    text_clean = text.lower().replace(",", "")
    
    match = re.search(r"(\d+(?:\.\d+)?)\s*([kmb])?", text_clean)
    if not match:
        return 0

    val = float(match.group(1))
    unit = match.group(2)
    if unit == "k":
        val *= 1_000
    elif unit == "m":
        val *= 1_000_000
    elif unit == "b":
        val *= 1_000_000_000
    return int(val)


def parse_duration_seconds(text: str) -> int:
    """Convert '12:34' -> 754, '1:02:15' -> 3735, '0:45' -> 45."""
    clean = re.sub(r"[^\d:]", "", text)
    if not clean:
        return 0
    parts = list(map(int, clean.split(":")))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0
