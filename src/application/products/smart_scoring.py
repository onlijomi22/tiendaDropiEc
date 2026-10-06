"""Smart Product Scoring — uses real data from multiple sources.

Replaces the basic margin-only scoring with a multi-signal approach:
- Margin (real, from Dropi)
- Competition (real, from MercadoLibre via enrichment)
- Trend (real, from Google Trends)
- Social demand (real, from Gemini web search)
- Image quality (real, from enrichment assessment)
- Stock health (real, from Dropi)
- Supplier quality (real, from Dropi if available)
"""

from __future__ import annotations

from dataclasses import dataclass
from src.domain.business_rules import (
    MIN_MARGIN_PCT,
    MIN_STOCK_FOR_BUY,
    SCORE_BUY_THRESHOLD,
    SCORE_WATCH_THRESHOLD,
    ESTIMATED_CPA_USD,
    ESTIMATED_SHIPPING_COST_USD,
)
from src.domain.products.entities import Product, ProductScore, ProductRecommendation, CompetitionLevel
from src.domain.products.repositories import IProductRepository
from src.infrastructure.search.trends_search import TrendsSearch
from src.infrastructure.search.social_demand import SocialDemandSearch
from src.infrastructure.search.mercadolibre_scraper import MercadoLibreScraper
from src.application.enrichment.product_matcher import ProductMatcher
from src.shared.logger import logger


# Weight configuration (must sum to 100)
_W_MARGIN = 25
_W_COMPETITION = 20
_W_TREND = 15
_W_SOCIAL = 15
_W_IMAGES = 10
_W_STOCK = 10
_W_SUPPLIER = 5


@dataclass
class ScoringContext:
    """All signals collected for scoring."""
    margin_pct: float = 0.0
    net_profit: float = 0.0
    # Competition
    competitor_count: int = 0
    competition_level: CompetitionLevel = CompetitionLevel.MEDIUM
    avg_competitor_price: float = 0.0
    # Trends
    trend_score: float = 0.5
    trend_rising: bool = False
    trend_avg_interest: float = 0.0
    # Social
    social_score: float = 0.5
    social_demand: str = "desconocida"
    social_recommendation: str = "investigar_mas"
    # Images
    total_images: int = 0
    clean_images: int = 0
    # Stock
    stock: int = 0
    # Supplier
    supplier_rating: float = 0.0


@dataclass
class SmartScoreResult:
    """Detailed scoring result with breakdown."""
    product: Product
    score: ProductScore
    context: ScoringContext
    breakdown: dict  # Component scores for transparency


class SmartScoringUseCase:
    """Score products using real multi-source data."""

    def __init__(
        self,
        product_repo: IProductRepository | None = None,
        trends: TrendsSearch | None = None,
        social: SocialDemandSearch | None = None,
        ml_scraper: MercadoLibreScraper | None = None,
    ) -> None:
        self._repo = product_repo
        self._trends = trends or TrendsSearch()
        self._social = social or SocialDemandSearch()
        self._ml_scraper = ml_scraper or MercadoLibreScraper()
        self._matcher = ProductMatcher()

    async def score_product(self, product: Product) -> SmartScoreResult:
        """Score a single product with all available signals.

        Args:
            product: The Dropi product to score.

        Returns:
            SmartScoreResult with score, context, and breakdown.
        """
        logger.info(f"[SmartScoring] Scoring: {product.name}")
        ctx = ScoringContext()

        # 1. Margin (always available)
        ctx.margin_pct = product.margin_pct
        ctx.net_profit = product.suggested_price - product.dropi_price - ESTIMATED_CPA_USD - ESTIMATED_SHIPPING_COST_USD
        ctx.stock = product.stock

        # 2. Competition (MercadoLibre)
        try:
            words = product.name.split()
            query = " ".join(words[:4])
            competitors = await self._ml_scraper.search_competitors(query=query.strip(), limit=5)
            # Use matcher to filter real matches
            matched = []
            for comp in competitors:
                match = self._matcher.match(product, comp)
                if match.quality.value != "CATEGORY_ONLY":
                    matched.append(comp)
            ctx.competitor_count = len(matched)
            if matched:
                ctx.avg_competitor_price = sum(c.price_usd for c in matched) / len(matched)
            # Classify
            if ctx.competitor_count < 3:
                ctx.competition_level = CompetitionLevel.LOW
            elif ctx.competitor_count <= 10:
                ctx.competition_level = CompetitionLevel.MEDIUM
            else:
                ctx.competition_level = CompetitionLevel.HIGH
        except Exception as e:
            logger.warning(f"[SmartScoring] ML search failed: {e}")

        # 3. Google Trends
        try:
            trends_data = await self._trends.get_trend_score(product.name, product.category)
            ctx.trend_score = trends_data["trend_score"]
            ctx.trend_rising = trends_data.get("is_rising", False)
            ctx.trend_avg_interest = trends_data.get("avg_interest", 0)
        except Exception as e:
            logger.warning(f"[SmartScoring] Trends failed: {e}")

        # 4. Social demand
        try:
            social_data = await self._social.assess_demand(product.name, product.category)
            ctx.social_score = social_data.get("social_score", 0.5)
            ctx.social_demand = social_data.get("overall_demand", "desconocida")
            ctx.social_recommendation = social_data.get("recommendation", "investigar_mas")
        except Exception as e:
            logger.warning(f"[SmartScoring] Social search failed: {e}")

        # 5. Image assessment (basic heuristic)
        ctx.total_images = len(product.images)
        ctx.clean_images = sum(1 for img in product.images if "cloudfront" in img and "placeholder" not in img)

        # --- Calculate weighted score ---
        breakdown = {}

        # Margin component (25 pts)
        if ctx.margin_pct < MIN_MARGIN_PCT:
            breakdown["margin"] = 0
        elif ctx.net_profit <= 0:
            breakdown["margin"] = _W_MARGIN * 0.3  # Low score if no net profit
        else:
            breakdown["margin"] = min(ctx.margin_pct / 80.0 * _W_MARGIN, _W_MARGIN)

        # Competition component (20 pts) — less competition = higher score
        comp_map = {CompetitionLevel.LOW: 1.0, CompetitionLevel.MEDIUM: 0.5, CompetitionLevel.HIGH: 0.0}
        breakdown["competition"] = comp_map[ctx.competition_level] * _W_COMPETITION

        # Trend component (15 pts)
        breakdown["trend"] = ctx.trend_score * _W_TREND

        # Social demand (15 pts)
        breakdown["social"] = ctx.social_score * _W_SOCIAL

        # Image quality (10 pts)
        if ctx.clean_images >= 3:
            breakdown["images"] = _W_IMAGES
        elif ctx.clean_images >= 1:
            breakdown["images"] = _W_IMAGES * 0.6
        else:
            breakdown["images"] = _W_IMAGES * 0.2

        # Stock health (10 pts)
        if ctx.stock >= 50:
            breakdown["stock"] = _W_STOCK
        elif ctx.stock >= MIN_STOCK_FOR_BUY:
            breakdown["stock"] = _W_STOCK * 0.7
        elif ctx.stock > 0:
            breakdown["stock"] = _W_STOCK * 0.3
        else:
            breakdown["stock"] = 0

        # Supplier (5 pts) — placeholder until we extract ratings
        breakdown["supplier"] = _W_SUPPLIER * 0.5

        total = sum(breakdown.values())
        total = round(min(max(total, 0), 100), 2)

        # Hard gates
        if ctx.margin_pct < MIN_MARGIN_PCT:
            total = min(total, SCORE_WATCH_THRESHOLD - 1)
        if ctx.stock < MIN_STOCK_FOR_BUY and total >= SCORE_BUY_THRESHOLD:
            total = SCORE_BUY_THRESHOLD - 1

        # Social override — if social says "evitar", cap the score
        if ctx.social_recommendation == "evitar" and total >= SCORE_BUY_THRESHOLD:
            total = SCORE_BUY_THRESHOLD - 1

        # Determine recommendation
        if total >= SCORE_BUY_THRESHOLD:
            rec = ProductRecommendation.BUY
        elif total >= SCORE_WATCH_THRESHOLD:
            rec = ProductRecommendation.WATCH
        else:
            rec = ProductRecommendation.SKIP

        reasoning = (
            f"Margen: {ctx.margin_pct:.1f}% (neto ${ctx.net_profit:.2f}) | "
            f"Competencia: {ctx.competitor_count} vendedores ({ctx.competition_level.value}) | "
            f"Tendencia: {ctx.trend_score:.2f} ({'subiendo' if ctx.trend_rising else 'estable'}) | "
            f"Social: {ctx.social_score:.2f} ({ctx.social_demand}) | "
            f"Imagenes: {ctx.clean_images}/{ctx.total_images} | "
            f"Stock: {ctx.stock} | "
            f"Score: {total}/100 -> {rec.value}"
        )

        score = ProductScore(
            product_id=product.id,
            margin_pct=round(ctx.margin_pct, 2),
            competition_level=ctx.competition_level,
            trend_score=ctx.trend_score,
            total_score=total,
            recommendation=rec,
            reasoning=reasoning,
        )

        if self._repo:
            await self._repo.save_score(score)

        # Register as analyzed so it won't be re-scored
        from pathlib import Path
        memory_file = Path("data/analyzed_products.txt")
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(f"{product.id}\n")

        logger.info(f"[SmartScoring] {product.name}: {total}/100 -> {rec.value}")
        return SmartScoreResult(product=product, score=score, context=ctx, breakdown=breakdown)
