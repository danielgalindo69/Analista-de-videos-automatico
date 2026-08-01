"""
Centralized Loguru configuration.

Design decisions:
- Called ONCE at application startup (main.py or CLI entry point)
- Removes Loguru's default handler before adding custom ones
  to avoid duplicate output
- Two sinks: stderr (colored, human-readable) + rotating file
- Log level driven by AppSettings — never hardcoded
- Structured format includes function name for easy code navigation

Usage:
    from infrastructure.logging.setup import setup_logging
    setup_logging()  # Call once at startup

Then anywhere in the codebase:
    from loguru import logger
    logger.info("Message")
    logger.debug("Debug data: {data}", data=some_dict)
"""

import sys
from pathlib import Path

from loguru import logger

from config.settings import get_settings


def setup_logging() -> None:
    """
    Initialize Loguru with project-wide configuration.
    Must be called once before any logging occurs.
    """
    settings = get_settings()
    log_level = settings.logging.level
    log_dir = Path(settings.logging.dir)

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default Loguru handler to avoid double output
    logger.remove()

    # --- Sink 1: Stderr (colored, human-readable) ---
    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        backtrace=True,
        diagnose=True,
    )

    # --- Sink 2: Rotating file (plain text, full detail) ---
    logger.add(
        log_dir / "framework_{time:YYYY-MM-DD}.log",
        level=log_level,
        rotation="00:00",       # New file each day at midnight
        retention="14 days",    # Keep 14 days of logs
        compression="zip",      # Compress old logs
        encoding="utf-8",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        backtrace=True,
        diagnose=True,
    )

    logger.info(
        "Logging initialized. level={level} log_dir={log_dir}",
        level=log_level,
        log_dir=str(log_dir),
    )
