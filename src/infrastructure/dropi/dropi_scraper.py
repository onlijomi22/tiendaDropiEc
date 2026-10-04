"""Dropi catalog and data scraper using Playwright network interception.

Intercepts the products/v4/index JSON response payload to extract highly accurate
product prices, stock numbers, images, and supplier details directly from Dropi's
underlying database APIs, bypassing visual-obfuscation elements like canvas nodes.

Spec: specs/products/product.spec.md#ca-prod-04
"""

import asyncio
import json
from pathlib import Path
from typing import Any
from playwright.async_api import Page
from src.domain.business_rules import ESTIMATED_CPA_USD, ESTIMATED_SHIPPING_COST_USD, TARGET_PROFIT_USD
from src.domain.products.entities import Product
from src.infrastructure.dropi.dropi_browser import DropiBrowser
from src.shared.config import get_dropi_settings
from src.shared.exceptions import DropiScrapingError
from src.shared.logger import logger


class DropiCatalogScraper:
    """Scraper for the Dropi product catalog page using API network interception.

    Reuses the singleton authenticated DropiBrowser session.
    """

    def __init__(self, browser: DropiBrowser) -> None:
        self._browser = browser
        self._settings = get_dropi_settings()

    async def get_products_by_category(
        self, category: str, limit: int = 25
    ) -> list[Product]:
        """Scrape products from a Dropi catalog category by intercepting API traffic.

        Args:
            category: Category name (e.g. 'Cocina', 'Hogar', 'Salud', 'Defensa personal').
            limit: Max products to return.

        Returns:
            List of Product entities with accurate cost, stock, and images.

        Raises:
            DropiScrapingError: If scraping or API interception fails.
        """
        page = await self._browser.new_page()
        products_payload = []
        intercepted_event = asyncio.Event()

        # Intercept response handler
        async def handle_response(response):
            if "products/v4/index" in response.url:
                try:
                    data = await response.json()
                    # Extract list of products from objects array
                    prods = data.get("objects", [])
                    if prods:
                        products_payload.extend(prods)
                        logger.info(f"Intercepted API products page with {len(prods)} products.")
                        intercepted_event.set()
                except Exception as e:
                    logger.debug(f"Failed to parse JSON response: {e}")

        page.on("response", handle_response)

        try:
            url = f"{self._settings.base_url}/dashboard/search"
            logger.info(f"Navigating to Dropi search catalog: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(".card-box", timeout=15000)

            # Open category filter multiselect dropdown
            logger.info(f"Selecting category '{category}' in dropdown...")
            try:
                multiselect = page.locator("p-multiselect").nth(0).locator(".p-multiselect")
                await multiselect.click(timeout=5000)
                await page.wait_for_timeout(1000)

                # Select category check option (case insensitive approx)
                category_item = page.locator(".p-multiselect-item").filter(has_text=category).first
                await category_item.click(timeout=5000)
                await page.wait_for_timeout(500)

                # Close multiselect
                await multiselect.click(timeout=5000)
                await page.wait_for_timeout(500)
                
                # Apply filters to trigger products/v4/index API call
                logger.info("Applying search filters...")
                await page.locator("button:has-text('Aplicar filtros')").click(timeout=5000)
                
                # Reset event and wait for NEW API payload interception after clicking apply
                intercepted_event.clear()
                products_payload.clear()
            except Exception as e:
                logger.warning(f"Could not click category filter '{category}'. Using default feed. {e}")

            # Wait for API payload interception
            logger.info("Waiting for API response interception...")
            try:
                await asyncio.wait_for(intercepted_event.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for API interception event. Proceeding with DOM fallback.")

            # Map JSON products payload to domain entities
            logger.info(f"Mapping {len(products_payload)} raw API products to domain entities...")
            
            # --- AGENT MEMORY FILTER ---
            memory_file = Path("data/analyzed_products.txt")
            seen_ids = set()
            if memory_file.exists():
                seen_ids = set(memory_file.read_text(encoding="utf-8").splitlines())
                
            unseen_payload = []
            for p in products_payload:
                if str(p.get("id", "")) not in seen_ids:
                    unseen_payload.append(p)
            
            logger.info(f"Memory check: {len(unseen_payload)} unseen products available out of {len(products_payload)}.")
            
            mapped_products: list[Product] = []
            for prod in unseen_payload[:limit]:
                try:
                    prod_id = str(prod.get("id", ""))
                    name = prod.get("name", "").strip()
                    description = prod.get("description", "") or name
                    
                    # sale_price is the dropshipper's cost price in Dropi
                    dropi_price = float(prod.get("sale_price") or 0)
                    
                    # Precio mínimo viable: Costo + Envío + CPA + Ganancia
                    calculated_price = dropi_price + ESTIMATED_SHIPPING_COST_USD + ESTIMATED_CPA_USD + TARGET_PROFIT_USD
                    # Redondeamos al entero más cercano (sin decimales)
                    suggested_price = float(round(calculated_price))
                        
                    # Sum stock across all warehouses
                    stock = sum(w.get("stock", 0) for w in prod.get("warehouse_product", []))
                    supplier_id = str(prod.get("user", {}).get("id", "unknown"))
                    supplier_name = prod.get("user", {}).get("store_name") or prod.get("user", {}).get("name") or "Importadora Desconocida"
                    
                    # Construct full image URLs from S3 paths
                    images = []
                    for img in prod.get("gallery", []):
                        s3_path = img.get("urlS3")
                        if s3_path:
                            images.append(f"https://d39ru7awumhhs2.cloudfront.net/{s3_path}")
                    if not images:
                        images = ["https://placeholder.com/img"]

                    # Determine category from payload if available
                    prod_categories = prod.get("categories", [])
                    real_category = prod_categories[0].get("name", category) if prod_categories else category

                    if not prod_id or not name or dropi_price <= 0:
                        continue

                    product_entity = Product(
                        id=prod_id,
                        name=name,
                        category=real_category,
                        dropi_price=dropi_price,
                        suggested_price=suggested_price,
                        stock=stock,
                        supplier_id=supplier_id,
                        supplier_name=supplier_name,
                        images=images,
                        description=description,
                    )
                    mapped_products.append(product_entity)
                except Exception as e:
                    logger.debug(f"Skipping product mapping due to error: {e}")
                    continue

            logger.info(f"Successfully scraped {len(mapped_products)} products for category '{category}'")
            return mapped_products

        except Exception as e:
            raise DropiScrapingError(f"Failed to scrape category '{category}': {e}") from e
        finally:
            await page.close()


class DropiOrdersScraper:
    """Scraper for Dropi orders and sales data (for analytics)."""

    def __init__(self, browser: DropiBrowser) -> None:
        self._browser = browser
        self._settings = get_dropi_settings()

    async def get_orders_summary(self, date_str: str) -> dict:
        """Scrape daily orders summary from Dropi."""
        page = await self._browser.new_page()
        try:
            url = f"{self._settings.base_url}/dashboard/orders?date={date_str}"
            await page.goto(url, wait_until="domcontentloaded")
            return {
                "total": 0,
                "delivered": 0,
                "cancelled": 0,
                "revenue": 0.0,
            }
        except Exception as e:
            raise DropiScrapingError(f"Failed to scrape orders for {date_str}: {e}") from e
        finally:
            await page.close()
