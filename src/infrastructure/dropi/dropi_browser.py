"""Dropi Playwright browser session manager.

Manages a singleton browser session for Dropi web automation.
Use this instead of creating new browser instances per request.

Spec: specs/products/product.spec.md#ca-prod-04
(Session must be reused - no re-login per request)
"""

from __future__ import annotations
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from src.shared.config import get_dropi_settings
from src.shared.logger import logger
from src.shared.exceptions import DropiAuthError


class DropiBrowser:
    """Singleton async context manager for a Dropi authenticated browser session.

    Usage:
        async with DropiBrowser.get_instance() as page:
            await page.goto('https://app.dropi.ec/catalog')
            ...
    """

    _instance: DropiBrowser | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._authenticated: bool = False

    @classmethod
    async def get_instance(cls) -> "DropiBrowser":
        """Return the singleton DropiBrowser instance, creating it if needed."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._initialize()
            return cls._instance

    async def _initialize(self) -> None:
        """Start Playwright and authenticate with Dropi."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        await self._login()

    async def _login(self) -> None:
        """Authenticate with Dropi using credentials from config.

        Raises:
            DropiAuthError: If login fails.
        """
        settings = get_dropi_settings()
        page = await self._context.new_page()
        try:
            logger.info("Authenticating with Dropi...")
            page.set_default_navigation_timeout(60000)
            await page.goto(f"{settings.base_url}/login", wait_until="commit")

            # Fill login form using semantic selectors (robust against minor UI changes)
            await page.locator("#email").fill(settings.email)
            await page.locator("#password").fill(
                settings.password.get_secret_value()
            )
            await page.get_by_role("button", name="Iniciar").click()
            await page.wait_for_url("**/dashboard/**", timeout=60000)

            self._authenticated = True
            logger.info("Dropi authentication successful.")
        except Exception as e:
            raise DropiAuthError(f"Failed to authenticate with Dropi: {e}") from e
        finally:
            await page.close()

    async def new_page(self) -> Page:
        """Open a new browser page in the authenticated context.

        Returns:
            A ready-to-use Playwright Page.

        Raises:
            DropiAuthError: If the browser session is not authenticated.
        """
        if not self._authenticated or not self._context:
            raise DropiAuthError("Browser session not authenticated. Call get_instance() first.")
        return await self._context.new_page()

    async def close(self) -> None:
        """Close browser session and clean up resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        DropiBrowser._instance = None
        logger.info("Dropi browser session closed.")
