"""
Unit tests for Retrieval V2 features in src/retrieval_v2.py and HybridRetriever.

Tests:
  - Retrieval confidence computation & explanation
  - Metadata filtering (filename, file type, upload date, date range)
  - Chunk citation attribution & formatting-preserving highlighting
  - Retrieval metrics tracking
  - Recent queries management

Run with: pytest tests/test_retrieval_v2.py -v
"""

from unittest.mock import MagicMock
import pytest

from src.retrieval_v2 import (
    RetrievalMetrics,
    add_recent_query,
    compute_retrieval_confidence,
    filter_chunks_by_metadata,
    highlight_chunk_html,
    identify_used_chunks,
    matches_metadata_filter,
    sigmoid,
)
from src.retriever import HybridRetriever


# ---------------------------------------------------------------------------
# 1. Retrieval Confidence Tests
# ---------------------------------------------------------------------------


def test_sigmoid_numerical_stability():
    assert abs(sigmoid(0.0) - 0.5) < 1e-6
    assert sigmoid(100.0) == 1.0 or abs(sigmoid(100.0) - 1.0) < 1e-6
    assert sigmoid(-100.0) == 0.0 or abs(sigmoid(-100.0) - 0.0) < 1e-6
    assert 0.0 < sigmoid(2.5) < 1.0


def test_confidence_empty_chunks():
    result = compute_retrieval_confidence([])
    assert result["score"] == 0.0
    assert result["percentage"] == 0.0
    assert result["level"] == "Low"
    assert "No relevant document chunks" in result["explanation"]


def test_confidence_high_tier():
    # Reranker score +4.0 (sigmoid ~0.982), similarity 0.88 -> weighted average ~0.95
    chunks = [
        {
            "text": "sample text",
            "metadata": {"filename": "doc.pdf"},
            "rerank_score": 4.0,
            "similarity_score": 0.88,
        }
    ]
    res = compute_retrieval_confidence(chunks)
    assert res["level"] == "High"
    assert res["score"] >= 0.70
    assert res["color"] == "#22c55e"
    assert "Confidence is" in res["explanation"]
    assert "High" in res["explanation"]
    assert res["details"]["top_rerank_score"] == 4.0
    assert res["details"]["top_similarity_score"] == 0.88


def test_confidence_medium_tier():
    # Reranker score 0.0 (sigmoid 0.50), similarity 0.55 -> weighted ~0.515
    chunks = [
        {
            "text": "sample text",
            "metadata": {"filename": "notes.txt"},
            "rerank_score": 0.0,
            "similarity_score": 0.55,
        }
    ]
    res = compute_retrieval_confidence(chunks)
    assert res["level"] == "Medium"
    assert 0.40 <= res["score"] < 0.70
    assert res["color"] == "#eab308"


def test_confidence_low_tier():
    # Reranker score -5.0 (sigmoid ~0.006), similarity 0.10 -> weighted ~0.034
    chunks = [
        {
            "text": "sample text",
            "metadata": {"filename": "irrelevant.txt"},
            "rerank_score": -5.0,
            "similarity_score": 0.10,
        }
    ]
    res = compute_retrieval_confidence(chunks)
    assert res["level"] == "Low"
    assert res["score"] < 0.40
    assert res["color"] == "#ef4444"


def test_confidence_only_similarity():
    chunks = [
        {
            "text": "sample text",
            "metadata": {"filename": "data.md"},
            "similarity_score": 0.75,
        }
    ]
    res = compute_retrieval_confidence(chunks)
    assert res["level"] == "High"
    assert res["percentage"] == 75.0


def test_confidence_only_rerank():
    chunks = [
        {
            "text": "sample text",
            "metadata": {"filename": "data.md"},
            "rerank_score": 2.0,
        }
    ]
    res = compute_retrieval_confidence(chunks)
    expected_prob = sigmoid(2.0)
    assert abs(res["score"] - expected_prob) < 1e-4


# ---------------------------------------------------------------------------
# 2. Metadata Filtering Tests
# ---------------------------------------------------------------------------


def test_matches_filter_wildcard_and_empty():
    meta = {"filename": "report.pdf", "file_type": "pdf", "upload_timestamp": "2026-10-27T12:00:00Z"}
    assert matches_metadata_filter(meta, None) is True
    assert matches_metadata_filter(meta, {}) is True
    assert matches_metadata_filter(meta, {"filename": "All Documents", "file_type": "All Types"}) is True


def test_matches_filter_filename():
    meta = {"filename": "financial_report.pdf", "source": "/data/financial_report.pdf"}
    assert matches_metadata_filter(meta, {"filename": "financial_report.pdf"}) is True
    assert matches_metadata_filter(meta, {"filename": "other.pdf"}) is False


def test_matches_filter_file_type():
    meta_pdf = {"file_type": "pdf"}
    meta_docx = {"file_type": "docx"}
    assert matches_metadata_filter(meta_pdf, {"file_type": "pdf"}) is True
    assert matches_metadata_filter(meta_pdf, {"file_type": ".pdf"}) is True
    assert matches_metadata_filter(meta_docx, {"file_type": "pdf"}) is False


def test_matches_filter_date():
    meta = {"upload_timestamp": "2026-10-27T14:32:00.123456+00:00"}
    assert matches_metadata_filter(meta, {"uploaded_date": "2026-10-27"}) is True
    assert matches_metadata_filter(meta, {"uploaded_date": "2026-10-28"}) is False


def test_matches_filter_date_range():
    meta = {"upload_timestamp": "2026-10-15T10:00:00Z"}
    assert matches_metadata_filter(meta, {"date_from": "2026-10-01", "date_to": "2026-10-31"}) is True
    assert matches_metadata_filter(meta, {"date_from": "2026-10-20", "date_to": "2026-10-31"}) is False
    assert matches_metadata_filter(meta, {"date_from": "2026-10-01", "date_to": "2026-10-10"}) is False


def test_filter_chunks_by_metadata():
    chunks = [
        {"text": "c1", "metadata": {"filename": "doc1.pdf", "file_type": "pdf"}},
        {"text": "c2", "metadata": {"filename": "doc2.docx", "file_type": "docx"}},
        {"text": "c3", "metadata": {"filename": "doc3.pdf", "file_type": "pdf"}},
    ]
    pdf_only = filter_chunks_by_metadata(chunks, {"file_type": "pdf"})
    assert len(pdf_only) == 2
    assert pdf_only[0]["metadata"]["filename"] == "doc1.pdf"
    assert pdf_only[1]["metadata"]["filename"] == "doc3.pdf"


def test_hybrid_retriever_metadata_filter_integration():
    vs = MagicMock()
    vs.search.return_value = [
        {"text": "d1", "metadata": {"filename": "target.pdf"}, "score": 0.9, "index": 0},
        {"text": "d2", "metadata": {"filename": "other.txt"}, "score": 0.8, "index": 1},
    ]
    vs.get_by_index.side_effect = lambda i: {
        "text": f"doc_{i}",
        "metadata": {"filename": "target.pdf" if i == 0 else "other.txt"},
    }

    bm = MagicMock()
    bm.get_top_n.return_value = [
        {"text": "d1", "score": 0.9, "index": 0},
        {"text": "d2", "score": 0.7, "index": 1},
    ]

    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 384

    retriever = HybridRetriever(vectorstore=vs, bm25=bm, embedder=embedder)

    # Filter only target.pdf
    results = retriever.retrieve("query", top_k=5, metadata_filter={"filename": "target.pdf"})
    assert len(results) == 1
    assert results[0]["metadata"]["filename"] == "target.pdf"
    assert results[0]["similarity_score"] == 0.9


# ---------------------------------------------------------------------------
# 3. Chunk Highlighting & Citation Attribution Tests
# ---------------------------------------------------------------------------


def test_identify_used_chunks_explicit_citation():
    chunks = [
        {"text": "Antigravity AI is an advanced agentic coding assistant.", "metadata": {"chunk_index": 0}},
        {"text": "DocMind AI implements hybrid retrieval from scratch.", "metadata": {"chunk_index": 1}},
        {"text": "Unrelated passage about neural networks.", "metadata": {"chunk_index": 2}},
    ]
    answer = "According to [Source 2], DocMind AI implements hybrid retrieval from scratch."

    attributed = identify_used_chunks(answer, chunks)
    assert len(attributed) == 3
    assert attributed[0]["is_used"] is False
    assert attributed[1]["is_used"] is True
    assert attributed[1]["citation_number"] == 2
    assert attributed[2]["is_used"] is False
    assert "<mark" in attributed[1]["highlighted_html"]


def test_identify_used_chunks_multiple_citations():
    chunks = [
        {"text": "First chunk text.", "metadata": {"chunk_index": 0}},
        {"text": "Second chunk text.", "metadata": {"chunk_index": 1}},
        {"text": "Third chunk text.", "metadata": {"chunk_index": 2}},
    ]
    answer = "Based on [Source 1] and [Source 3], the answer is complete."
    attributed = identify_used_chunks(answer, chunks)
    assert attributed[0]["is_used"] is True
    assert attributed[1]["is_used"] is False
    assert attributed[2]["is_used"] is True


def test_identify_used_chunks_fallback_overlap():
    chunks = [
        {"text": "Apples, bananas, and oranges are fruits.", "metadata": {"chunk_index": 0}},
        {"text": "PyTorch is an open-source machine learning framework.", "metadata": {"chunk_index": 1}},
    ]
    # Answer has no [Source N] tag
    answer = "PyTorch is widely recognized as an open-source machine learning framework."
    attributed = identify_used_chunks(answer, chunks)
    # Chunk 1 should have highest overlap with PyTorch answer
    assert attributed[1]["is_used"] is True


def test_highlight_chunk_html_preserves_formatting():
    original_text = (
        "DocMind AI Features:\n"
        "    - Hybrid Retrieval (Dense + BM25)\n"
        "    - Cross-Encoder Reranking\n\n"
        "Section 2:\n"
        "All algorithms preserved without modification."
    )
    answer = "DocMind AI Features include Hybrid Retrieval and Cross-Encoder Reranking."

    highlighted = highlight_chunk_html(original_text, answer)

    # Must preserve newlines and indentation
    assert "\n    - " in highlighted
    assert "\n\nSection 2:\n" in highlighted
    # Must contain highlight tags
    assert '<mark class="docmind-highlight"' in highlighted
    # Stripping tags should match original text exactly
    import re

    stripped = re.sub(r"</?mark[^>]*>", "", highlighted)
    assert stripped == original_text


# ---------------------------------------------------------------------------
# 4. Retrieval Metrics Tests
# ---------------------------------------------------------------------------


def test_retrieval_metrics():
    metrics = RetrievalMetrics(
        retrieval_latency_ms=12.45,
        reranking_latency_ms=45.60,
        generation_latency_ms=310.20,
        total_latency_ms=368.25,
        retrieved_chunk_count=10,
        reranked_chunk_count=5,
    )
    d = metrics.to_dict()
    assert d["retrieval_latency_ms"] == 12.45
    assert d["reranking_latency_ms"] == 45.60
    assert d["generation_latency_ms"] == 310.20
    assert d["total_latency_ms"] == 368.25
    assert d["retrieved_chunk_count"] == 10
    assert d["reranked_chunk_count"] == 5


# ---------------------------------------------------------------------------
# 5. Recent Queries Tests
# ---------------------------------------------------------------------------


def test_add_recent_query():
    recent = ["Query 1", "Query 2", "Query 3"]

    # Add new query
    recent = add_recent_query(recent, "Query 4")
    assert recent[0] == "Query 4"
    assert len(recent) == 4

    # Add duplicate (case-insensitive) -> moves to front
    recent = add_recent_query(recent, "query 2")
    assert recent[0] == "query 2"
    assert recent.count("Query 2") == 0
    assert len(recent) == 4

    # Empty string should not be added
    recent = add_recent_query(recent, "   ")
    assert len(recent) == 4


def test_recent_query_cap_at_ten():
    recent = [f"Old Query {i}" for i in range(10)]
    recent = add_recent_query(recent, "Brand New Query", max_items=10)
    assert len(recent) == 10
    assert recent[0] == "Brand New Query"
    assert "Old Query 9" not in recent  # Oldest pruned
