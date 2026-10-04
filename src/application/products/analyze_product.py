"""Use case: Analyze a single product for dropshipping viability.

Spec: specs/products/product.spec.md
Criteria: CA-PROD-01, CA-PROD-02, CA-PROD-03
"""

from dataclasses import dataclass
from src.domain.business_rules import (
    MIN_MARGIN_PCT,
    MIN_STOCK_FOR_BUY,
    SCORE_BUY_THRESHOLD,
    SCORE_WATCH_THRESHOLD,
    DEFAULT_TREND_SCORE,
    MARGIN_WEIGHT,
    TREND_WEIGHT,
)
from src.domain.products.entities import (
    Product, ProductScore, ProductRecommendation, CompetitionLevel
)
from src.domain.products.repositories import IProductRepository
from src.shared.logger import logger


@dataclass
class AnalyzeProductInput:
    """Input DTO for the AnalyzeProduct use case."""
    product_id: str
    competition_level: CompetitionLevel = CompetitionLevel.MEDIUM
    trend_score: float = DEFAULT_TREND_SCORE


@dataclass
class AnalyzeProductOutput:
    """Output DTO for the AnalyzeProduct use case."""
    product: Product
    score: ProductScore


class AnalyzeProductUseCase:
    """Analyze a product and generate an AI-informed score.

    Implements SDD: all business rules derive from product.spec.md.
    Depends only on IProductRepository interface (DIP).

    Args:
        product_repo: Repository to fetch product data.
    """

    def __init__(self, product_repo: IProductRepository) -> None:
        self._repo = product_repo

    async def execute(self, input_data: AnalyzeProductInput) -> AnalyzeProductOutput:
        """Execute product analysis.

        Args:
            input_data: Product ID and optional context.

        Returns:
            AnalyzeProductOutput with product and score.

        Raises:
            ProductNotFoundError: If product doesn't exist.
        """
        product = await self._repo.get_product(input_data.product_id)
        logger.info(f"Analyzing product: {product.name} (id={product.id})")

        score = self._calculate_score(product, input_data)
        await self._repo.save_score(score)
        
        # Save to memory to prevent re-analysis
        from pathlib import Path
        memory_file = Path("data/analyzed_products.txt")
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(f"{product.id}\n")

        logger.info(
            f"Product '{product.name}' scored {score.total_score:.1f}/100 → {score.recommendation}"
        )
        return AnalyzeProductOutput(product=product, score=score)

    def _calculate_score(
        self, product: Product, ctx: AnalyzeProductInput
    ) -> ProductScore:
        """Calculate a ProductScore from spec-defined rules.

        Business rules:
        - CA-PROD-01: margin = (selling - cost) / selling * 100
        - CA-PROD-02: score thresholds determine recommendation
        - CA-PROD-03: stock < 10 cannot be BUY

        Args:
            product: The product to score.
            ctx: Additional context (competition, trend).

        Returns:
            ProductScore with recommendation.
        """
        margin = product.margin_pct

        # CA-PROD-01: hard gate — margin below minimum forces immediate SKIP
        if margin < MIN_MARGIN_PCT:
            total = SCORE_WATCH_THRESHOLD - 1  # Force below WATCH threshold → SKIP
        else:
            # Build weighted score only for products that pass the margin gate
            margin_score = min(margin / 60.0 * MARGIN_WEIGHT, MARGIN_WEIGHT)
            trend_component = ctx.trend_score * TREND_WEIGHT
            competition_map = {
                CompetitionLevel.LOW: 30,
                CompetitionLevel.MEDIUM: 15,
                CompetitionLevel.HIGH: 0,
            }
            competition_score = competition_map[ctx.competition_level]
            total = margin_score + trend_component + competition_score

            # CA-PROD-03: stock < MIN_STOCK_FOR_BUY cannot be BUY regardless of score
            if product.stock < MIN_STOCK_FOR_BUY and total >= SCORE_BUY_THRESHOLD:
                total = SCORE_BUY_THRESHOLD - 1  # Force to WATCH

        # CA-PROD-02: Determine recommendation from score
        if total >= SCORE_BUY_THRESHOLD:
            rec = ProductRecommendation.BUY
        elif total >= SCORE_WATCH_THRESHOLD:
            rec = ProductRecommendation.WATCH
        else:
            rec = ProductRecommendation.SKIP

        reasoning_parts = [
            f"Margen bruto: {margin:.1f}% ({'✅' if margin >= MIN_MARGIN_PCT else f'❌ bajo mínimo {MIN_MARGIN_PCT}%'})",
            f"Stock: {product.stock} unidades ({'✅' if product.stock >= MIN_STOCK_FOR_BUY else '⚠️ bajo mínimo'})",
            f"Competencia: {ctx.competition_level.value}",
            f"Tendencia: {ctx.trend_score:.2f}/1.0",
            f"Score final: {total:.1f}/100 → {rec.value}",
        ]

        return ProductScore(
            product_id=product.id,
            margin_pct=round(margin, 2),
            competition_level=ctx.competition_level,
            trend_score=ctx.trend_score,
            total_score=round(total, 2),
            recommendation=rec,
            reasoning=" | ".join(reasoning_parts),
        )
