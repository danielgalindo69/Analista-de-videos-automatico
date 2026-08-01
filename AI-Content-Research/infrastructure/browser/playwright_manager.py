"""
PlaywrightManager — Async context manager for Chromium browser automation.

Design decisions:
- ONLY Chromium is supported (per project spec). Firefox and WebKit are
  explicitly excluded to reduce maintenance surface and VRAM overhead.
- Async context manager pattern ensures the browser is always closed,
  even on exceptions — no resource leaks.
- Stealth configuration (user-agent, viewport, accept-language) reduces
  bot detection on platforms like YouTube.
- get_page() always returns a fresh page. Callers are responsible for
  closing pages they open. This avoids shared-state bugs in concurrent use.

Usage:
    async with PlaywrightManager() as manager:
        page = await manager.get_page()
        await manager.navigate(page, "https://youtube.com")
        content = await page.content()
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
)

from config.settings import get_settings
from core.exceptions import BrowserError


class PlaywrightManager:
    """
    Manages a single Chromium browser instance across the session.

    One manager = one browser process.
    Multiple pages can be opened from the same browser context.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._headless = settings.browser.headless
        self._timeout_ms = settings.browser.timeout_ms
        self._viewport = {
            "width": settings.browser.viewport_width,
            "height": settings.browser.viewport_height,
        }
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "PlaywrightManager":
        await self._launch()
        return self

    async def __aexit__(self, *_) -> None:
        await self._close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_page(self) -> Page:
        """
        Open and return a new browser page with default settings applied.

        Returns:
            Fresh Playwright Page object

        Raises:
            BrowserError: If browser context is not initialized
        """
        if not self._context:
            raise BrowserError(
                "PlaywrightManager not started. Use: async with PlaywrightManager() as mgr:"
            )
        page = await self._context.new_page()
        page.set_default_timeout(self._timeout_ms)
        logger.debug("Browser | new page opened")
        return page

    async def navigate(self, page: Page, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        Navigate a page to a URL and wait for it to load.

        Args:
            page: Playwright Page to navigate
            url: Target URL
            wait_until: When to consider navigation complete.
                        Options: 'load', 'domcontentloaded', 'networkidle', 'commit'
                        Default 'domcontentloaded' — faster than 'networkidle' for SPAs.

        Raises:
            BrowserError: If navigation fails or times out
        """
        try:
            logger.debug("Browser | navigating to {url}", url=url)
            await page.goto(url, wait_until=wait_until)
            logger.debug("Browser | navigation complete | url={url}", url=url)
        except PlaywrightTimeout as e:
            raise BrowserError(
                f"Navigation timeout after {self._timeout_ms}ms",
                context={"url": url, "timeout_ms": self._timeout_ms},
            ) from e
        except Exception as e:
            raise BrowserError(
                f"Navigation failed: {e}",
                context={"url": url},
            ) from e

    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout_ms: int | None = None,
    ) -> None:
        """
        Wait for a CSS selector to appear in the DOM.

        Args:
            page: Active Playwright Page
            selector: CSS selector string
            timeout_ms: Custom timeout. Defaults to manager-level timeout.

        Raises:
            BrowserError: If selector not found within timeout
        """
        timeout = timeout_ms or self._timeout_ms
        try:
            await page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeout as e:
            raise BrowserError(
                f"Selector not found within {timeout}ms: '{selector}'",
                context={"selector": selector, "timeout_ms": timeout},
            ) from e

    async def get_text(self, page: Page, selector: str) -> str:
        """
        Extract inner text from an element matching the selector.

        Returns empty string if element is not found.
        """
        try:
            element = await page.query_selector(selector)
            if element:
                return (await element.inner_text()).strip()
        except Exception as e:
            logger.warning("Browser | get_text failed | selector={sel} | {e}", sel=selector, e=e)
        return ""

    async def scroll_to_bottom(self, page: Page, times: int = 3, delay_ms: int = 1500) -> None:
        """
        Scroll the page to the bottom multiple times to trigger lazy-loading.

        Args:
            page: Active Playwright Page
            times: Number of scroll steps
            delay_ms: Milliseconds to wait between scrolls
        """
        import asyncio
        for i in range(times):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay_ms / 1000)
            logger.debug("Browser | scroll {i}/{total}", i=i + 1, total=times)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _launch(self) -> None:
        """Launch Chromium with stealth configuration."""
        try:
            self._playwright = await async_playwright().start()

            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            self._context = await self._browser.new_context(
                viewport=self._viewport,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
                java_script_enabled=True,
            )

            logger.info(
                "Browser | Chromium launched | headless={headless}",
                headless=self._headless,
            )
        except Exception as e:
            raise BrowserError(f"Failed to launch Chromium: {e}") from e

    async def _close(self) -> None:
        """Close browser and Playwright in correct teardown order."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser | Chromium closed")


@asynccontextmanager
async def get_browser() -> AsyncIterator[PlaywrightManager]:
    """
    Convenience async context manager for one-off browser sessions.

    Usage:
        async with get_browser() as browser:
            page = await browser.get_page()
    """
    async with PlaywrightManager() as manager:
        yield manager
