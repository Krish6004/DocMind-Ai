"""
Unit, Latency, Fallback, and Integration Tests for Adaptive Hybrid Retrieval Planner (Sprint 4.4).
"""

from __future__ import annotations

import time
from backend.app.services.retrieval_planner import RetrievalPlan, RetrievalPlanner


def test_planner_fact_lookup():
    """Verify Fact Lookup classification and parameters (top_k=5, rerank=3)."""
    planner = RetrievalPlanner()
    for q in ["What is CNN?", "Who invented Python?", "Define gradient descent."]:
        plan = planner.plan(q)
        assert plan.query_type == "fact_lookup"
        assert plan.strategy_name == "fact_lookup_search"
        assert plan.recommended_top_k == 5
        assert plan.recommended_rerank_count == 3
        assert plan.needs_memory is False
        assert plan.needs_metadata_filter is False
        assert plan.reason
        assert plan.decision_time_ms < 2.0


def test_planner_summary():
    """Verify Summary classification and parameters (top_k=12, rerank=6)."""
    planner = RetrievalPlanner()
    for q in ["Summarize this document.", "Give key points.", "TLDR"]:
        plan = planner.plan(q)
        assert plan.query_type == "summary"
        assert plan.strategy_name == "summary_search"
        assert plan.recommended_top_k == 12
        assert plan.recommended_rerank_count == 6
        assert plan.needs_memory is False
        assert plan.decision_time_ms < 2.0


def test_planner_comparison():
    """Verify Comparison classification and parameters (top_k=10, rerank=5)."""
    planner = RetrievalPlanner()
    for q in ["Difference between CNN and RNN", "Compare Random Forest and XGBoost"]:
        plan = planner.plan(q)
        assert plan.query_type == "comparison"
        assert plan.strategy_name == "comparison_search"
        assert plan.recommended_top_k == 10
        assert plan.recommended_rerank_count == 5
        assert plan.needs_memory is False
        assert plan.decision_time_ms < 2.0


def test_planner_list():
    """Verify List classification and parameters (top_k=15, rerank=7)."""
    planner = RetrievalPlanner()
    for q in ["List all advantages", "What are the limitations?", "Mention every dataset"]:
        plan = planner.plan(q)
        assert plan.query_type == "list"
        assert plan.strategy_name == "list_search"
        assert plan.recommended_top_k == 15
        assert plan.recommended_rerank_count == 7
        assert plan.needs_memory is False
        assert plan.decision_time_ms < 2.0


def test_planner_follow_up():
    """Verify Follow-up classification enables memory and reuses rewritten query."""
    planner = RetrievalPlanner()

    # Case 1: QueryRewriter flagged is_rewritten=True
    plan1 = planner.plan(
        query="Explain Perceptron.",
        original_query="Explain it",
        is_rewritten=True,
        has_history=True,
    )
    assert plan1.query_type == "follow_up"
    assert plan1.strategy_name == "follow_up_search"
    assert plan1.needs_memory is True
    assert plan1.decision_time_ms < 2.0

    # Case 2: Follow-up with history and unresolved phrasing
    for orig in ["Explain it", "What about disadvantages?", "Compare with SVM"]:
        plan2 = planner.plan(
            query=orig,
            original_query=orig,
            is_rewritten=False,
            has_history=True,
        )
        assert plan2.query_type == "follow_up"
        assert plan2.needs_memory is True


def test_planner_code():
    """Verify Code classification activates metadata/code chunk prioritization."""
    planner = RetrievalPlanner()
    for q in ["Show code", "Implementation", "Python example"]:
        plan = planner.plan(q)
        assert plan.query_type == "code"
        assert plan.strategy_name == "code_search"
        assert plan.needs_metadata_filter is True
        assert plan.decision_time_ms < 2.0


def test_planner_multi_document():
    """Verify Multi-document classification triggers on multi-file phrasing or >=2 filenames."""
    planner = RetrievalPlanner()

    plan1 = planner.plan("Summarize across all uploaded documents")
    assert plan1.query_type == "multi_document"
    assert plan1.strategy_name == "multi_document_search"
    assert plan1.recommended_top_k == 15
    assert plan1.recommended_rerank_count == 7

    plan2 = planner.plan(
        "Compare findings in notes.pdf and architecture.md",
        available_filenames=["notes.pdf", "architecture.md", "other.txt"],
    )
    assert plan2.query_type == "multi_document"
    assert plan2.strategy_name == "multi_document_search"


def test_planner_latency_under_2ms():
    """Verify planner consistently runs strictly under 2 ms per decision."""
    planner = RetrievalPlanner()
    queries = [
        "What is CNN?",
        "Summarize this document.",
        "Difference between CNN and RNN",
        "List all advantages",
        "Show Python code implementation",
        "Compare across all uploaded documents",
    ]
    for q in queries:
        t0 = time.perf_counter()
        plan = planner.plan(q)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 2.0, f"Planner took {elapsed_ms:.3f}ms for '{q}'"
        assert plan.decision_time_ms < 2.0


def test_planner_fallback_and_disabled():
    """Verify planner gracefully falls back to fact_lookup on internal error or when disabled."""
    # Disabled
    disabled_planner = RetrievalPlanner(enabled=False)
    plan_disabled = disabled_planner.plan("Summarize this document.")
    assert plan_disabled.query_type == "fact_lookup"
    assert plan_disabled.recommended_top_k == 5
    assert plan_disabled.recommended_rerank_count == 3

    # Internal error simulation
    planner = RetrievalPlanner(enabled=True)

    def broken_multi(*args, **kwargs):
        raise RuntimeError("Simulated internal regex/metadata crash")

    planner._mentions_multiple_files = broken_multi  # type: ignore[method-assign]
    plan_fallback = planner.plan("What is CNN?", available_filenames=["a.pdf", "b.pdf"])
    assert isinstance(plan_fallback, RetrievalPlan)
    assert plan_fallback.query_type == "fact_lookup"
    assert plan_fallback.recommended_top_k == 5
    assert plan_fallback.recommended_rerank_count == 3
    assert plan_fallback.decision_time_ms < 2.0

