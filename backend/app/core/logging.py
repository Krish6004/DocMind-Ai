"""
Centralized logging setup for DocMind AI Backend.

Integrates with the core DocMind AI logging architecture in src.logger.
"""

from __future__ import annotations

import logging
import sys

from backend.app.core.config import get_settings
from src.logger import DEFAULT_LOG_FORMAT, configure_logging, get_logger as get_src_logger


def setup_backend_logging() -> None:
    """
    Initialize centralized logging for the FastAPI backend using configured settings.
    """
    settings = get_settings()
    level = settings.DOCMIND_LOG_LEVEL.upper()
    numeric_level = getattr(logging, level, logging.INFO)

    configure_logging(level=numeric_level, log_format=DEFAULT_LOG_FORMAT)

    # Configure uvicorn loggers to match DocMind AI format
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_logger_name)
        u_logger.setLevel(numeric_level)


def get_logger(name: str = "docmind.backend") -> logging.Logger:
    """
    Retrieve a standardized logger for backend components.
    """
    return get_src_logger(name)
