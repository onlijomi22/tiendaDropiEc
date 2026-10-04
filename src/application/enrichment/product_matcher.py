"""ProductMatcher: determines if an external listing matches a Dropi product.

A MercadoLibre listing for "destapador liquido" is NOT the same as
"polvo destapa canerías". This module prevents false matches from
contaminating product data with incorrect prices or reviews.
"""

from __future__ import annotations

import re

from src.domain.enrichment.entities import MatchQuality, MatchResult
from src.domain.intelligence.entities import CompetitorListing
from src.domain.products.entities import Product

# Words that carry no product-specific meaning
_STOPWORDS = frozenset({
    "de", "del", "la", "el", "los", "las", "en", "para", "con", "sin",
    "por", "un", "una", "y", "o", "a", "al", "es", "se", "que",
    "su", "x", "pcs", "pzs", "unidades", "pack", "set", "kit",
})


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip accents, split into meaningful tokens."""
    text = text.lower()
    for old, new in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        text = text.replace(old, new)
    tokens = set(re.findall(r"[a-z0-9]+", text))
    return tokens - _STOPWORDS


def _extract_numbers(text: str) -> set[str]:
    """Extract numeric tokens like '500ml', '3l', '2.5kg'."""
    return set(re.findall(r"\d+(?:\.\d+)?(?:ml|l|kg|g|cm|mm|w|v|mah|oz)\b", text.lower()))


class ProductMatcher:
    """Determines if an external listing matches a Dropi product."""

    def match(self, dropi: Product, external: CompetitorListing) -> MatchResult:
        """Compare a Dropi product against an external listing.

        Scoring:
        - Name similarity (40%): Jaccard similarity of meaningful tokens
        - Numeric specs (25%): Shared measurements (500ml, 3L, etc.)
        - Price compatibility (20%): Within reasonable range
        - Category signal (15%): Implicit from name overlap

        Args:
            dropi: The Dropi product.
            external: A competitor listing from MercadoLibre.

        Returns:
            MatchResult with quality classification and reasoning.
        """
        # Name similarity
        dropi_tokens = _tokenize(dropi.name)
        ext_tokens = _tokenize(external.title)
        intersection = dropi_tokens & ext_tokens
        union = dropi_tokens | ext_tokens
        name_sim = len(intersection) / len(union) if union else 0.0

        # Numeric specs bonus
        dropi_nums = _extract_numbers(dropi.name + " " + dropi.description)
        ext_nums = _extract_numbers(external.title)
        nums_match = bool(dropi_nums & ext_nums) if dropi_nums and ext_nums else False
        nums_conflict = bool(dropi_nums and ext_nums and not (dropi_nums & ext_nums))

        # Price compatibility
        if external.price_usd > 0 and dropi.suggested_price > 0:
            ratio = external.price_usd / dropi.suggested_price
            price_compatible = 0.4 <= ratio <= 2.5
            price_close = 0.7 <= ratio <= 1.4
        else:
            price_compatible = True
            price_close = False

        # Weighted score
        score = name_sim * 0.40
        if nums_match:
            score += 0.25
        elif nums_conflict:
            score -= 0.10
        if price_compatible:
            score += 0.10
        if price_close:
            score += 0.10
        # Intersection bonus for strong overlap
        if len(intersection) >= 3:
            score += 0.15

        score = max(0.0, min(1.0, score))

        # Classify
        if score >= 0.7 and name_sim >= 0.5 and price_compatible:
            quality = MatchQuality.EXACT
        elif score >= 0.4 and name_sim >= 0.25:
            quality = MatchQuality.SIMILAR
        else:
            quality = MatchQuality.CATEGORY_ONLY

        reasoning_parts = [
            f"name_sim={name_sim:.2f} ({len(intersection)}/{len(union)} tokens)",
            f"nums={'match' if nums_match else 'conflict' if nums_conflict else 'none'}",
            f"price={'close' if price_close else 'compatible' if price_compatible else 'incompatible'}",
        ]

        return MatchResult(
            quality=quality,
            match_score=round(score, 3),
            name_similarity=round(name_sim, 3),
            price_compatible=price_compatible,
            reasoning=" | ".join(reasoning_parts),
        )
