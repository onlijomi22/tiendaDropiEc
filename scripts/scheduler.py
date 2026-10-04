"""Entry point: APScheduler automatic orchestration.

Runs agents on configurable cron schedules from .env:
- SCHEDULER_PRODUCTS_CRON: Product analysis (default: every 6h)
- SCHEDULER_ADS_CRON: Ads optimization (default: every 12h)
- SCHEDULER_ANALYTICS_CRON: Daily report (default: 8 AM daily)

Usage:
    python scripts/scheduler.py
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.shared.logger import setup_logger, logger
from src.shared.config import get_scheduler_settings
from src.infrastructure.dropi.dropi_browser import DropiBrowser
from src.infrastructure.dropi.dropi_product_repo import DropiProductRepository
from src.agents.orchestrator_agent import OrchestratorAgent


async def run_product_analysis_job() -> None:
    """Scheduled job: analyze Dropi products for winners."""
    logger.info("[SCHEDULER] Running product analysis job")
    browser = await DropiBrowser.get_instance()
    product_repo = DropiProductRepository(browser)
    agent = OrchestratorAgent(product_repo=product_repo)
    result = await agent.run(
        "Analiza las categorías más rentables de Dropi y encuentra los mejores productos BUY."
    )
    logger.info(f"[SCHEDULER] Product analysis complete: {result[:200]}")


async def run_analytics_job() -> None:
    """Scheduled job: generate daily analytics report."""
    logger.info("[SCHEDULER] Running analytics report job")
    # TODO: instantiate AnalyticsAgent when implemented
    logger.info("[SCHEDULER] Analytics job placeholder - implement AnalyticsAgent")


async def main() -> None:
    """Configure and start the APScheduler."""
    setup_logger()
    settings = get_scheduler_settings()
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_product_analysis_job,
        trigger=CronTrigger.from_crontab(settings.products_cron),
        id="product_analysis",
        name="Product Analysis",
        replace_existing=True,
    )

    scheduler.add_job(
        run_analytics_job,
        trigger=CronTrigger.from_crontab(settings.analytics_cron),
        id="analytics_report",
        name="Daily Analytics Report",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("TiendaDropiEc Scheduler started.")
    logger.info(f"  Products: {settings.products_cron}")
    logger.info(f"  Analytics: {settings.analytics_cron}")

    try:
        # Run forever
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
        browser = await DropiBrowser.get_instance()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
