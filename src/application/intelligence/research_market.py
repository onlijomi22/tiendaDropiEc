"""Use case: Research market competition and buyer behavior.

Spec: specs/intelligence/product_intelligence.spec.md
CA-INTEL-01: All data sourced from real web searches
CA-INTEL-02: MercadoLibre competition analysis
"""

from __future__ import annotations
from dataclasses import dataclass

from src.domain.business_rules import (
    COMPETITION_LOW_MAX_SELLERS,
    COMPETITION_HIGH_MIN_SELLERS,
)
from src.domain.intelligence.entities import MarketInsight
from src.domain.products.entities import CompetitionLevel, Product
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.infrastructure.search.gemini_grounded_search import GeminiGroundedSearch
from src.infrastructure.search.mercadolibre_scraper import MercadoLibreScraper
from src.shared.logger import logger


@dataclass
class ResearchMarketInput:
    """Input for market research."""
    product: Product


class ResearchMarketUseCase:
    """Research market competition for a product.

    1. Search MercadoLibre Ecuador for competitor listings
    2. Use Gemini Search Grounding to research buyer behavior
    3. Build and return MarketInsight (raw data)
    """

    def __init__(
        self,
        ml_scraper: MercadoLibreScraper | None = None,
        gemini_search: GeminiGroundedSearch | None = None,
    ) -> None:
        self._ml_scraper = ml_scraper or MercadoLibreScraper()
        self._gemini_search = gemini_search or GeminiGroundedSearch()

    async def execute(self, inp: ResearchMarketInput) -> MarketInsight:
        """Run market research pipeline.

        Args:
            inp: Product to research.

        Returns:
            MarketInsight with competitor data and buyer behavior.
        """
        product = inp.product
        logger.info(f"[ResearchMarket] Starting research for: {product.name}")

        # Step 1: MercadoLibre competition research
        words = product.name.split()
        search_query = " ".join(words[:4])
        competitors = await self._ml_scraper.search_competitors(
            query=search_query.strip(), limit=5
        )

        # Step 2: Gemini grounded search for buyer insights
        buyer_data = await self._gemini_search.research_product_category(
            product_name=product.name,
            category=product.category,
        )

        # Step 3: Build MarketInsight
        comp_count = len(competitors)
        if comp_count < COMPETITION_LOW_MAX_SELLERS:
            comp_level = CompetitionLevel.LOW
        elif comp_count <= COMPETITION_HIGH_MIN_SELLERS:
            comp_level = CompetitionLevel.MEDIUM
        else:
            comp_level = CompetitionLevel.HIGH

        avg_price = (
            sum(c.price_usd for c in competitors) / len(competitors)
            if competitors else 0.0
        )

        market_insight = MarketInsight(
            category=product.category,
            product_name=product.name,
            buyer_concerns=buyer_data.get("buyer_concerns", []),
            buyer_positives=buyer_data.get("buyer_positives", []),
            real_reviews=buyer_data.get("real_reviews", []),
            competitors=competitors,
            avg_competitor_price=avg_price,
            competition_count=comp_count,
            competition_level=comp_level,
            sources=buyer_data.get("sources_used", []),
            search_query_used=search_query,
        )

        logger.info(
            f"[ResearchMarket] Done. {comp_count} competitors, "
            f"level={comp_level.value}, avg_price=${avg_price:.2f}"
        )
        return market_insight
