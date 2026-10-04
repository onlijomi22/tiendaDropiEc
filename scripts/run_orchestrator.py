"""Entry point: Run the OrchestratorAgent manually.

Usage:
    python scripts/run_orchestrator.py
    python scripts/run_orchestrator.py --task "Analiza categoría hogar"
"""

import asyncio
import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shared.logger import setup_logger, logger
from src.infrastructure.dropi.dropi_browser import DropiBrowser
from src.infrastructure.dropi.dropi_product_repo import DropiProductRepository
from src.agents.orchestrator_agent import OrchestratorAgent


async def main(task: str) -> None:
    """Initialize all dependencies and run the orchestrator."""
    setup_logger()
    logger.info("=" * 60)
    logger.info("TiendaDropiEc Orchestrator - Manual Run")
    logger.info("=" * 60)

    browser = await DropiBrowser.get_instance()
    product_repo = DropiProductRepository(browser)

    orchestrator = OrchestratorAgent(product_repo=product_repo)

    try:
        result = await orchestrator.run(task)
        logger.info("Orchestrator completed successfully.")
        print("\n" + "=" * 60)
        print("RESULTADO:")
        print(result)
        print("=" * 60)
    finally:
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TiendaDropiEc Orchestrator")
    parser.add_argument(
        "--task",
        default="Ejecuta el análisis diario: encuentra los mejores productos en las categorías principales de Dropi.",
        help="Task for the orchestrator agent",
    )
    args = parser.parse_args()
    asyncio.run(main(args.task))
