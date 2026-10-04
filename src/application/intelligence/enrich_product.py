"""EnrichProduct use case: orchestrates market research + copy generation + viability.

Spec: specs/intelligence/product_intelligence.spec.md
CA-INTEL-01: All data sourced from real web searches
CA-INTEL-02: MercadoLibre competition analysis
CA-INTEL-03: Always return raw data + draft copy (dual output)
"""

from __future__ import annotations
from dataclasses import dataclass

from src.application.intelligence.research_market import (
    ResearchMarketInput,
    ResearchMarketUseCase,
)
from src.application.intelligence.generate_product_copy import (
    GenerateProductCopyInput,
    GenerateProductCopyUseCase,
)
from src.application.intelligence.evaluate_viability import EvaluateViabilityUseCase
from src.domain.intelligence.entities import ProductIntelligenceResult
from src.domain.products.entities import Product
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.infrastructure.search.gemini_grounded_search import GeminiGroundedSearch
from src.infrastructure.search.mercadolibre_scraper import MercadoLibreScraper
from src.shared.logger import logger


@dataclass
class EnrichProductInput:
    """Input for the EnrichProduct use case."""
    product: Product
    target_sale_price: float | None = None  # Override Dropi suggested price


class EnrichProductUseCase:
    """Enriches a Dropi product with real market intelligence.

    Orchestrates three sub-use-cases:
    1. ResearchMarketUseCase — MercadoLibre + Gemini grounded search
    2. GenerateProductCopyUseCase — AI copywriting from real data
    3. EvaluateViabilityUseCase — economic viability decision

    Spec: CA-INTEL-01, CA-INTEL-02, CA-INTEL-03
    """

    def __init__(
        self,
        ml_scraper: MercadoLibreScraper | None = None,
        gemini_search: GeminiGroundedSearch | None = None,
        gemini_adapter: GeminiAdapter | None = None,
    ) -> None:
        adapter = gemini_adapter or GeminiAdapter()
        self._research_uc = ResearchMarketUseCase(
            ml_scraper=ml_scraper,
            gemini_search=gemini_search,
        )
        self._copy_uc = GenerateProductCopyUseCase(gemini_adapter=adapter)
        self._viability_uc = EvaluateViabilityUseCase()

    async def execute(self, inp: EnrichProductInput) -> ProductIntelligenceResult:
        """Run full product enrichment pipeline.

        Args:
            inp: Product and optional price override.

        Returns:
            ProductIntelligenceResult with raw data and draft copy.
        """
        product = inp.product
        sale_price = inp.target_sale_price or product.suggested_price
        logger.info(f"[EnrichProduct] Starting enrichment for: {product.name}")

        # Step 1: Market research
        market_insight = await self._research_uc.execute(
            ResearchMarketInput(product=product)
        )

        # Step 2: Generate copy draft
        copy_draft = await self._copy_uc.execute(
            GenerateProductCopyInput(
                product=product,
                sale_price=sale_price,
                market_insight=market_insight,
            )
        )

        # Step 3: Evaluate viability
        viable, viability_reason, copy_draft = self._viability_uc.execute(
            product=product,
            sale_price=sale_price,
            market_insight=market_insight,
            copy_draft=copy_draft,
        )

        logger.info(f"[EnrichProduct] Done. Viable={viable}")

        return ProductIntelligenceResult(
            product_id=product.id,
            product_name=product.name,
            dropi_cost=product.dropi_price,
            market_insight=market_insight,
            copy_draft=copy_draft,
            viable=viable,
            viability_reason=viability_reason,
        )
