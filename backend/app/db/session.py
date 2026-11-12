"""
Database engine and session management for DocMind AI Backend.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
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
    Initialize SQLite database tables and ensure Sprint 7.0 user_id columns exist.
    """
    logger.info("Initializing SQLite database tables at %s", settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            for table in ("documents", "chat_history", "evaluation_history"):
                cols = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
                if cols and "user_id" not in cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT 'default'"))
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_user_id ON {table} (user_id)"))
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
