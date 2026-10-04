"""OrchestratorAgent: Coordinates all domain agents in a ReAct loop.

The orchestrator is the main entry point of the system. It decides:
- Which agents to run and in what order
- How to pass results between agents
- How to handle failures and retries

Activation modes:
- Manual: python scripts/run_orchestrator.py
- Automatic: python scripts/scheduler.py (APScheduler cron)
"""

from typing import Any, Callable
from src.agents.base_agent import BaseAgent
from src.agents.product_analyst_agent import ProductAnalystAgent
from src.domain.products.repositories import IProductRepository
from src.shared.logger import get_agent_logger


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that coordinates all domain agents.

    Follows the Plan-and-Execute pattern:
    1. PLAN: Decide which agents to run based on current context
    2. EXECUTE: Run each agent with appropriate inputs
    3. EVALUATE: Check results and decide next steps
    4. LOOP: Continue until all planned tasks are complete

    Args:
        product_repo: Product repository for ProductAnalystAgent.
        max_iterations: ReAct loop safety limit.
    """

    def __init__(
        self,
        product_repo: IProductRepository,
        max_iterations: int = 10,
    ) -> None:
        super().__init__(max_iterations=max_iterations)
        self._product_agent = ProductAnalystAgent(product_repo)
        self._log = get_agent_logger("OrchestratorAgent")

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el OrchestratorAgent de TiendaDropiEc.\n"
            "Tu trabajo es coordinar los agentes especializados para automatizar"
            " el negocio de dropshipping con Dropi Ecuador.\n\n"
            "Agentes disponibles:\n"
            "- run_product_analysis: Analiza productos y encuentra ganadores\n\n"
            "Planifica y ejecuta las tareas en el orden correcto. "
            "Reporta los resultados en español de forma concisa."
        )

    @property
    def agent_tools(self) -> dict[str, Callable[..., Any]]:
        return {
            "run_product_analysis": self._tool_run_product_analysis,
        }

    async def _tool_run_product_analysis(
        self, category: str = "hogar", limit: int = 25
    ) -> str:
        self._log.info(f"Delegating to ProductAnalystAgent: category='{category}'")
        
        # 1. Find winners
        analysis_result = await self._product_agent._tool_find_winners(category=category, limit=limit)
        
        buy_products = analysis_result.get("buy", [])
        if not buy_products:
            return "No se encontraron productos rentables en esta categoría."
            
        import os
        import json
        
        # 2. Save to Pending Approval (Human in the loop)
        pending_file = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
        
        # Load existing
        pending_data = {}
        if os.path.exists(pending_file):
            try:
                with open(pending_file, "r", encoding="utf-8") as f:
                    pending_data = json.load(f)
            except:
                pass
                
        # Add new BUYs
        for item in buy_products:
            full_prod = await self._product_agent._product_repo.get_product(item["id"])
            pending_data[item["id"]] = {
                "id": full_prod.id,
                "name": full_prod.name,
                "category": full_prod.category,
                "dropi_price": full_prod.dropi_price,
                "suggested_price": full_prod.suggested_price,
                "stock": full_prod.stock,
                "images": full_prod.images,
                "margin_pct": item.get("margin_pct", 0),
                "reasoning": item.get("reasoning", "")
            }
            
        # Save
        os.makedirs(os.path.dirname(pending_file), exist_ok=True)
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)

        return f"Análisis completado. Se enviaron {len(buy_products)} productos ganadores a la bandeja de Aprobación Pendiente."
