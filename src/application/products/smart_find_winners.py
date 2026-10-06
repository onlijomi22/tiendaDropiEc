"""Smart Find Winners: two-phase scoring for efficient product discovery.

Phase 1 (fast, ~1s): Filter by margin + stock — eliminate obvious SKIPs
Phase 2 (deep, ~20s each): Smart Score only candidates that pass Phase 1
  - Google Trends
  - MercadoLibre competition with matching
  - Social demand via Gemini
  - Image quality assessment

This avoids spending 5 minutes scoring products with 10% margin.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.application.products.smart_scoring import SmartScoringUseCase, SmartScoreResult
from src.domain.business_rules import MIN_MARGIN_PCT, MIN_STOCK_FOR_BUY
from src.domain.products.entities import Product, ProductRecommendation
from src.domain.products.repositories import IProductRepository
from src.shared.logger import logger

_MAX_PRODUCTS_PER_RUN = 30
_MAX_SMART_SCORE = 10  # Max products to deep-score (avoid long runs)


@dataclass
class SmartFindWinnersInput:
    category: str
    limit: int = _MAX_PRODUCTS_PER_RUN


@dataclass
class SmartFindWinnersOutput:
    buy: list[SmartScoreResult] = field(default_factory=list)
    watch: list[SmartScoreResult] = field(default_factory=list)
    skip_fast: int = 0  # Skipped in Phase 1 (never deep-scored)
    total_scanned: int = 0
    total_deep_scored: int = 0


class SmartFindWinnersUseCase:
    """Two-phase product discovery with real multi-source scoring."""

    def __init__(self, product_repo: IProductRepository) -> None:
        self._repo = product_repo
        self._smart_scorer = SmartScoringUseCase(product_repo=product_repo)

    async def execute(self, inp: SmartFindWinnersInput) -> SmartFindWinnersOutput:
        """Scan category with two-phase scoring.

        Phase 1: Fast filter (margin + stock)
        Phase 2: Smart Score top candidates

        Args:
            inp: Category and limit.

        Returns:
            SmartFindWinnersOutput with BUY/WATCH results and stats.
        """
        limit = min(inp.limit, _MAX_PRODUCTS_PER_RUN)
        products = await self._repo.get_catalog(inp.category, limit=limit)
        logger.info(f"[SmartFindWinners] Phase 1: scanning {len(products)} products in '{inp.category}'")

        output = SmartFindWinnersOutput(total_scanned=len(products))

        # Phase 1: Fast filter
        from pathlib import Path
        from src.domain.business_rules import ESTIMATED_CPA_USD, ESTIMATED_SHIPPING_COST_USD

        candidates: list[Product] = []
        skipped_ids: list[str] = []
        for p in products:
            margin = p.margin_pct
            if margin < MIN_MARGIN_PCT:
                output.skip_fast += 1
                skipped_ids.append(p.id)
                continue
            if p.stock < MIN_STOCK_FOR_BUY:
                output.skip_fast += 1
                skipped_ids.append(p.id)
                continue
            net = p.suggested_price - p.dropi_price - ESTIMATED_CPA_USD - ESTIMATED_SHIPPING_COST_USD
            if net <= 0:
                output.skip_fast += 1
                skipped_ids.append(p.id)
                continue
            candidates.append(p)

        # Register skipped products so they don't reappear
        if skipped_ids:
            memory_file = Path("data/analyzed_products.txt")
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(memory_file, "a", encoding="utf-8") as f:
                for pid in skipped_ids:
                    f.write(f"{pid}\n")

        # Sort by margin descending, take top N for deep scoring
        candidates.sort(key=lambda p: p.margin_pct, reverse=True)
        to_score = candidates[:_MAX_SMART_SCORE]

        logger.info(
            f"[SmartFindWinners] Phase 1 done: {len(candidates)} candidates, "
            f"{output.skip_fast} fast-skipped, {len(to_score)} to deep-score"
        )

        # Phase 2: Smart Score
        for i, product in enumerate(to_score):
            logger.info(f"[SmartFindWinners] Phase 2: scoring {i+1}/{len(to_score)} — {product.name}")
            try:
                result = await self._smart_scorer.score_product(product)
                output.total_deep_scored += 1
                if result.score.recommendation == ProductRecommendation.BUY:
                    output.buy.append(result)
                else:
                    output.watch.append(result)
            except Exception as e:
                logger.warning(f"[SmartFindWinners] Smart scoring failed for {product.id}: {e}")

        # Sort BUY by score descending
        output.buy.sort(key=lambda r: r.score.total_score, reverse=True)
        output.watch.sort(key=lambda r: r.score.total_score, reverse=True)

        logger.info(
            f"[SmartFindWinners] Done: {len(output.buy)} BUY, {len(output.watch)} WATCH, "
            f"{output.skip_fast} fast-skipped out of {output.total_scanned}"
        )
        return output
