"""EnrichProductV2: evidence-based product enrichment pipeline.

Replaces the monolithic EnrichProductUseCase with a traceable,
confidence-scored pipeline.

Flow:
    Dropi Product
        -> EvidenceCollector (Dropi + ML + Gemini Search)
        -> EnrichmentEngine (apply rules, gates, priorities)
        -> EnrichedProduct (validated, ready for landing)
"""

from __future__ import annotations

from dataclasses import dataclass

from src.application.enrichment.evidence_collector import EvidenceCollector
from src.application.enrichment.enrichment_engine import EnrichmentEngine
from src.domain.enrichment.entities import EnrichedProduct, ProductEvidence
from src.domain.products.entities import Product
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.infrastructure.search.gemini_grounded_search import GeminiGroundedSearch
from src.infrastructure.search.mercadolibre_scraper import MercadoLibreScraper
from src.shared.logger import logger


@dataclass
class EnrichProductV2Input:
    """Input for the V2 enrichment pipeline."""
    product: Product
    target_sale_price: float | None = None


class EnrichProductV2UseCase:
    """Evidence-based product enrichment.

    Unlike V1, every piece of data carries:
    - origin (where it came from)
    - confidence (how reliable it is)
    - data_type (FACT / DERIVED_BENEFIT / MARKETING_COPY)

    The landing page only shows data that passes confidence gates.
    """

    def __init__(
        self,
        ml_scraper: MercadoLibreScraper | None = None,
        gemini_search: GeminiGroundedSearch | None = None,
    ) -> None:
        self._ml_scraper = ml_scraper or MercadoLibreScraper()
        self._gemini_search = gemini_search or GeminiGroundedSearch()
        self._collector = EvidenceCollector()
        self._engine = EnrichmentEngine()

    async def execute(self, inp: EnrichProductV2Input) -> EnrichedProduct:
        """Run the full evidence-based enrichment pipeline.

        Args:
            inp: Product and optional price override.

        Returns:
            EnrichedProduct with validated, confidence-scored data.
        """
        product = inp.product
        if inp.target_sale_price:
            product = product.model_copy(update={"suggested_price": inp.target_sale_price})

        logger.info(f"[EnrichV2] Starting enrichment for: {product.name}")

        # Step 1: Collect evidence from all sources
        all_evidence: list[ProductEvidence] = []

        # 1a. Dropi facts (always available)
        all_evidence.extend(self._collector.collect_from_dropi(product))

        # 1b. MercadoLibre competitors
        words = product.name.split()
        search_query = " ".join(words[:4])
        try:
            competitors = await self._ml_scraper.search_competitors(
                query=search_query.strip(), limit=5
            )
            all_evidence.extend(
                self._collector.collect_from_mercadolibre(product, competitors)
            )
        except Exception as e:
            logger.warning(f"[EnrichV2] MercadoLibre search failed: {e}")

        # 1c. Gemini grounded search
        try:
            buyer_data = await self._gemini_search.research_product_category(
                product_name=product.name,
                category=product.category,
            )
            sources = buyer_data.get("sources_used", [])
            all_evidence.extend(
                self._collector.collect_from_gemini_search(buyer_data, sources)
            )
        except Exception as e:
            logger.warning(f"[EnrichV2] Gemini search failed: {e}")

        # Step 2: Assess image quality
        images = [
            self._collector.assess_image_quality(url, product.description)
            for url in product.images
        ]

        # Step 3: Build EnrichedProduct
        enriched = self._engine.build(product, all_evidence, images)

        logger.info(
            f"[EnrichV2] Done. {enriched.evidence_count} evidences, "
            f"avg_confidence={enriched.avg_confidence:.2f}, "
            f"viable={enriched.viable}, "
            f"{len(enriched.human_review_notes)} review notes"
        )
        return enriched
