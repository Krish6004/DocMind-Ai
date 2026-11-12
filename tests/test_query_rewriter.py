"""
Unit and performance tests for QueryRewriter service in DocMind AI.
"""

from __future__ import annotations

import time
from backend.app.services.query_rewriter import QueryRewriter, QueryRewriteResult


def test_no_rewrite_needed():
    """Verify that standalone, unambiguous queries without context are returned unchanged."""
    rewriter = QueryRewriter(enabled=True)

    # 1. Standard question without history
    res = rewriter.rewrite("What is machine learning?", history=[])
    assert res.is_rewritten is False
    assert res.status == "skipped"
    assert res.rewritten_query == "What is machine learning?"

    # 2. Complete, self-contained question with history
    res2 = rewriter.rewrite("What is machine learning?", history=["Explain neural networks"])
    assert res2.is_rewritten is False
    assert res2.status == "skipped"
    assert res2.rewritten_query == "What is machine learning?"


def test_pronoun_resolution():
    """Verify resolving pronouns (it, this, that, they, its) to salient historical entities."""
    rewriter = QueryRewriter(enabled=True)

    # Example 1: "Explain it" -> "Explain Perceptron."
    res = rewriter.rewrite("Explain it", history=["What is Perceptron?"])
    assert res.is_rewritten is True
    assert res.status == "rewritten"
    assert res.rewritten_query == "Explain Perceptron."

    # Example 2: "Explain it simply" -> "Explain Perceptron simply."
    res = rewriter.rewrite("Explain it simply", history=["What is Perceptron?"])
    assert res.is_rewritten is True
    assert res.rewritten_query == "Explain Perceptron simply."

    # Example 3: "How does it work?" -> "How does Perceptron work?"
    res = rewriter.rewrite("How does it work?", history=["What is Perceptron?"])
    assert res.is_rewritten is True
    assert res.rewritten_query == "How does Perceptron work?"

    # Example 4: Possessive "What is its architecture?" -> "What is Transformer's architecture?"
    res = rewriter.rewrite("What is its architecture?", history=["Tell me about Transformer"])
    assert res.is_rewritten is True
    assert res.rewritten_query == "What is Transformer's architecture?"


def test_follow_up_questions():
    """Verify transforming follow-up questions and single-aspect fragments."""
    rewriter = QueryRewriter(enabled=True)

    # Example 1: "Advantages?" -> "What are the advantages of Decision Trees?"
    res = rewriter.rewrite("Advantages?", history=["What are Decision Trees?"])
    assert res.is_rewritten is True
    assert res.status == "rewritten"
    assert res.rewritten_query == "What are the advantages of Decision Trees?"

    # Example 2: "And disadvantages?" -> "What are the disadvantages of Neural Networks?"
    res = rewriter.rewrite("And disadvantages?", history=["Neural Networks"])
    assert res.is_rewritten is True
    assert res.status == "rewritten"
    assert res.rewritten_query == "What are the disadvantages of Neural Networks?"

    # Example 3: "Compare with SVM" -> "Compare Random Forest with SVM."
    res = rewriter.rewrite("Compare with SVM", history=["Random Forest"])
    assert res.is_rewritten is True
    assert res.status == "rewritten"
    assert res.rewritten_query == "Compare Random Forest with SVM."

    # Example 4: "And unsupervised?" -> "What is unsupervised learning?"
    res = rewriter.rewrite("And unsupervised?", history=["What about supervised learning?"])
    assert res.is_rewritten is True
    assert res.status == "rewritten"
    assert res.rewritten_query == "What is unsupervised learning?"

    # Example 5: Multi-turn chain (Turn 1: Machine Learning, Turn 2: Explain it simply, Turn 3: Advantages?)
    res_chain = rewriter.rewrite(
        "Advantages?",
        history=["What is Machine Learning?", "Explain it simply"],
    )
    assert res_chain.is_rewritten is True
    assert res_chain.rewritten_query == "What are the advantages of Machine Learning?"


def test_failure_fallback_never_raises():
    """Verify that any exception or corrupted history returns original query without raising."""
    rewriter = QueryRewriter(enabled=True)

    # Simulate unexpected input object in history
    corrupted_history = [object(), None, 12345]
    res = rewriter.rewrite("Explain it", history=corrupted_history)
    # Should safely return without exception
    assert res.original_query == "Explain it"
    assert res.rewritten_query == "Explain it"
    assert res.is_rewritten is False

    # Monkey patch extract_context to raise an exception
    def broken_extract(h):
        raise RuntimeError("Simulated internal exception")

    original_extract = rewriter.extract_context
    try:
        rewriter.extract_context = broken_extract
        res_fail = rewriter.rewrite("Explain it", history=["What is Perceptron?"])
        assert res_fail.status == "failed"
        assert res_fail.is_rewritten is False
        assert res_fail.rewritten_query == "Explain it"
    finally:
        rewriter.extract_context = original_extract


def test_performance_latency_under_50ms():
    """Verify that query rewrite execution takes well under 50 milliseconds."""
    rewriter = QueryRewriter(enabled=True)
    history = [
        "What is machine learning?",
        "Explain supervised learning algorithms in detail",
        "What are Decision Trees?",
    ]

    t0 = time.perf_counter()
    res = rewriter.rewrite("What are their limitations?", history=history)
    latency_ms = (time.perf_counter() - t0) * 1000

    assert latency_ms < 50.0, f"Latency {latency_ms:.2f}ms exceeded 50ms requirement"
    assert res.rewrite_time_ms < 50.0
    assert res.is_rewritten is True
    assert "Decision Trees" in res.rewritten_query


def test_disabled_query_rewriter():
    """Verify that when ENABLE_QUERY_REWRITE is false, system behaves exactly as before."""
    rewriter = QueryRewriter(enabled=False)
    res = rewriter.rewrite("Explain it", history=["What is Perceptron?"])
    assert res.status == "disabled"
    assert res.is_rewritten is False
    assert res.rewritten_query == "Explain it"
    assert res.rewrite_time_ms == 0.0
