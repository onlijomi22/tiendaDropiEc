"""Use case: Evaluate product viability based on economics and competition.

Decides whether a product is worth selling based on margin, competition,
pricing constraints, and physical characteristics.
"""

from __future__ import annotations
from dataclasses import dataclass

from src.domain.business_rules import (
    TARGET_MARGIN_PCT,
    ESTIMATED_CPA_USD,
    ESTIMATED_SHIPPING_COST_USD,
    TARGET_PROFIT_USD,
)
from src.domain.intelligence.entities import MarketInsight, ProductCopyDraft
from src.domain.products.entities import CompetitionLevel, Product
from src.shared.logger import logger


@dataclass
class ViabilityResult:
    """Result of viability evaluation."""
    viable: bool
    reason: str
    net_profit: float
    margin_pct: float
    minimum_viable_price: float


class EvaluateViabilityUseCase:
    """Evaluate whether a product is economically viable to sell.

    Rules:
    - margin >= TARGET_MARGIN_PCT and competition != HIGH -> viable
    - is_bulky -> not viable (needs manual logistics review)
    - If AI suggests price below minimum viable price -> flag for review
    """

    def execute(
        self,
        product: Product,
        sale_price: float,
        market_insight: MarketInsight,
        copy_draft: ProductCopyDraft,
    ) -> tuple[bool, str, ProductCopyDraft]:
        """Evaluate viability and optionally annotate the copy draft.

        Args:
            product: The product to evaluate.
            sale_price: Target sale price.
            market_insight: Market research data.
            copy_draft: Generated copy (may be annotated with pricing warnings).

        Returns:
            Tuple of (viable, viability_reason, updated_copy_draft).
        """
        minimum_viable_price = (
            product.dropi_price + ESTIMATED_SHIPPING_COST_USD
            + ESTIMATED_CPA_USD + TARGET_PROFIT_USD
        )
        net_profit = (
            sale_price - product.dropi_price
            - ESTIMATED_CPA_USD - ESTIMATED_SHIPPING_COST_USD
        )
        margin = (sale_price - product.dropi_price) / sale_price * 100

        # Pricing rule: economic formula has priority over AI suggestion
        suggested_market_price = copy_draft.suggested_price_usd
        if suggested_market_price < minimum_viable_price:
            copy_draft = copy_draft.model_copy(update={
                "human_review_notes": (
                    f"{copy_draft.human_review_notes}\n"
                    f"⚠️ PRICING REVIEW: IA sugiere ${suggested_market_price:.2f} pero el precio "
                    f"minimo viable es ${minimum_viable_price:.2f}. No se redujo el precio automaticamente."
                ),
            })

        viable = (
            margin >= TARGET_MARGIN_PCT
            and market_insight.competition_level != CompetitionLevel.HIGH
        )

        if copy_draft.is_bulky:
            viable = False
            viability_reason = "Rechazado por volumen (Requiere revision manual de logistica)"
        else:
            viability_reason = self._explain(
                viable, margin, market_insight, sale_price,
                product.dropi_price, net_profit
            )

        logger.info(
            f"[EvaluateViability] Viable={viable}, "
            f"Margin={margin:.1f}%, Competition={market_insight.competition_level}"
        )

        return viable, viability_reason, copy_draft

    def _explain(
        self, viable: bool, margin: float, insight: MarketInsight,
        sale_price: float, cost: float, net_profit: float,
    ) -> str:
        lines = [
            f"Margen bruto: {margin:.1f}% ({'✅' if margin >= TARGET_MARGIN_PCT else f'⚠️ bajo el objetivo de {TARGET_MARGIN_PCT}%'})",
            f"Competencia: {insight.competition_count} vendedores -> {insight.competition_level.value}",
            f"Precio promedio competencia: ${insight.avg_competitor_price:.2f}",
            f"Tu precio sugerido: ${sale_price:.2f} | Costo: ${cost:.2f} | Ganancia neta: ${net_profit:.2f}",
        ]
        if not viable:
            if margin < TARGET_MARGIN_PCT:
                lines.append("⚠️ Sube el precio de venta para mejorar margen.")
            if insight.competition_level == CompetitionLevel.HIGH:
                lines.append("⚠️ Alta competencia. Considera diferenciarte por precio o bundle.")
        return "\n".join(lines)
