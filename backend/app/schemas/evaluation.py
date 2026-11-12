"""
Pydantic schemas and data contracts for DocMind AI Enterprise Evaluation &
Benchmarking APIs (Sprint 6.0).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CitationCheckItem(BaseModel):
    """Verification result for an individual [Source N] citation."""

    citation_num: int
    citation_exists: bool
    chunk_exists: bool
    filename: str | None = None
    page_number: int | str | None = None
    chunk_index: int | str | None = None
    chunk_text_matches: bool = False
    warning: str | None = None


class CitationVerificationResult(BaseModel):
    """Aggregate citation integrity audit (non-destructive, warnings only)."""

    total_citations: int = 0
    valid_citations: int = 0
    citation_score: float = 0.0
    items: list[CitationCheckItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetrievalMetricsDetail(BaseModel):
    """Information retrieval quality metrics."""

    precision_at_k: float = Field(..., description="Precision@K in [0.0, 1.0]")
    recall_at_k: float = Field(..., description="Recall@K in [0.0, 1.0]")
    mrr: float = Field(..., description="Mean Reciprocal Rank in [0.0, 1.0]")
    dcg: float = Field(..., description="Discounted Cumulative Gain")
    idcg: float = Field(..., description="Ideal Discounted Cumulative Gain")
    ndcg: float = Field(..., description="Normalized DCG in [0.0, 1.0]")
    context_recall: float = Field(..., description="Context Recall in [0.0, 100.0]")
    retrieval_coverage: float = Field(..., description="Corpus Document Coverage in [0.0, 100.0]")
    source_diversity: int = Field(..., description="Count of unique documents contributing")


class GenerationMetricsDetail(BaseModel):
    """Normalized answer generation quality scores (0 -> 100)."""

    grounding_score: float = Field(..., description="Grounding score (0-100)")
    faithfulness: float = Field(..., description="Faithfulness score (0-100)")
    citation_coverage: float = Field(..., description="Citation coverage (0-100)")
    context_utilization: float = Field(..., description="Context utilization (0-100)")
    answer_completeness: float = Field(..., description="Answer completeness (0-100)")
    hallucination_risk: float = Field(..., description="Hallucination risk (0-100, lower is better)")
    source_utilization: float = Field(..., description="Source utilization (0-100)")
    answer_length: int = Field(..., description="Word count of generated answer")
    reasoning_coverage: float = Field(..., description="Reasoning coverage (0-100)")


class PerformanceMetricsDetail(BaseModel):
    """End-to-end latency and token usage telemetry."""

    query_rewrite_latency_ms: float = 0.0
    planner_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    confidence_latency_ms: float = 0.0
    memory_retrieval_time_ms: float = 0.0
    evaluation_latency_ms: float = 0.0
    total_response_time_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retrieved_chunk_count: int = 0
    reranked_chunk_count: int = 0
    document_count: int = 0
    provider: str = "unknown"
    model: str = "unknown"


class EvaluationRecord(BaseModel):
    """Complete evaluation report for a single RAG response or benchmark item."""

    id: str
    request_id: str
    session_id: str
    query: str
    answer: str | None = None
    provider: str
    model: str
    confidence: float
    overall_score: float
    retrieval: RetrievalMetricsDetail
    generation: GenerationMetricsDetail
    citation_verification: CitationVerificationResult
    performance: PerformanceMetricsDetail
    is_benchmark: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationHistoryListResponse(BaseModel):
    """Paginated/capped evaluation history list."""

    total: int
    items: list[EvaluationRecord] = Field(default_factory=list)


class ProviderComparisonEntry(BaseModel):
    """Aggregated performance & quality metrics per LLM provider."""

    provider: str
    total_runs: int
    avg_overall_score: float
    avg_grounding: float
    avg_faithfulness: float
    avg_hallucination_risk: float
    avg_latency_ms: float
    avg_tokens: float


class EvaluationSummaryResponse(BaseModel):
    """Aggregated telemetry summary powering the Evaluation Dashboard."""

    total_evaluations: int = 0
    overall_rag_score: float = 0.0
    avg_grounding: float = 0.0
    avg_retrieval_score: float = 0.0
    avg_generation_score: float = 0.0
    avg_hallucination_risk: float = 0.0
    avg_precision: float = 0.0
    avg_recall: float = 0.0
    avg_mrr: float = 0.0
    avg_ndcg: float = 0.0
    avg_context_recall: float = 0.0
    avg_retrieval_coverage: float = 0.0
    avg_source_diversity: float = 0.0
    avg_faithfulness: float = 0.0
    avg_citation_coverage: float = 0.0
    avg_context_utilization: float = 0.0
    avg_answer_completeness: float = 0.0
    avg_source_utilization: float = 0.0
    avg_reasoning_coverage: float = 0.0
    avg_confidence: float = 0.0
    avg_total_latency_ms: float = 0.0
    avg_rewrite_latency_ms: float = 0.0
    avg_planner_latency_ms: float = 0.0
    avg_retrieval_latency_ms: float = 0.0
    avg_reranking_latency_ms: float = 0.0
    avg_generation_latency_ms: float = 0.0
    total_tokens: int = 0
    avg_tokens_per_query: float = 0.0
    provider_comparison: list[ProviderComparisonEntry] = Field(default_factory=list)
    trend_series: list[dict[str, Any]] = Field(default_factory=list)
    heatmap_matrix: list[dict[str, Any]] = Field(default_factory=list)


class BenchmarkRunRequest(BaseModel):
    """Request payload for POST /api/v1/evaluation/run."""

    dataset_name: str = Field(
        default="sample_questions.json",
        description="Dataset filename under evaluation/datasets/",
    )
    max_queries: int = Field(
        default=55,
        ge=1,
        le=200,
        description="Maximum number of benchmark queries to run",
    )
    use_live_llm: bool = Field(
        default=False,
        description="If True, executes full LLM generation for each benchmark query; otherwise evaluates live Hybrid Retrieval + Cross-Encoder against ground truth with deterministic reference synthesis.",
    )


class BenchmarkRunResponse(BaseModel):
    """Aggregated results from running an automated benchmark suite."""

    run_id: str
    dataset_name: str
    total_queries: int
    avg_precision: float
    avg_recall: float
    avg_mrr: float
    avg_ndcg: float
    avg_grounding: float
    avg_faithfulness: float
    avg_hallucination: float
    avg_latency_ms: float
    avg_confidence: float
    document_coverage: float
    provider_comparison: list[ProviderComparisonEntry] = Field(default_factory=list)
    executed_at: datetime
    sample_results: list[EvaluationRecord] = Field(default_factory=list)

