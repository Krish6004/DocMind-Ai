"""
SQLAlchemy ORM model for persistent RAG evaluation history (Sprint 6.0).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from backend.app.db.base import Base


class EvaluationHistoryModel(Base):
    """
    SQLAlchemy model representing persisted evaluation metrics for each RAG
    query turn or benchmark evaluation run in the 'evaluation_history' table.
    """

    __tablename__ = "evaluation_history"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        index=True,
        doc="Unique primary key for the evaluation record",
    )
    request_id = Column(
        String(64),
        nullable=False,
        index=True,
        doc="Linked chat request UUID or benchmark item ID",
    )
    session_id = Column(
        String(64),
        nullable=False,
        default="default",
        index=True,
        doc="Conversation session ID or benchmark run ID",
    )
    query = Column(
        Text,
        nullable=False,
        doc="Evaluated user or benchmark query",
    )
    answer = Column(
        Text,
        nullable=True,
        doc="Generated LLM answer observed for evaluation",
    )
    provider = Column(
        String(64),
        nullable=False,
        default="unknown",
        doc="Active LLM provider used (e.g. gemini, groq)",
    )
    model = Column(
        String(128),
        nullable=False,
        default="unknown",
        doc="LLM model identifier used",
    )
    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
        doc="Retrieval confidence percentage (0.0 to 100.0)",
    )

    # Retrieval metrics
    precision = Column(Float, nullable=False, default=0.0, doc="Precision@K (0.0 to 1.0)")
    recall = Column(Float, nullable=False, default=0.0, doc="Recall@K (0.0 to 1.0)")
    mrr = Column(Float, nullable=False, default=0.0, doc="Mean Reciprocal Rank (0.0 to 1.0)")
    ndcg = Column(Float, nullable=False, default=0.0, doc="Normalized DCG (0.0 to 1.0)")
    dcg = Column(Float, nullable=False, default=0.0, doc="Discounted Cumulative Gain")
    idcg = Column(Float, nullable=False, default=0.0, doc="Ideal Discounted Cumulative Gain")
    context_recall = Column(Float, nullable=False, default=0.0, doc="Context Recall (0 to 100)")
    retrieval_coverage = Column(Float, nullable=False, default=0.0, doc="Document Coverage (0 to 100)")
    source_diversity = Column(Integer, nullable=False, default=0, doc="Unique documents used")

    # Generation metrics (0 -> 100)
    grounding = Column(Float, nullable=False, default=0.0, doc="Grounding score (0 to 100)")
    faithfulness = Column(Float, nullable=False, default=0.0, doc="Faithfulness score (0 to 100)")
    citation_score = Column(Float, nullable=False, default=0.0, doc="Citation integrity/coverage (0 to 100)")
    context_utilization = Column(Float, nullable=False, default=0.0, doc="Context utilization (0 to 100)")
    answer_completeness = Column(Float, nullable=False, default=0.0, doc="Answer completeness (0 to 100)")
    hallucination_score = Column(Float, nullable=False, default=0.0, doc="Hallucination risk score (0 to 100)")
    source_utilization = Column(Float, nullable=False, default=0.0, doc="Source utilization (0 to 100)")
    answer_length = Column(Integer, nullable=False, default=0, doc="Answer length in words")
    reasoning_coverage = Column(Float, nullable=False, default=0.0, doc="Reasoning coverage (0 to 100)")
    overall_score = Column(Float, nullable=False, default=0.0, doc="Composite Overall RAG Score (0 to 100)")

    # Structured JSON payloads
    citation_verification = Column(
        Text,
        nullable=True,
        doc="JSON-serialized citation verification items and warnings",
    )
    latencies = Column(
        Text,
        nullable=False,
        default="{}",
        doc="JSON-serialized latency breakdown across all pipeline stages",
    )
    token_usage = Column(
        Text,
        nullable=False,
        default="{}",
        doc="JSON-serialized prompt, completion, and total token counts",
    )
    document_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total indexed documents in corpus at evaluation time",
    )
    chunk_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Retrieved/reranked chunk count evaluated",
    )
    is_benchmark = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether record came from an automated benchmark run",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
        doc="UTC timestamp of evaluation",
    )

