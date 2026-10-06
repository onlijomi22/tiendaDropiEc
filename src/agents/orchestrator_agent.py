"""OrchestratorAgent: Coordinates product discovery with Smart Scoring.

Uses two-phase scoring:
Phase 1 (fast): Filter by margin + stock + net profit
Phase 2 (deep): Smart Score with Google Trends, MercadoLibre, social demand
"""

import json
import os
from typing import Any, Callable

from src.agents.base_agent import BaseAgent
from src.application.products.smart_find_winners import (
    SmartFindWinnersInput,
    SmartFindWinnersUseCase,
)
from src.domain.products.repositories import IProductRepository
from src.shared.logger import get_agent_logger


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that finds winning products with real data scoring."""

    def __init__(
        self,
        product_repo: IProductRepository,
        max_iterations: int = 10,
    ) -> None:
        super().__init__(max_iterations=max_iterations)
        self._product_repo = product_repo
        self._smart_finder = SmartFindWinnersUseCase(product_repo)
        self._log = get_agent_logger("OrchestratorAgent")

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el OrchestratorAgent de TiendaDropiEc.\n"
            "Tu trabajo es encontrar los mejores productos para vender en Ecuador.\n\n"
            "Usas Smart Scoring que analiza:\n"
            "- Margen real y ganancia neta\n"
            "- Competencia en MercadoLibre\n"
            "- Tendencia en Google Trends Ecuador\n"
            "- Demanda social (Facebook, TikTok)\n"
            "- Calidad de imagenes\n"
            "- Stock disponible\n\n"
            "Ejecuta run_product_analysis con la categoria indicada.\n"
            "Reporta resultados en espanol de forma concisa."
        )

    @property
    def agent_tools(self) -> dict[str, Callable[..., Any]]:
        return {
            "run_product_analysis": self._tool_run_product_analysis,
        }

    async def _tool_run_product_analysis(
        self, category: str = "hogar", limit: int = 25
    ) -> str:
        """Find winning products using Smart Scoring."""
        self._log.info(f"Starting Smart Find Winners: category='{category}', limit={limit}")

        result = await self._smart_finder.execute(
            SmartFindWinnersInput(category=category, limit=limit)
        )

        if not result.buy and not result.watch:
            return (
                f"Se escanearon {result.total_scanned} productos en '{category}'. "
                f"{result.skip_fast} eliminados por margen/stock insuficiente. "
                f"Ninguno paso el Smart Scoring como BUY."
            )

        # Save BUYs to pending approval
        pending_file = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
        pending_data = {}
        if os.path.exists(pending_file):
            try:
                with open(pending_file, "r", encoding="utf-8") as f:
                    pending_data = json.load(f)
            except Exception:
                pass

        for item in result.buy:
            p = item.product
            pending_data[p.id] = {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "dropi_price": p.dropi_price,
                "suggested_price": p.suggested_price,
                "stock": p.stock,
                "images": p.images,
                "margin_pct": round(item.context.margin_pct, 2),
                "reasoning": item.score.reasoning,
                "smart_score": item.score.total_score,
                "trend_score": item.context.trend_score,
                "social_score": item.context.social_score,
                "competition_level": item.context.competition_level.value,
                "net_profit": round(item.context.net_profit, 2),
            }

        os.makedirs(os.path.dirname(pending_file), exist_ok=True)
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)

        # Build summary
        summary_lines = [
            f"Smart Scoring completado para '{category}':",
            f"  Escaneados: {result.total_scanned}",
            f"  Eliminados (margen/stock): {result.skip_fast}",
            f"  Deep-scored: {result.total_deep_scored}",
            f"  BUY: {len(result.buy)}",
            f"  WATCH: {len(result.watch)}",
            "",
        ]

        if result.buy:
            summary_lines.append("Productos BUY (enviados a Pendientes):")
            for item in result.buy:
                summary_lines.append(
                    f"  - {item.product.name}: {item.score.total_score:.0f}/100 "
                    f"(margen {item.context.margin_pct:.0f}%, "
                    f"trend {item.context.trend_score:.2f}, "
                    f"social {item.context.social_score:.2f})"
                )

        return "\n".join(summary_lines)
