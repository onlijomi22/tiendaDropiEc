"""MercadoLibre Ecuador scraper for competition research.

Scrapes mercadolibre.com.ec to find:
- Competitor listings and prices
- Sales volume (number of sales shown)
- Market pricing benchmarks

Spec: specs/intelligence/product_intelligence.spec.md#CA-INTEL-02
"""

from __future__ import annotations
import re
from playwright.async_api import async_playwright
from src.domain.intelligence.entities import CompetitorListing
from src.shared.logger import logger

_ML_ECUADOR_BASE = "https://listado.mercadolibre.com.ec"


class MercadoLibreScraper:
    """Scraper for MercadoLibre Ecuador product listings.

    No login required — public catalog.
    Uses a fresh browser per search (no session needed).

    Usage:
        scraper = MercadoLibreScraper()
        competitors = await scraper.search_competitors("licuadora portátil", limit=5)
    """

    async def search_competitors(
        self,
        query: str,
        limit: int = 5,
    ) -> list[CompetitorListing]:
        """Search MercadoLibre Ecuador for competing products.

        Args:
            query: Search term (e.g., 'licuadora 2 en 1').
            limit: Maximum listings to return.

        Returns:
            List of CompetitorListing with prices and sales data.
        """
        logger.info(f"[MLScraper] Searching MercadoLibre EC: '{query}'")
        results: list[CompetitorListing] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                search_url = f"{_ML_ECUADOR_BASE}/{query.replace(' ', '-')}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)

                # Wait for product listings to load or empty state
                await page.wait_for_selector(
                    ".ui-search-layout__item, .ui-search-results, .results-item, .ui-empty-state",
                    timeout=8000
                )

                # Get all product cards
                items = await page.query_selector_all(
                    ".ui-search-layout__item, .ui-search-result__wrapper, .results-item"
                )
                logger.info(f"[MLScraper] Found {len(items)} items for '{query}'")

                for item in items[:limit]:
                    listing = await self._extract_listing(item, page)
                    if listing:
                        results.append(listing)

            except Exception as e:
                logger.warning(f"[MLScraper] Scraping failed for '{query}': {e}")
            finally:
                await browser.close()

        logger.info(f"[MLScraper] Extracted {len(results)} competitor listings")
        return results

    async def _extract_listing(
        self, item, page
    ) -> CompetitorListing | None:
        """Extract data from a single MercadoLibre result card."""
        try:
            # Title
            title_el = await item.query_selector(
                ".ui-search-item__title, .item__title"
            )
            title = await title_el.inner_text() if title_el else ""

            # Price
            price_el = await item.query_selector(
                ".andes-money-amount__fraction, .price-tag-fraction"
            )
            price_text = await price_el.inner_text() if price_el else "0"
            price = float(re.sub(r"[^0-9.]", "", price_text.replace(",", "")) or "0")

            # Sales count (shown as "X vendidos")
            sales_el = await item.query_selector(
                ".ui-search-item__sales, [class*='sold']"
            )
            sales_text = await sales_el.inner_text() if sales_el else "0"
            sales_num = int(re.sub(r"[^0-9]", "", sales_text) or "0")

            # URL
            link_el = await item.query_selector("a")
            url = await link_el.get_attribute("href") if link_el else ""

            if not title or price <= 0:
                return None

            return CompetitorListing(
                title=title.strip(),
                price_usd=price,
                sales_count=sales_num,
                rating=0.0,  # ML requires extra click for rating
                url=url or "",
            )
        except Exception as e:
            logger.debug(f"[MLScraper] Card parse error: {e}")
            return None
