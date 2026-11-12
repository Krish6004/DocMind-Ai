"""
SQLAlchemy ORM models for AI Provider configuration and priority management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from backend.app.db.base import Base


class ProviderConfigModel(Base):
    """
    SQLAlchemy model representing an AI Provider's configuration,
    credentials source (Developer Hosted vs BYOK), selected model,
    and priority rank for fallback execution.
    """

    __tablename__ = "provider_configs"

    provider_id = Column(
        String(32),
        primary_key=True,
        index=True,
        doc="Unique identifier for the provider (gemini, groq, openai, anthropic, ollama)",
    )
    mode = Column(
        String(16),
        nullable=False,
        default="developer",
        doc="Mode: 'developer' (uses .env) or 'byok' (uses user provided custom_api_key)",
    )
    custom_api_key = Column(
        String(512),
        nullable=True,
        doc="User provided API key for BYOK mode. Never exposed to the frontend.",
    )
    custom_base_url = Column(
        String(256),
        nullable=True,
        doc="Optional custom base URL (e.g. for self-hosted Ollama or custom gateway)",
    )
    selected_model = Column(
        String(64),
        nullable=True,
        doc="Currently selected model identifier for this provider",
    )
    is_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this provider is enabled for generation and fallback",
    )
    priority_order = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Priority rank for automatic fallback (lower number = higher priority)",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this provider is currently selected as the primary provider",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of last configuration update",
    )

    def __repr__(self) -> str:
        return (
            f"<ProviderConfigModel(provider_id='{self.provider_id}', mode='{self.mode}', "
            f"model='{self.selected_model}', priority={self.priority_order}, is_active={self.is_active})>"
        )

