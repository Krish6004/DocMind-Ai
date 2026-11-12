"""
Pydantic schemas and data contracts for DocMind AI Chat & RAG APIs (Sprint 4.3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """
    Input request schema for the /api/v1/chat endpoint.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user question or query to answer using the RAG pipeline.",
        examples=["What are the key findings in the annual report?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional conversation session ID for multi-turn history. If omitted, a new UUID is generated.",
        examples=["session_12345"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top candidate chunks to retrieve and rerank.",
        examples=[5],
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata filters (e.g. filename, file_type, upload_date).",
        examples=[{"file_type": "pdf"}],
    )
    use_memory: bool = Field(
        default=True,
        description="Whether to incorporate recent conversation turns from SQLite into the generation prompt.",
    )
    memory_window: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of previous conversation turns to fetch for conversational context.",
    )


class SourceChunk(BaseModel):
    """
    Attributed source document chunk used in retrieval and answer generation.
    """

    source_num: int = Field(..., description="1-based sequential source block number")
    filename: str = Field(..., description="Source document basename")
    chunk_index: Any = Field(..., description="Sequential chunk index within document")
    score: float = Field(..., description="Reranker cross-encoder or hybrid retrieval score")
    text: str | None = Field(default=None, description="Extracted text content of the chunk")
    metadata: dict[str, Any] | None = Field(default=None, description="Original chunk metadata")


class ConfidenceDetails(BaseModel):
    """
    Calibrated retrieval confidence details.
    """

    score: float = Field(..., description="Confidence score in range [0.0, 1.0]")
    percentage: float = Field(..., description="Confidence percentage [0.0, 100.0]")
    level: str = Field(..., description="Confidence tier: 'High', 'Medium', or 'Low'")
    color: str = Field(..., description="Hex color code associated with tier")
    explanation: str = Field(..., description="Human-readable mathematical explanation")
    details: dict[str, Any] | None = Field(default=None, description="Component score breakdowns")


class LatencyMetrics(BaseModel):
    """
    Telemetry latency breakdown for RAG pipeline stages.
    """

    retrieval_latency_ms: float = Field(..., description="Time taken for dense + sparse hybrid retrieval in ms")
    reranking_latency_ms: float = Field(..., description="Time taken for cross-encoder reranking in ms")
    generation_latency_ms: float = Field(..., description="Time taken for LLM answer generation in ms")
    total_latency_ms: float = Field(..., description="Total wall-clock response time in ms")
    retrieved_chunk_count: int = Field(..., description="Number of candidate chunks retrieved")
    reranked_chunk_count: int = Field(..., description="Number of top chunks passed to LLM")
    rewrite_latency_ms: float = Field(default=0.0, description="Time taken for query rewriting in ms")
    planner_latency_ms: float = Field(default=0.0, description="Time taken for adaptive retrieval planning in ms")


class QueryRewriteTelemetry(BaseModel):
    """
    Telemetry details for the query rewrite stage.
    """

    original_query: str = Field(..., description="Original user query")
    rewritten_query: str = Field(..., description="Optimized retrieval query")
    rewrite_time_ms: float = Field(..., description="Latency for rewriting in ms")
    status: str = Field(..., description="Rewrite status: 'rewritten', 'skipped', 'disabled', or 'failed'")
    is_rewritten: bool = Field(default=False, description="Whether query was altered")


class RetrievalPlannerTelemetry(BaseModel):
    """
    Telemetry details for the Adaptive Retrieval Planner stage.
    """

    query_type: str = Field(..., description="Detected query category (fact_lookup, summary, comparison, list, follow_up, code, multi_document)")
    strategy_name: str = Field(..., description="Selected retrieval orchestration strategy")
    recommended_top_k: int = Field(..., description="Planned candidate retrieval pool size")
    recommended_rerank_count: int = Field(..., description="Planned top chunks kept after reranking")
    needs_memory: bool = Field(..., description="Whether conversation memory should be activated")
    needs_metadata_filter: bool = Field(..., description="Whether metadata filtering/prioritization is requested")
    reason: str = Field(..., description="Explanation for the chosen retrieval strategy")
    decision_time_ms: float = Field(..., description="Planner decision latency in ms")


class ChatResponseData(BaseModel):
    """
    Structured response payload returned by POST /api/v1/chat.
    """

    request_id: str = Field(..., description="Unique UUID generated for this request")
    session_id: str = Field(..., description="Active session ID for the conversation")
    query: str = Field(..., description="The original user query")
    answer: str = Field(..., description="Grounded LLM-generated answer with citations")
    sources: list[SourceChunk] = Field(default_factory=list, description="List of attributed source chunks")
    confidence: ConfidenceDetails = Field(..., description="Calculated confidence metrics")
    metrics: LatencyMetrics = Field(..., description="Latency telemetry for the pipeline")
    query_rewrite: QueryRewriteTelemetry | None = Field(default=None, description="Query rewrite telemetry")
    retrieval_planner: RetrievalPlannerTelemetry | None = Field(default=None, description="Adaptive retrieval planner telemetry")
    model: str = Field(..., description="LLM model identifier used for generation")
    created_at: datetime = Field(..., description="UTC timestamp of the interaction")

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryTurn(BaseModel):
    """
    Schema for a single historical conversation turn.
    """

    id: str = Field(..., description="Unique UUID of the turn")
    session_id: str = Field(..., description="Conversation session ID")
    query: str = Field(..., description="User query prompt")
    answer: str = Field(..., description="LLM response")
    sources: list[dict[str, Any]] | None = Field(default=None, description="Serialized source citations")
    confidence_score: float | None = Field(default=None, description="Confidence score")
    latency_ms: float | None = Field(default=None, description="Total latency in ms")
    created_at: datetime = Field(..., description="UTC timestamp")

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """
    Schema for session history responses.
    """

    session_id: str = Field(..., description="Conversation session ID")
    total_turns: int = Field(..., description="Total count of turns in this session")
    history: list[ChatHistoryTurn] = Field(..., description="Chronological list of conversation turns")
