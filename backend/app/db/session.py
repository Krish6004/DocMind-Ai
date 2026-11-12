"""
Database engine and session management for DocMind AI Backend.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.base import Base
# Import models to ensure they register on Base.metadata
from backend.app.db.models import (  # noqa: F401
    ChatHistoryModel,
    DocumentModel,
    EvaluationHistoryModel,
    ProviderConfigModel,
)

logger = get_logger(__name__)

settings = get_settings()

# Ensure directory for sqlite db exists if path is specified
if settings.DATABASE_URL.startswith("sqlite"):
    db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_path_str and not db_path_str.startswith(":memory:"):
        db_file = Path(db_path_str)
        db_file.parent.mkdir(parents=True, exist_ok=True)

connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Initialize SQLite database tables.
    Creates 'documents' and 'chat_history' tables if they don't exist.
    """
    logger.info("Initializing SQLite database tables at %s", settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request.
    Closes the session after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
