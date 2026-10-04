"""EvidenceCollector: gathers ProductEvidence from multiple sources.

Each piece of data gets tagged with origin, confidence, and data_type.
No data transformation happens here — only collection and classification.
"""

from __future__ import annotations

import re
from datetime import datetime

from src.application.enrichment.product_matcher import ProductMatcher
from src.domain.enrichment.entities import (
    DataOrigin,
    DataType,
    MatchQuality,
    ProductEvidence,
    ProductImage,
)
from src.domain.intelligence.entities import CompetitorListing, MarketInsight
from src.domain.products.entities import Product
from src.shared.logger import logger

# Confidence values by source and match quality
_CONFIDENCE = {
    "dropi_fact": 1.0,
    "ml_exact": 0.95,
    "ml_similar": 0.8,
    "ml_category": 0.5,
    "google_search_with_url": 0.7,
    "google_search_no_url": 0.5,
    "llm_derived_benefit": 0.4,
    "llm_review_rewrite": 0.3,
    "marketing_copy": 0.2,
    "placeholder": 0.0,
}

# Patterns that indicate a "dirty" image
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-]{8,}")
_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")


class EvidenceCollector:
    """Collects ProductEvidence from Dropi, MercadoLibre, and Gemini Search."""

    def __init__(self) -> None:
        self._matcher = ProductMatcher()

    def collect_from_dropi(self, product: Product) -> list[ProductEvidence]:
        """Extract evidence from the Dropi product itself.

        Everything from Dropi is FACT with confidence 1.0.
        """
        now = datetime.utcnow()
        evidences: list[ProductEvidence] = []

        # Core facts
        for field, value in [
            ("name", product.name),
            ("category", product.category),
            ("dropi_price", product.dropi_price),
            ("suggested_price", product.suggested_price),
            ("stock", product.stock),
            ("supplier_id", product.supplier_id),
            ("supplier_name", product.supplier_name),
            ("description", product.description),
        ]:
            evidences.append(ProductEvidence(
                field=field,
                value=value,
                data_type=DataType.FACT,
                origin=DataOrigin.DROPI,
                confidence=_CONFIDENCE["dropi_fact"],
                source_product_id=product.id,
                collected_at=now,
            ))

        # Images — each one gets quality flags
        for url in product.images:
            evidences.append(ProductEvidence(
                field="image_url",
                value=url,
                data_type=DataType.FACT,
                origin=DataOrigin.DROPI,
                confidence=_CONFIDENCE["dropi_fact"],
                source_product_id=product.id,
                collected_at=now,
            ))

        # Weight if available
        if product.weight_kg is not None:
            evidences.append(ProductEvidence(
                field="weight_kg",
                value=product.weight_kg,
                data_type=DataType.FACT,
                origin=DataOrigin.DROPI,
                confidence=_CONFIDENCE["dropi_fact"],
                source_product_id=product.id,
                collected_at=now,
            ))

        logger.info(f"[EvidenceCollector] Dropi: {len(evidences)} evidences")
        return evidences

    def collect_from_mercadolibre(
        self, product: Product, competitors: list[CompetitorListing]
    ) -> list[ProductEvidence]:
        """Extract evidence from MercadoLibre competitor listings.

        Each competitor is matched against the Dropi product.
        Confidence depends on match quality.
        """
        now = datetime.utcnow()
        evidences: list[ProductEvidence] = []

        for comp in competitors:
            match = self._matcher.match(product, comp)
            conf_key = {
                MatchQuality.EXACT: "ml_exact",
                MatchQuality.SIMILAR: "ml_similar",
                MatchQuality.CATEGORY_ONLY: "ml_category",
            }[match.quality]

            evidences.append(ProductEvidence(
                field="competitor_price",
                value=comp.price_usd,
                data_type=DataType.FACT,
                origin=DataOrigin.MERCADOLIBRE,
                confidence=_CONFIDENCE[conf_key],
                source_url=comp.url,
                match_quality=match.quality,
                collected_at=now,
                notes=match.reasoning,
            ))

            if comp.sales_count > 0:
                evidences.append(ProductEvidence(
                    field="competitor_sales",
                    value=comp.sales_count,
                    data_type=DataType.FACT,
                    origin=DataOrigin.MERCADOLIBRE,
                    confidence=_CONFIDENCE[conf_key],
                    source_url=comp.url,
                    match_quality=match.quality,
                    collected_at=now,
                ))

            if comp.rating > 0:
                evidences.append(ProductEvidence(
                    field="competitor_rating",
                    value=comp.rating,
                    data_type=DataType.FACT,
                    origin=DataOrigin.MERCADOLIBRE,
                    confidence=_CONFIDENCE[conf_key],
                    source_url=comp.url,
                    match_quality=match.quality,
                    collected_at=now,
                ))

        logger.info(
            f"[EvidenceCollector] MercadoLibre: {len(evidences)} evidences "
            f"from {len(competitors)} listings"
        )
        return evidences

    def collect_from_gemini_search(
        self, buyer_data: dict, sources: list[str] | None = None
    ) -> list[ProductEvidence]:
        """Extract evidence from Gemini grounded search results.

        Buyer concerns and positives sourced from real web data.
        """
        now = datetime.utcnow()
        evidences: list[ProductEvidence] = []
        has_sources = bool(sources)

        conf = _CONFIDENCE["google_search_with_url"] if has_sources else _CONFIDENCE["google_search_no_url"]

        for concern in buyer_data.get("buyer_concerns", []):
            evidences.append(ProductEvidence(
                field="buyer_concern",
                value=concern,
                data_type=DataType.FACT,
                origin=DataOrigin.GOOGLE_SEARCH,
                confidence=conf,
                collected_at=now,
            ))

        for positive in buyer_data.get("buyer_positives", []):
            evidences.append(ProductEvidence(
                field="buyer_positive",
                value=positive,
                data_type=DataType.FACT,
                origin=DataOrigin.GOOGLE_SEARCH,
                confidence=conf,
                collected_at=now,
            ))

        for review in buyer_data.get("real_reviews", []):
            evidences.append(ProductEvidence(
                field="real_review",
                value=review,
                data_type=DataType.FACT,
                origin=DataOrigin.GOOGLE_SEARCH,
                confidence=conf,
                collected_at=now,
                notes="Review extracted by Gemini grounded search",
            ))

        logger.info(f"[EvidenceCollector] Gemini Search: {len(evidences)} evidences")
        return evidences

    def assess_image_quality(self, url: str, description: str = "") -> ProductImage:
        """Assess quality flags for a product image based on URL and context.

        Heuristic checks — not pixel-level analysis.
        """
        lower_url = url.lower()
        is_placeholder = "placeholder" in lower_url

        # Check description for Chinese text or phone numbers
        has_chinese = bool(_CHINESE_PATTERN.search(description))
        has_phone = bool(_PHONE_PATTERN.search(description))

        # Dropi CloudFront images are generally product photos
        is_cloudfront = "cloudfront.net" in lower_url
        is_clean = is_cloudfront and not is_placeholder
        is_product_only = is_cloudfront  # Heuristic: CloudFront = product gallery

        return ProductImage(
            url=url,
            origin=DataOrigin.DROPI,
            is_clean=is_clean,
            is_product_only=is_product_only,
            has_chinese_text=has_chinese,
            has_phone_number=has_phone,
        )
