"""Structured logging setup using loguru.

Provides a singleton logger with:
- Colored console output with rich formatting
- File rotation (10MB, 7 days retention)
- Structured JSON format for file output
- Agent-aware context (agent_name field)
"""

import sys
from pathlib import Path
from loguru import logger
from src.shared.config import get_app_settings


def setup_logger() -> None:
    """Configure loguru logger. Call once at application startup."""
    settings = get_app_settings()
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()  # Remove default handler

    # Console: human-readable, colored
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File: structured JSON for analysis
    logger.add(
        str(log_file),
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        serialize=True,  # JSON output
    )


def get_agent_logger(agent_name: str):
    """Return a contextualized logger bound to a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'ProductAnalystAgent')

    Returns:
        Loguru logger with agent_name bound to all messages.
    """
    return logger.bind(agent=agent_name)


# Convenience re-export
__all__ = ["logger", "setup_logger", "get_agent_logger"]
