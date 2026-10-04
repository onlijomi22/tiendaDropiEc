"""Dropi implementation of IProductRepository.

Uses Playwright-based scraping (no official Dropi API).
Implements the IProductRepository interface from the domain layer.

Spec: specs/products/product.spec.md
"""

import json
from pathlib import Path
from src.domain.products.entities import Product, ProductScore, ProductRecommendation
from src.domain.products.repositories import IProductRepository
from src.infrastructure.dropi.dropi_browser import DropiBrowser
from src.infrastructure.dropi.dropi_scraper import DropiCatalogScraper
from src.shared.exceptions import ProductNotFoundError
from src.shared.logger import logger


class DropiProductRepository(IProductRepository):
    """Dropi product repository backed by Playwright web scraping.

    Implements all IProductRepository methods:
    - get_catalog: Scrapes Dropi catalog page
    - get_product: Scrapes individual product page
    - save_score: Persists to local JSON file
    - get_scored_products: Reads from local JSON file

    Note: Scores are stored locally in data/scores.jsonl for simplicity.
    Future: migrate to Supabase when volume requires it.
    """

    _SCORES_FILE = Path("data/product_scores.jsonl")

    def __init__(self, browser: DropiBrowser) -> None:
        self._browser = browser
        self._scraper = DropiCatalogScraper(browser)
        self._SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Product] = {}

    async def get_catalog(self, category: str, limit: int = 50) -> list[Product]:
        """Fetch products from Dropi catalog via Playwright."""
        products = await self._scraper.get_products_by_category(category, limit=limit)
        for p in products:
            self._cache[str(p.id)] = p
        return products

    async def get_product(self, product_id: str) -> Product:
        """Fetch single product from cache."""
        if product_id in self._cache:
            return self._cache[product_id]
        raise ProductNotFoundError(product_id)

    async def save_score(self, score: ProductScore) -> None:
        """Append score to local JSONL file."""
        with open(self._SCORES_FILE, "a", encoding="utf-8") as f:
            f.write(score.model_dump_json() + "\n")
        logger.debug(f"Score saved for product {score.product_id}")

    async def get_scored_products(
        self, recommendation: str | None = None
    ) -> list[ProductScore]:
        """Read scored products from local JSONL, optionally filtered."""
        if not self._SCORES_FILE.exists():
            return []
        scores = []
        with open(self._SCORES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                score = ProductScore.model_validate_json(line)
                if recommendation is None or score.recommendation.value == recommendation:
                    scores.append(score)
        return scores
