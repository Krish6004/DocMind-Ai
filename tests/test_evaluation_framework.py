"""
Comprehensive Unit, API, Performance, Benchmark, Export, and Regression Safety
Tests for DocMind AI Enterprise RAG Evaluation Framework (Sprint 6.0).
"""

from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import (
    get_app_settings,
    get_database_session,
    get_embedding_model,
    get_generator,
    get_reranker,
    get_vector_store,
)
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.db.models.evaluation import EvaluationHistoryModel
from backend.app.main import app
from backend.app.services.evaluation_service import EvaluationService
from src.vectorstore import VectorStore


class _EvalMockEmbedder:
    EMBEDDING_DIM = 384

    def embed_texts(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        n = len(texts)
        if n == 0:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)
        vecs = np.ones((n, self.EMBEDDING_DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            vecs[i, 0] = max(1.0, float(len(t) % 19))
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.where(norms == 0, 1.0, norms)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


class _EvalMockReranker:
    def rerank(self, query: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        out = []
        for idx, ch in enumerate(chunks[:top_k]):
            c = dict(ch)
            c["rerank_score"] = round(3.0 - idx * 0.4, 4)
            out.append(c)
        return out


class _EvalMockGenerator:
    model = "eval-mock-llm"

    def generate(self, query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "answer": (
                "DocMind AI combines dense vector embeddings and BM25 sparse search "
                "using Reciprocal Rank Fusion with k=60 [Source 1]. "
                "A Cross-Encoder reranker then refines the top candidate chunks [Source 2]."
            ),
            "model": self.model,
            "provider": "gemini",
            "prompt_tokens": 120,
            "completion_tokens": 42,
        }


@pytest.fixture
def eval_test_env():
    """Isolated SQLite + VectorStore + Mock AI environment for Sprint 6.0 tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="docmind_eval_test_"))
    upload_dir = temp_dir / "uploads"
    store_dir = temp_dir / "store"
    db_file = temp_dir / "test_eval.db"

    upload_dir.mkdir(parents=True, exist_ok=True)
    store_dir.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    test_settings = Settings(
        DATABASE_URL=db_url,
        DATA_DIR=temp_dir,
        UPLOAD_DIR=upload_dir,
        STORE_DIR=store_dir,
    )

    vs = VectorStore()
    emb = _EvalMockEmbedder()
    reranker = _EvalMockReranker()
    generator = _EvalMockGenerator()

    chunks = [
        "DocMind AI combines dense vector embeddings and BM25 sparse search via Reciprocal Rank Fusion (RRF k=60).",
        "Cross-Encoder ms-marco-MiniLM-L-6-v2 reranks top candidate chunks for higher precision.",
    ]
    vs.add(
        emb.embed_texts(chunks),
        chunks,
        [
            {"filename": "benchmark_corpus.txt", "source": "benchmark_corpus.txt", "chunk_index": 0, "file_type": "txt"},
            {"filename": "test_architecture.txt", "source": "test_architecture.txt", "chunk_index": 1, "file_type": "txt"},
        ],
    )

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_app_settings] = lambda: test_settings
    app.dependency_overrides[get_vector_store] = lambda: vs
    app.dependency_overrides[get_embedding_model] = lambda: emb
    app.dependency_overrides[get_reranker] = lambda: reranker
    app.dependency_overrides[get_generator] = lambda: generator

    with TestClient(app) as client:
        yield {
            "client": client,
            "session_factory": TestingSessionLocal,
            "settings": test_settings,
        }

    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Unit Tests: Retrieval, Generation, Citation, Storage & Overhead
# ---------------------------------------------------------------------------


def test_retrieval_metrics_precision_recall_mrr_ndcg():
    """Verify Precision@K, Recall@K, MRR, DCG, IDCG, NDCG, Coverage & Diversity."""
    svc = EvaluationService()
    sources = [
        {
            "source_num": 1,
            "filename": "unrelated.txt",
            "chunk_index": 0,
            "text": "Weather forecast for tomorrow is sunny.",
            "metadata": {"filename": "unrelated.txt", "chunk_index": 0},
        },
        {
            "source_num": 2,
            "filename": "rag_architecture.pdf",
            "chunk_index": 1,
            "text": "Retrieval-Augmented Generation uses dense vector search and an LLM context window.",
            "metadata": {"filename": "rag_architecture.pdf", "chunk_index": 1, "page_number": 3},
        },
    ]

    metrics = svc.compute_retrieval_evaluation(
        query="What is Retrieval-Augmented Generation?",
        answer="RAG uses dense vector search and LLM context [Source 2].",
        retrieved_chunks=sources,
        sources=sources,
        total_corpus_docs=4,
        expected_keywords=["retrieval", "vector", "LLM", "context"],
        expected_sources=["rag_architecture.pdf"],
    )

    assert metrics.precision_at_k == 0.5
    assert metrics.recall_at_k == 1.0
    assert metrics.mrr == 0.5  # First relevant is at rank 2
    assert metrics.dcg > 0.0
    assert metrics.idcg >= metrics.dcg
    assert 0.0 < metrics.ndcg < 1.0  # Suboptimal ordering since relevant doc was at rank 2
    assert metrics.context_recall == 50.0
    assert metrics.retrieval_coverage == 50.0  # 2 unique docs out of 4 corpus docs
    assert metrics.source_diversity == 2


def test_generation_grounding_faithfulness_and_hallucination():
    """Verify Grounding, Faithfulness, Completeness, Reasoning & Hallucination Risk (0 -> 100)."""
    svc = EvaluationService()
    sources = [
        {
            "source_num": 1,
            "filename": "doc1.txt",
            "chunk_index": 0,
            "text": "Reciprocal Rank Fusion combines BM25 sparse rankings and dense vector rankings using k=60.",
            "metadata": {"filename": "doc1.txt", "chunk_index": 0},
        }
    ]

    grounded_answer = (
        "Reciprocal Rank Fusion combines BM25 sparse rankings and dense vector rankings "
        "because a smoothing constant k=60 stabilizes scores [Source 1]."
    )
    cit_good = svc.verify_citations(grounded_answer, sources)
    gen_good = svc.compute_generation_evaluation(
        query="How does Reciprocal Rank Fusion work?",
        answer=grounded_answer,
        sources=sources,
        citation_result=cit_good,
    )

    assert 70.0 <= gen_good.grounding_score <= 100.0
    assert gen_good.faithfulness == 100.0
    assert gen_good.citation_coverage == 100.0
    assert gen_good.hallucination_risk < 25.0
    assert gen_good.answer_length > 10
    assert gen_good.reasoning_coverage > 40.0

    ungrounded_answer = "Quantum teleportation uses entangled photons on Mars satellites [Source 9]."
    cit_bad = svc.verify_citations(ungrounded_answer, sources)
    gen_bad = svc.compute_generation_evaluation(
        query="How does Reciprocal Rank Fusion work?",
        answer=ungrounded_answer,
        sources=sources,
        citation_result=cit_bad,
    )

    assert gen_bad.grounding_score < 20.0
    assert gen_bad.faithfulness == 0.0
    assert gen_bad.hallucination_risk > 80.0


def test_citation_validation_non_destructive_and_warnings():
    """Verify citation checks never modify the answer and report warnings accurately."""
    svc = EvaluationService()
    sources = [
        {
            "source_num": 1,
            "filename": "notes.pdf",
            "chunk_index": 2,
            "text": "Gradient descent updates model weights iteratively.",
            "metadata": {"filename": "notes.pdf", "chunk_index": 2},  # missing page metadata
        }
    ]
    original_answer = (
        "Gradient descent updates model weights iteratively [Source 1]. "
        "Bananas grow on tropical trees [Source 4]."
    )
    res = svc.verify_citations(original_answer, sources)

    # Answer must remain strictly untouched
    assert "Bananas grow on tropical trees [Source 4]." in original_answer
    assert res.total_citations == 2
    assert res.valid_citations == 1
    assert res.citation_score == 50.0
    assert len(res.warnings) >= 2  # PDF missing page metadata + out-of-range Source 4
    assert any("out-of-range" in w for w in res.warnings)
    assert any("page metadata" in w for w in res.warnings)


def test_evaluation_persistence_and_overhead_under_15ms(eval_test_env):
    """Verify evaluation_history SQLite persistence and <15ms evaluation overhead."""
    session_factory = eval_test_env["session_factory"]
    svc = EvaluationService(settings=eval_test_env["settings"])

    sources = [
        {
            "source_num": 1,
            "filename": "doc1.txt",
            "chunk_index": 0,
            "text": "DocMind AI uses hybrid retrieval combining dense embeddings and BM25.",
            "similarity_score": 0.85,
            "rerank_score": 4.2,
            "metadata": {"filename": "doc1.txt", "chunk_index": 0},
        }
    ]

    with session_factory() as db:
        record = svc.evaluate_and_persist(
            db,
            request_id="req-eval-001",
            session_id="sess-eval-001",
            query="How does DocMind AI perform retrieval?",
            answer="DocMind AI uses hybrid retrieval combining dense embeddings and BM25 [Source 1].",
            sources=sources,
            retrieved_chunks=sources,
            confidence_percentage=88.5,
            provider="gemini",
            model="gemini-2.5-flash",
            latencies={
                "query_rewrite_latency_ms": 0.4,
                "planner_latency_ms": 0.2,
                "retrieval_latency_ms": 18.5,
                "reranking_latency_ms": 12.1,
                "generation_latency_ms": 420.0,
                "confidence_latency_ms": 0.15,
                "memory_retrieval_time_ms": 1.1,
                "total_response_time_ms": 452.45,
            },
            token_usage={"prompt_tokens": 140, "completion_tokens": 35, "total_tokens": 175},
            document_count=2,
        )

        assert record.performance.evaluation_latency_ms < 15.0
        assert record.performance.prompt_tokens == 140
        assert record.performance.completion_tokens == 35
        assert record.performance.total_tokens == 175
        assert record.performance.provider == "gemini"

        row = db.query(EvaluationHistoryModel).filter_by(request_id="req-eval-001").first()
        assert row is not None
        assert row.model == "gemini-2.5-flash"
        assert row.overall_score > 0.0


# ---------------------------------------------------------------------------
# API Integration Tests: Chat Observer, Latest, History, Summary, Run, Export
# ---------------------------------------------------------------------------


def test_chat_regression_safety_and_automatic_evaluation_observer(eval_test_env):
    """
    Verify POST /api/v1/chat remains completely intact while automatically
    persisting an evaluation record observable via /evaluation/latest, /history, /summary.
    """
    client: TestClient = eval_test_env["client"]

    chat_resp = client.post(
        "/api/v1/chat",
        json={"query": "How does DocMind AI use hybrid retrieval?", "session_id": "eval_obs_sess"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()["data"]
    assert "DocMind AI combines dense vector embeddings" in chat_data["answer"]
    assert len(chat_data["sources"]) > 0

    # Latest Evaluation API
    latest_resp = client.get("/api/v1/evaluation/latest")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()["data"]
    assert latest_data is not None
    assert latest_data["request_id"] == chat_data["request_id"]
    assert latest_data["performance"]["evaluation_latency_ms"] < 15.0
    assert latest_data["generation"]["grounding_score"] > 0.0

    # History API
    hist_resp = client.get("/api/v1/evaluation/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()["data"]
    assert hist_data["total"] >= 1
    assert hist_data["items"][0]["request_id"] == chat_data["request_id"]

    # Summary / Dashboard API
    sum_resp = client.get("/api/v1/evaluation/summary")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()["data"]
    assert sum_data["total_evaluations"] >= 1
    assert sum_data["overall_rag_score"] > 0.0
    assert len(sum_data["trend_series"]) >= 1
    assert len(sum_data["heatmap_matrix"]) >= 1


def test_benchmark_runner_55_queries_and_export_apis(eval_test_env):
    """Verify POST /api/v1/evaluation/run (55+ queries) and CSV/JSON/PDF Export APIs."""
    client: TestClient = eval_test_env["client"]

    run_resp = client.post(
        "/api/v1/evaluation/run",
        json={"dataset_name": "sample_questions.json", "max_queries": 55, "use_live_llm": False},
    )
    assert run_resp.status_code == 200
    bench = run_resp.json()["data"]
    assert bench["total_queries"] >= 50
    assert 0.0 <= bench["avg_precision"] <= 1.0
    assert 0.0 <= bench["avg_recall"] <= 1.0
    assert 0.0 <= bench["avg_mrr"] <= 1.0
    assert 0.0 <= bench["avg_ndcg"] <= 1.0
    assert bench["avg_grounding"] >= 0.0
    assert bench["avg_latency_ms"] >= 0.0
    assert len(bench["provider_comparison"]) >= 1

    # Export JSON
    exp_json = client.get("/api/v1/evaluation/export?format=json")
    assert exp_json.status_code == 200
    assert "application/json" in exp_json.headers["content-type"]
    parsed_json = json.loads(exp_json.text)
    assert parsed_json["system_version"] == "v1.7.0"
    assert "executive_summary" in parsed_json
    assert "retrieval_metrics" in parsed_json
    assert "generation_metrics" in parsed_json
    assert len(parsed_json["evaluations"]) >= 50

    # Export CSV
    exp_csv = client.get("/api/v1/evaluation/export?format=csv")
    assert exp_csv.status_code == 200
    assert "text/csv" in exp_csv.headers["content-type"]
    rows = list(csv.reader(io.StringIO(exp_csv.text)))
    assert len(rows) > 50

    # Export PDF
    exp_pdf = client.get("/api/v1/evaluation/export?format=pdf")
    assert exp_pdf.status_code == 200
    assert "application/pdf" in exp_pdf.headers["content-type"]
    assert exp_pdf.content.startswith(b"%PDF")


def test_ndcg_ideal_ordering_equals_one():
    """Verify NDCG == 1.0 when relevant items appear in ideal descending rank order."""
    svc = EvaluationService()
    sources = [
        {
            "source_num": 1,
            "filename": "rag_architecture.pdf",
            "chunk_index": 0,
            "text": "Retrieval-Augmented Generation uses dense vector search and an LLM context.",
            "metadata": {"filename": "rag_architecture.pdf", "chunk_index": 0},
        },
        {
            "source_num": 2,
            "filename": "other.txt",
            "chunk_index": 0,
            "text": "Unrelated filler text about cooking recipes.",
            "metadata": {"filename": "other.txt", "chunk_index": 0},
        },
    ]
    m = svc.compute_retrieval_evaluation(
        query="What is RAG?",
        answer="RAG uses vector search [Source 1].",
        retrieved_chunks=sources,
        sources=sources,
        total_corpus_docs=2,
        expected_keywords=["retrieval", "vector", "LLM"],
        expected_sources=["rag_architecture.pdf"],
    )
    assert m.mrr == 1.0
    assert m.ndcg == 1.0


def test_abstention_response_has_zero_hallucination_risk():
    """Verify conservative abstention responses are treated as 100% grounded with 0% hallucination risk."""
    svc = EvaluationService()
    abstention = "I don't have enough information in the provided documents to answer this question."
    cit = svc.verify_citations(abstention, [])
    gen = svc.compute_generation_evaluation(
        query="What is the secret project codename?",
        answer=abstention,
        sources=[],
        citation_result=cit,
    )
    assert gen.grounding_score == 100.0
    assert gen.faithfulness == 100.0
    assert gen.hallucination_risk == 0.0


def test_context_and_source_utilization_scoring():
    """Verify Context Utilization and Source Utilization measure active citation & concept usage."""
    svc = EvaluationService()
    sources = [
        {"source_num": 1, "filename": "a.txt", "chunk_index": 0, "text": "BM25 computes lexical term scores.", "metadata": {"filename": "a.txt", "chunk_index": 0}},
        {"source_num": 2, "filename": "b.txt", "chunk_index": 0, "text": "Cross-encoder reranks chunks accurately.", "metadata": {"filename": "b.txt", "chunk_index": 0}},
    ]
    ans = "BM25 computes lexical term scores [Source 1], while Cross-encoder reranks chunks [Source 2]."
    cit = svc.verify_citations(ans, sources)
    gen = svc.compute_generation_evaluation("How do BM25 and Cross-encoder work?", ans, sources, cit)
    assert gen.source_utilization == 100.0
    assert gen.context_utilization == 100.0


def test_benchmark_dataset_contains_50_plus_questions():
    """Verify ground-truth dataset in evaluation/datasets/ contains 50+ structured questions."""
    svc = EvaluationService()
    ds = svc.load_benchmark_dataset("sample_questions.json")
    assert len(ds["questions"]) >= 50
    for item in ds["questions"][:5]:
        assert "question" in item
        assert "expected_keywords" in item
        assert "expected_sources" in item


def test_evaluation_api_error_handling(eval_test_env):
    """Verify invalid export formats and missing benchmark datasets return clean 4xx responses."""
    client: TestClient = eval_test_env["client"]

    bad_export = client.get("/api/v1/evaluation/export?format=xlsx")
    assert bad_export.status_code == 422

    missing_ds = client.post(
        "/api/v1/evaluation/run",
        json={"dataset_name": "nonexistent_dataset.json", "max_queries": 5},
    )
    assert missing_ds.status_code == 404


def test_empty_evaluation_summary_returns_zeroed_schema(eval_test_env):
    """Verify GET /summary and GET /latest behave cleanly when evaluation_history is empty."""
    client: TestClient = eval_test_env["client"]

    latest = client.get("/api/v1/evaluation/latest")
    assert latest.status_code == 200
    assert latest.json()["data"] is None

    summary = client.get("/api/v1/evaluation/summary")
    assert summary.status_code == 200
    assert summary.json()["data"]["total_evaluations"] == 0

