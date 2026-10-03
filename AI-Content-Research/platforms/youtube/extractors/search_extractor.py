"""
YouTube Search Extractor — Scraping search results using Playwright.

Design decision:
Uses Playwright to render search result DOM (`ytd-video-renderer`).
Parses video ID, title, channel name, relative views, duration text, and URL.
Helper functions convert text durations ('10:45', '1:02:15') to integer seconds
and relative view counts ('1.5M views', '250K views') to numbers.
"""

import re
from datetime import datetime, timedelta, timezone
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
            published_text = extract_published_text(meta_text)
            published_at = parse_relative_published_at(published_text)
            age_days = calculate_age_days(published_at)
            views_per_day = calculate_views_per_day(view_count, published_at)
            
            # Duration badge
            badge_elem = await node.query_selector("ytd-thumbnail-overlay-time-status-renderer, #length")
            duration_text = (await badge_elem.inner_text()).strip() if badge_elem else ""
            # YouTube's badge element sometimes returns the time twice (e.g. "1:13:57 1:13:57").
            # Deduplicate: grab the first token that looks like a time string (contains ":").
            duration_text = _deduplicate_duration(duration_text)
            duration_seconds = parse_duration_seconds(duration_text)
            is_short = "SHORT" in duration_text.upper() or (0 < duration_seconds <= 60)

            return YouTubeVideo(
                id=video_id,
                platform=Platform.YOUTUBE,
                content_type=ContentType.VIDEO,
                title=title,
                url=video_url,
                author_name=channel_name,
                published_at=published_at,
                metadata={
                    "view_count": view_count,
                    "published_text": published_text,
                    "age_days": age_days,
                    "views_per_day": views_per_day,
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


def _deduplicate_duration(text: str) -> str:
    """
    Fix YouTube badge returning duration twice, e.g. '1:13:57 1:13:57' or 'SHORT SHORT'.
    Returns the first distinct time-like token, or the original stripped text.
    """
    if not text:
        return text
    # Split into words and find the first token that contains a digit+colon pattern
    tokens = text.split()
    seen: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.append(t)
    # If all unique: nothing was duplicated → return joined
    # If duplicates removed: use the de-duped version
    candidate = " ".join(seen)
    # Prefer just the first time-looking token (contains ":")
    for t in seen:
        if ":" in t and re.match(r"^\d+:\d+", t):
            return t
    return candidate


def parse_view_count(text: str) -> int:
    """Extract localized view counts without confusing publication age for views."""
    match = re.search(
        r"(?P<number>\d[\d.,]*)\s*(?P<unit>k|m|b|mil)?(?:\s+de)?\s*"
        r"(?:views?|visualizaciones?|vistas?)",
        text,
        re.IGNORECASE,
    )
    if not match:
        # YouTube's compact metadata currently omits the label and returns
        # two lines such as "2.5M\n5y ago". Only inspect the first line so the
        # publication age can never be mistaken for a view count.
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        match = re.fullmatch(
            r"(?P<number>\d[\d.,]*)\s*(?P<unit>k|m|b|mil)?",
            first_line,
            re.IGNORECASE,
        )
    if not match:
        return 0

    number = match.group("number")
    unit = (match.group("unit") or "").lower()
    if unit:
        # YouTube abbreviations use a decimal separator before K/M/B/mil.
        val = float(number.replace(",", "."))
    else:
        # Exact view counts use punctuation as thousands separators.
        val = float(number.replace(",", "").replace(".", ""))

    if unit in {"k", "mil"}:
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


_RELATIVE_DATE_PATTERNS = (
    re.compile(
        r"(?:(?:streamed|premiered)\s+)?(?P<value>\d+)\s+"
        r"(?P<unit>second|minute|hour|day|week|month|year)s?\s+ago",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:(?:emitido|transmitido|estrenado)\s+)?hace\s+(?P<value>\d+)\s+"
        r"(?P<unit>segundo|minuto|hora|d[ií]a|semana|mes|a[ñn]o)(?:s|es)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<value>\d+)\s*(?P<unit>min|mo|s|m|h|d|w|y)\s+ago",
        re.IGNORECASE,
    ),
)

_UNIT_SECONDS = {
    "second": 1,
    "segundo": 1,
    "minute": 60,
    "minuto": 60,
    "hour": 3_600,
    "hora": 3_600,
    "day": 86_400,
    "dia": 86_400,
    "día": 86_400,
    "week": 604_800,
    "semana": 604_800,
    "month": 2_592_000,
    "mes": 2_592_000,
    "year": 31_536_000,
    "ano": 31_536_000,
    "año": 31_536_000,
    "s": 1,
    "min": 60,
    "m": 60,
    "h": 3_600,
    "d": 86_400,
    "w": 604_800,
    "mo": 2_592_000,
    "y": 31_536_000,
}


def extract_published_text(text: str) -> str | None:
    """Return the relative publication label found in a YouTube metadata line."""
    normalized = " ".join(text.split())
    if not normalized:
        return None

    for pattern in _RELATIVE_DATE_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(0)

    lowered = normalized.lower()
    for label in ("today", "hoy", "yesterday", "ayer", "just now", "ahora mismo"):
        if label in lowered:
            return label
    return None


def parse_relative_published_at(
    text: str | None,
    *,
    now: datetime | None = None,
) -> datetime | None:
    """
    Convert YouTube's relative publication label into an estimated UTC datetime.

    Month and year labels are necessarily approximate because search results do
    not include an exact date. The original label is preserved in metadata.
    """
    if not text:
        return None

    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    lowered = text.strip().lower()
    if lowered in {"today", "hoy", "just now", "ahora mismo"}:
        return reference
    if lowered in {"yesterday", "ayer"}:
        return reference - timedelta(days=1)

    for pattern in _RELATIVE_DATE_PATTERNS:
        match = pattern.search(lowered)
        if not match:
            continue
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        seconds = _UNIT_SECONDS.get(unit)
        if seconds is None:
            return None
        return reference - timedelta(seconds=value * seconds)
    return None


def calculate_age_days(
    published_at: datetime | None,
    *,
    now: datetime | None = None,
) -> int | None:
    """Return estimated whole age in days, using zero for content under 24 hours."""
    if published_at is None:
        return None
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    return max(0, int((reference - published_at).total_seconds() // 86_400))


def calculate_views_per_day(
    view_count: int,
    published_at: datetime | None,
    *,
    now: datetime | None = None,
) -> float | None:
    """Calculate average daily velocity, including content newer than one day."""
    if published_at is None:
        return None
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    elapsed_days = max((reference - published_at).total_seconds() / 86_400, 1 / 24)
    return round(max(0, view_count) / elapsed_days, 2)
