"""
Centralized logging configuration for DocMind AI.

Provides consistent formatting, level management, and logger instantiation
across all pipeline components.
"""

from __future__ import annotations

import logging
import os
import sys

DEFAULT_LOG_FORMAT: str = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)
DEFAULT_LOG_LEVEL: str = os.environ.get("DOCMIND_LOG_LEVEL", "INFO").upper()


def configure_logging(
    level: str | int | None = None,
    log_format: str = DEFAULT_LOG_FORMAT,
) -> None:
    """
    Configure the root logger for DocMind AI.

    Args:
        level: Logging level (e.g. "DEBUG", "INFO", logging.INFO).
               Defaults to the DOCMIND_LOG_LEVEL environment variable or "INFO".
        log_format: Formatter pattern for stream log records.
    """
    if level is None:
        level = DEFAULT_LOG_LEVEL

    numeric_level = (
        level if isinstance(level, int) else getattr(logging, str(level).upper(), logging.INFO)
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if already configured
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: str = "docmind") -> logging.Logger:
    """
    Retrieve a named logger instance configured with DocMind AI standards.

    Args:
        name: Name of the logger, typically __name__ of the calling module.

    Returns:
        logging.Logger instance.
    """
    if not logging.getLogger().handlers:
        configure_logging()

    return logging.getLogger(name)
