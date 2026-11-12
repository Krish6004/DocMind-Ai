"""
SQLAlchemy ORM model for chat history.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text

from backend.app.db.base import Base


class ChatHistoryModel(Base):
    """
    SQLAlchemy model representing conversational history and retrieval metadata.
    """

    __tablename__ = "chat_history"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        index=True,
        doc="Unique identifier for the chat turn",
    )
    user_id = Column(
        String(64),
        nullable=False,
        default="default",
        index=True,
        doc="Owner user ID for strict multi-user isolation",
    )
    session_id = Column(
        String(64),
        nullable=False,
        default="default",
        index=True,
        doc="Conversation session identifier for multi-turn chats",
    )
    query = Column(
        Text,
        nullable=False,
        doc="User query prompt",
    )
    answer = Column(
        Text,
        nullable=False,
        doc="LLM-generated answer grounded in retrieved chunks",
    )
    retrieved_sources = Column(
        Text,
        nullable=True,
        doc="JSON-serialized array of source chunk citations and scores",
    )
    confidence_score = Column(
        Float,
        nullable=True,
        doc="Calculated retrieval confidence score (0.0 to 1.0)",
    )
    latency_ms = Column(
        Float,
        nullable=True,
        doc="Total query-to-answer latency in milliseconds",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="UTC timestamp of interaction",
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "query": self.query,
            "answer": self.answer,
            "retrieved_sources": self.retrieved_sources,
            "confidence_score": self.confidence_score,
            "latency_ms": self.latency_ms,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return f"<ChatHistoryModel(id='{self.id}', session='{self.session_id}')>"
