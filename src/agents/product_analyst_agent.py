"""ProductAnalystAgent: Analyzes Dropi products and finds winners.

Responsibilities:
- Scan Dropi catalog by category
- Score each product using domain rules (spec CA-PROD-01/02/03)
- Return ranked list of BUY recommendations

Skill: .agents/skills/dropi-products/SKILL.md
"""

from typing import Any, Callable
from src.agents.base_agent import BaseAgent
from src.application.products.analyze_product import (
    AnalyzeProductInput, AnalyzeProductUseCase
)
from src.application.products.find_winners import FindWinnersInput, FindWinnersUseCase
from src.domain.business_rules import (
    MIN_MARGIN_PCT,
    SCORE_BUY_THRESHOLD,
    SCORE_WATCH_THRESHOLD,
    MIN_STOCK_FOR_BUY,
    MAX_PRODUCTS_PER_RUN,
)
from src.domain.products.repositories import IProductRepository


class ProductAnalystAgent(BaseAgent):
    """Gemini agent specialized in Dropi product research and scoring.

    Uses FindWinnersUseCase and AnalyzeProductUseCase to evaluate
    products from the Dropi catalog against spec-defined criteria.

    Args:
        product_repo: Dropi product repository implementation.
        max_iterations: ReAct loop safety limit.
    """

    def __init__(
        self, product_repo: IProductRepository, max_iterations: int = 10
    ) -> None:
        super().__init__(max_iterations=max_iterations)
        self._product_repo = product_repo
        self._find_winners_uc = FindWinnersUseCase(product_repo)
        self._analyze_uc = AnalyzeProductUseCase(product_repo)

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el ProductAnalystAgent de TiendaDropiEc, un experto en "
            "análisis de productos para dropshipping en Ecuador usando la plataforma Dropi.\n\n"
            "Tu objetivo es identificar los mejores productos para vender, "
            "basado en criterios de margen, stock, competencia y tendencia.\n\n"
            "Reglas de negocio (de la spec):\n"
            f"- Margen mínimo: {MIN_MARGIN_PCT}% (CA-PROD-01)\n"
            f"- Score BUY >= {SCORE_BUY_THRESHOLD}, WATCH {SCORE_WATCH_THRESHOLD}-{SCORE_BUY_THRESHOLD - 1}, SKIP < {SCORE_WATCH_THRESHOLD} (CA-PROD-02)\n"
            f"- Stock mínimo para BUY: {MIN_STOCK_FOR_BUY} unidades (CA-PROD-03)\n"
            f"- Máximo {MAX_PRODUCTS_PER_RUN} productos por análisis\n\n"
            "Usa las herramientas disponibles para analizar productos y "
            "presenta tus resultados de forma clara y accionable en español."
        )

    @property
    def agent_tools(self) -> dict[str, Callable[..., Any]]:
        return {
            "find_winners_in_category": self._tool_find_winners,
            "analyze_single_product": self._tool_analyze_product,
            "get_buy_recommendations": self._tool_get_buy_recs,
        }

    async def _tool_find_winners(
        self, category: str, limit: int = 20
    ) -> dict:
        """Find winning products in a Dropi category.

        Args:
            category: Dropi category name.
            limit: Max products to analyze (max 50).

        Returns:
            Dict with BUY, WATCH, SKIP lists.
        """
        result = await self._find_winners_uc.execute(
            FindWinnersInput(category=category, limit=limit)
        )
        return {
            "total_analyzed": result.total_analyzed,
            "buy": [
                {
                    "id": r.product.id,
                    "name": r.product.name,
                    "score": r.score.total_score,
                    "margin_pct": r.score.margin_pct,
                    "recommendation": r.score.recommendation.value,
                    "reasoning": r.score.reasoning,
                }
                for r in result.buy
            ],
            "watch": [r.product.name for r in result.watch],
            "skip_count": len(result.skip),
        }

    async def _tool_analyze_product(self, product_id: str) -> dict:
        """Analyze a single product by its Dropi ID."""
        result = await self._analyze_uc.execute(
            AnalyzeProductInput(product_id=product_id)
        )
        return {
            "name": result.product.name,
            "score": result.score.total_score,
            "recommendation": result.score.recommendation.value,
            "reasoning": result.score.reasoning,
        }

    async def _tool_get_buy_recs(self) -> list[dict]:
        """Retrieve all previously stored BUY recommendations."""
        scores = await self._product_repo.get_scored_products(recommendation="BUY")
        return [
            {"product_id": s.product_id, "score": s.total_score, "reasoning": s.reasoning}
            for s in scores
        ]
