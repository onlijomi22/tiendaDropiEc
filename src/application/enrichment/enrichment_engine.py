"""EnrichmentEngine: transforms raw evidence into a validated EnrichedProduct.

Applies source priority, confidence gates, conflict resolution,
and image quality filtering to produce a product ready for the landing page.
"""

from __future__ import annotations

import re
from datetime import datetime

from src.domain.business_rules import (
    ESTIMATED_CPA_USD,
    ESTIMATED_SHIPPING_COST_USD,
    TARGET_MARGIN_PCT,
)
from src.domain.enrichment.category_config import get_category_config
from src.domain.enrichment.entities import (
    CategoryConfig,
    DataOrigin,
    DataType,
    EnrichedProduct,
    EvidencedClaim,
    MatchQuality,
    ProductEvidence,
    ProductImage,
    ProductSpec,
)
from src.domain.products.entities import CompetitionLevel, Product
from src.shared.logger import logger

# Confidence thresholds for display
_FACT_GATE = 0.6
_BENEFIT_GATE = 0.4
_REVIEW_GATE = 0.7


class EnrichmentEngine:
    """Transforms raw ProductEvidence into a validated EnrichedProduct.

    Rules applied:
    - Source priority: MANUAL > DROPI > ML_EXACT > GOOGLE_SEARCH > ML_SIMILAR > LLM
    - Confidence gates for facts, benefits, and reviews
    - Image quality filtering
    - Category-specific configuration
    """

    def build(
        self,
        product: Product,
        evidences: list[ProductEvidence],
        images: list[ProductImage],
    ) -> EnrichedProduct:
        """Build an EnrichedProduct from raw evidence.

        Args:
            product: The base Dropi product.
            evidences: All collected evidence from all sources.
            images: Assessed product images.

        Returns:
            EnrichedProduct with validated, confidence-scored data.
        """
        category_config = get_category_config(product.category)
        notes: list[str] = []

        # --- Pricing ---
        competitor_prices = self._get_competitor_prices(evidences)
        competitor_avg, price_confidence = self._compute_competitor_avg(competitor_prices)

        # --- Competition ---
        competition_count, competition_level = self._assess_competition(evidences)

        # --- Market evidence ---
        buyer_concerns = self._extract_claims(evidences, "buyer_concern", _FACT_GATE)
        buyer_positives = self._extract_claims(evidences, "buyer_positive", _FACT_GATE)
        real_reviews = self._extract_claims(evidences, "real_review", _REVIEW_GATE)

        # --- Benefits (derived from positives) ---
        benefits = self._derive_benefits(buyer_positives)

        # --- Description cleanup ---
        description_clean = self._clean_description(product.description)
        specifications = self._extract_specs(product.description)

        # --- Display name ---
        display_name = self._clean_display_name(product.name)

        # --- Slug ---
        slug = self._generate_slug(product.name)

        # --- Viability ---
        margin = product.margin_pct
        net_profit = (
            product.suggested_price - product.dropi_price
            - ESTIMATED_CPA_USD - ESTIMATED_SHIPPING_COST_USD
        )
        viable = (
            margin >= TARGET_MARGIN_PCT
            and competition_level != CompetitionLevel.HIGH
        )
        viability_reason = self._explain_viability(
            margin, competition_level, competition_count, net_profit,
        )

        # --- Image quality checks ---
        if not any(img.is_clean and img.is_product_only for img in images):
            notes.append("IMAGENES: Ninguna imagen limpia disponible. Requiere revision manual.")
        elif sum(1 for img in images if img.is_clean and img.is_product_only) < category_config.min_clean_images:
            notes.append(
                f"IMAGENES: Solo {sum(1 for img in images if img.is_clean)} imagenes limpias. "
                f"Minimo requerido: {category_config.min_clean_images}."
            )

        # --- Review sufficiency ---
        if not real_reviews:
            notes.append("REVIEWS: No se encontraron resenas reales con confidence suficiente.")

        # --- Competitor price warning ---
        if competitor_avg is not None and competitor_avg < product.suggested_price * 0.7:
            notes.append(
                f"PRICING: Precio competencia promedio (${competitor_avg:.2f}) es significativamente "
                f"menor al precio de venta (${product.suggested_price:.2f})."
            )

        # --- Confidence stats ---
        all_confidences = [e.confidence for e in evidences]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        enriched = EnrichedProduct(
            product_id=product.id,
            dropi_name=product.name,
            display_name=display_name,
            category=product.category,
            slug=slug,
            dropi_price=product.dropi_price,
            sale_price=product.suggested_price,
            competitor_avg_price=competitor_avg,
            competitor_price_confidence=price_confidence,
            stock=product.stock,
            supplier_name=product.supplier_name,
            supplier_id=product.supplier_id,
            images=images,
            description_raw=product.description,
            description_clean=description_clean,
            specifications=specifications,
            buyer_concerns=buyer_concerns,
            buyer_positives=buyer_positives,
            real_reviews=real_reviews,
            competition_level=competition_level,
            competition_count=competition_count,
            benefits=benefits,
            copy=None,  # Generated separately by CopyGenerator
            viable=viable,
            viability_reason=viability_reason,
            margin_pct=round(margin, 2),
            net_profit=round(net_profit, 2),
            enriched_at=datetime.utcnow(),
            evidence_count=len(evidences),
            avg_confidence=round(avg_confidence, 3),
            human_review_notes=notes,
            category_config=category_config,
        )

        logger.info(
            f"[EnrichmentEngine] Built EnrichedProduct for '{display_name}': "
            f"{len(evidences)} evidences, avg_confidence={avg_confidence:.2f}, "
            f"viable={viable}, {len(notes)} review notes"
        )
        return enriched

    # --- Private helpers ---

    def _get_competitor_prices(
        self, evidences: list[ProductEvidence]
    ) -> list[tuple[float, float, MatchQuality | None]]:
        """Extract (price, confidence, match_quality) tuples for competitor prices."""
        return [
            (e.value, e.confidence, e.match_quality)
            for e in evidences
            if e.field == "competitor_price" and isinstance(e.value, (int, float))
        ]

    def _compute_competitor_avg(
        self, prices: list[tuple[float, float, MatchQuality | None]]
    ) -> tuple[float | None, float]:
        """Compute weighted average competitor price.

        Only EXACT and SIMILAR matches contribute.
        Returns (avg_price, confidence).
        """
        usable = [
            (price, conf) for price, conf, mq in prices
            if mq in (MatchQuality.EXACT, MatchQuality.SIMILAR)
        ]
        if not usable:
            return None, 0.0

        total_weight = sum(conf for _, conf in usable)
        if total_weight == 0:
            return None, 0.0

        weighted_avg = sum(price * conf for price, conf in usable) / total_weight
        avg_conf = total_weight / len(usable)
        return round(weighted_avg, 2), round(avg_conf, 3)

    def _assess_competition(
        self, evidences: list[ProductEvidence]
    ) -> tuple[int, CompetitionLevel]:
        """Count unique competitors and determine competition level."""
        competitor_urls = {
            e.source_url for e in evidences
            if e.field == "competitor_price" and e.source_url
        }
        count = len(competitor_urls)
        from src.domain.business_rules import COMPETITION_LOW_MAX_SELLERS, COMPETITION_HIGH_MIN_SELLERS
        if count < COMPETITION_LOW_MAX_SELLERS:
            level = CompetitionLevel.LOW
        elif count <= COMPETITION_HIGH_MIN_SELLERS:
            level = CompetitionLevel.MEDIUM
        else:
            level = CompetitionLevel.HIGH
        return count, level

    def _extract_claims(
        self,
        evidences: list[ProductEvidence],
        field: str,
        min_confidence: float,
    ) -> list[EvidencedClaim]:
        """Extract claims of a given field that pass the confidence gate."""
        return [
            EvidencedClaim(
                text=str(e.value),
                data_type=e.data_type,
                confidence=e.confidence,
                source_url=e.source_url,
                origin=e.origin,
            )
            for e in evidences
            if e.field == field and e.confidence >= min_confidence
        ]

    def _derive_benefits(
        self, positives: list[EvidencedClaim]
    ) -> list[EvidencedClaim]:
        """Promote buyer positives to benefits with DERIVED_BENEFIT type."""
        return [
            EvidencedClaim(
                text=p.text,
                data_type=DataType.DERIVED_BENEFIT,
                confidence=min(p.confidence, 0.6),
                source_url=p.source_url,
                origin=p.origin,
            )
            for p in positives
        ]

    def _clean_description(self, raw: str) -> str:
        """Remove phone numbers, junk, and excessive whitespace from description."""
        cleaned = re.sub(r"\+?\d[\d\s\-]{8,}", "", raw)
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:2000]

    def _extract_specs(self, description: str) -> list[ProductSpec]:
        """Extract measurable specifications from product description."""
        specs: list[ProductSpec] = []
        patterns = {
            "Peso": r"(\d+(?:\.\d+)?\s*(?:kg|g|gr|lb))",
            "Volumen": r"(\d+(?:\.\d+)?\s*(?:ml|l|lt|oz|fl))",
            "Dimension": r"(\d+(?:\.\d+)?\s*(?:cm|mm|m|pulgadas|in))",
            "Potencia": r"(\d+(?:\.\d+)?\s*(?:w|watts|v|voltios))",
            "Capacidad": r"(\d+(?:\.\d+)?\s*(?:mah|ah))",
        }
        lower = description.lower()
        for name, pattern in patterns.items():
            match = re.search(pattern, lower)
            if match:
                specs.append(ProductSpec(
                    name=name,
                    value=match.group(1).strip(),
                    data_type=DataType.DERIVED_FACT,
                    confidence=0.8,
                ))
        return specs

    def _clean_display_name(self, name: str) -> str:
        """Clean product name for display: title case, remove codes."""
        cleaned = re.sub(r"\b[A-Z]{2,}\d{2,}\b", "", name)  # Remove codes like GBJ061
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.title() if cleaned.isupper() else cleaned

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from product name."""
        slug = name.lower().strip()
        for old, new in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
            slug = slug.replace(old, new)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug

    def _explain_viability(
        self,
        margin: float,
        competition: CompetitionLevel,
        comp_count: int,
        net_profit: float,
    ) -> str:
        lines = [
            f"Margen: {margin:.1f}% ({'OK' if margin >= TARGET_MARGIN_PCT else 'BAJO'})",
            f"Competencia: {comp_count} vendedores ({competition.value})",
            f"Ganancia neta estimada: ${net_profit:.2f}",
        ]
        return " | ".join(lines)
