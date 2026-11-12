"""
Integration tests for DocMind AI Backend Chat & RAG API (Sprint 4.3).
"""

from __future__ import annotations

import io
import shutil
import tempfile
import uuid
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
    get_provider_manager,
    get_reranker,
    get_vector_store,
)
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import ChatHistoryModel, DocumentModel
from backend.app.main import app
from src.vectorstore import VectorStore


# ---------------------------------------------------------------------------
# Mock AI Engine Components for Fast, Deterministic Integration Testing
# ---------------------------------------------------------------------------


class MockEmbedder:
    """Mock embedder returning fixed-dimension unit vectors."""

    EMBEDDING_DIM = 384

    def embed_texts(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        n = len(texts)
        if n == 0:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)
        # Deterministic vector based on string lengths
        vectors = np.ones((n, self.EMBEDDING_DIM), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


class MockReranker:
    """Mock cross-encoder reranker adding synthetic rerank_score logits."""

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int | None = None,
        batch_size: int = 16,
    ) -> list[dict[str, Any]]:
        k = top_k or len(documents)
        out = []
        for i, doc in enumerate(documents[:k]):
            d = dict(doc)
            # Assign descending positive logits for testing
            d["rerank_score"] = round(2.5 - (i * 0.5), 4)
            out.append(d)
        return out


class MockGenerator:
    """Mock LLM generator implementing generate(), _call_api(), and _extract_sources()."""

    SYSTEM_PROMPT = "You are a precise question-answering assistant."
    model = "mock-docmind-model"

    def __init__(self) -> None:
        self.call_history: list[list[dict[str, str]]] = []

    def generate(self, query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        sources = self._extract_sources(chunks)
        if not chunks:
            answer = "I don't have enough information in the provided documents to answer this question."
        else:
            answer = f"According to [Source 1], DocMind AI provides explainable hybrid retrieval for: '{query}'."
        return {
            "answer": answer,
            "sources": sources,
            "prompt_tokens": 120,
            "completion_tokens": 35,
            "model": self.model,
        }

    def _call_api(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        self.call_history.append(messages)
        # Check if conversation history is in messages
        has_history = any(m.get("role") == "assistant" for m in messages)
        last_user_msg = messages[-1]["content"] if messages else ""

        if has_history:
            answer = f"Continuing our discussion grounded in [Source 1]: relevant answer to '{last_user_msg.split('Question: ')[-1]}'."
        else:
            answer = "Grounded response: DocMind AI combines dense embeddings, BM25 sparse index, and cross-encoders [Source 1]."

        return {
            "choices": [{"message": {"role": "assistant", "content": answer}}],
            "usage": {"prompt_tokens": 180, "completion_tokens": 42},
            "model": self.model,
        }

    @staticmethod
    def _extract_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sources = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata", {})
            sources.append(
                {
                    "source_num": i,
                    "filename": meta.get("filename", "unknown.txt"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "score": round(float(chunk.get("rerank_score", chunk.get("score", 0.8))), 4),
                }
            )
        return sources


# ---------------------------------------------------------------------------
# Test Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def chat_test_env():
    """
    Creates an isolated test environment with SQLite, populated VectorStore,
    and mock AI components.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="docmind_chat_test_"))
    upload_dir = temp_dir / "uploads"
    store_dir = temp_dir / "store"
    db_file = temp_dir / "test_docmind_chat.db"

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

    test_vector_store = VectorStore()
    test_embedder = MockEmbedder()
    test_reranker = MockReranker()
    test_generator = MockGenerator()

    # Pre-populate VectorStore with two sample documents
    doc1_text = "DocMind AI uses hybrid retrieval combining dense all-MiniLM embeddings and BM25 sparse indices."
    doc2_text = "DocMind AI cross-encoder reranker evaluates token interactions using ms-marco-MiniLM."

    embs = test_embedder.embed_texts([doc1_text, doc2_text])
    test_vector_store.add(
        embs,
        [doc1_text, doc2_text],
        [
            {"filename": "doc1.txt", "source": "doc1.txt", "chunk_index": 0, "file_type": "txt", "file_size": 100},
            {"filename": "doc2.md", "source": "doc2.md", "chunk_index": 0, "file_type": "md", "file_size": 120},
        ],
    )

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_settings() -> Settings:
        return test_settings

    def override_get_vector_store() -> VectorStore:
        return test_vector_store

    def override_get_embedder() -> MockEmbedder:
        return test_embedder

    def override_get_reranker() -> MockReranker:
        return test_reranker

    def override_get_generator() -> MockGenerator:
        return test_generator

    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_app_settings] = override_get_settings
    app.dependency_overrides[get_vector_store] = override_get_vector_store
    app.dependency_overrides[get_embedding_model] = override_get_embedder
    app.dependency_overrides[get_reranker] = override_get_reranker
    app.dependency_overrides[get_generator] = override_get_generator

    with TestClient(app) as client:
        yield {
            "client": client,
            "session_factory": TestingSessionLocal,
            "settings": test_settings,
            "vector_store": test_vector_store,
            "generator": test_generator,
            "temp_dir": temp_dir,
        }

    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_chat_endpoint_basic_query(chat_test_env):
    """Verify POST /api/v1/chat executes hybrid retrieval, reranking, generation, and returns schema."""
    client: TestClient = chat_test_env["client"]
    session_factory = chat_test_env["session_factory"]

    payload = {
        "query": "How does DocMind AI combine dense and sparse retrieval?",
        "session_id": "session_test_01",
        "top_k": 3,
        "use_memory": False,
    }

    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    res = data["data"]

    # 1. Verify required top-level fields
    assert "request_id" in res
    uuid.UUID(res["request_id"])  # must be a valid UUID
    assert res["session_id"] == "session_test_01"
    assert res["query"] == payload["query"]
    assert len(res["answer"]) > 0

    # 2. Verify sources
    assert isinstance(res["sources"], list)
    assert len(res["sources"]) > 0
    src = res["sources"][0]
    assert "source_num" in src
    assert "filename" in src
    assert "score" in src
    assert "text" in src

    # 3. Verify confidence
    conf = res["confidence"]
    assert 0.0 <= conf["score"] <= 1.0
    assert conf["level"] in ["High", "Medium", "Low"]
    assert "explanation" in conf

    # 4. Verify latency metrics
    metrics = res["metrics"]
    assert metrics["retrieval_latency_ms"] >= 0.0
    assert metrics["reranking_latency_ms"] >= 0.0
    assert metrics["generation_latency_ms"] >= 0.0
    assert metrics["total_latency_ms"] >= 0.0
    assert metrics["retrieved_chunk_count"] > 0
    assert metrics["reranked_chunk_count"] > 0

    # 5. Verify SQLite persistence in chat_history table
    with session_factory() as db:
        record = db.query(ChatHistoryModel).filter_by(id=res["request_id"]).first()
        assert record is not None
        assert record.session_id == "session_test_01"
        assert record.query == payload["query"]
        assert record.answer == res["answer"]
        assert record.confidence_score == conf["score"]


def test_chat_endpoint_empty_query_validation(chat_test_env):
    """Verify empty or whitespace-only queries return 422 validation error."""
    client: TestClient = chat_test_env["client"]

    # 1. Empty string
    resp1 = client.post("/api/v1/chat", json={"query": ""})
    assert resp1.status_code == 422
    data1 = resp1.json()
    assert data1["success"] is False
    assert data1["error"]["type"] == "validation_error"

    # 2. Whitespace string
    resp2 = client.post("/api/v1/chat", json={"query": "   \n\t  "})
    assert resp2.status_code == 422
    data2 = resp2.json()
    assert data2["success"] is False
    assert data2["error"]["type"] == "validation_error"


def test_chat_endpoint_conversation_memory(chat_test_env):
    """
    Verify multi-turn conversation memory:
      Turn 1 is stored in SQLite.
      Turn 2 fetches Turn 1 and provides conversational continuity.
      GET /api/v1/chat/history/{session_id} returns all turns in chronological order.
    """
    client: TestClient = chat_test_env["client"]
    generator: MockGenerator = chat_test_env["generator"]
    session_id = f"mem_session_{uuid.uuid4().hex[:8]}"

    # Turn 1
    resp1 = client.post(
        "/api/v1/chat",
        json={
            "query": "Tell me about DocMind embeddings.",
            "session_id": session_id,
            "use_memory": True,
            "memory_window": 3,
        },
    )
    assert resp1.status_code == 200
    turn1_id = resp1.json()["data"]["request_id"]

    # Turn 2 (with memory enabled)
    resp2 = client.post(
        "/api/v1/chat",
        json={
            "query": "What reranker does it use?",
            "session_id": session_id,
            "use_memory": True,
            "memory_window": 3,
        },
    )
    assert resp2.status_code == 200
    turn2_id = resp2.json()["data"]["request_id"]
    assert turn1_id != turn2_id

    # Verify generator received previous conversation memory
    assert len(generator.call_history) > 0
    last_messages = generator.call_history[-1]
    roles = [m["role"] for m in last_messages]
    assert "system" in roles
    assert "user" in roles
    assert "assistant" in roles  # from previous turn!

    # Verify GET /api/v1/chat/history/{session_id}
    hist_resp = client.get(f"/api/v1/chat/history/{session_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["success"] is True
    history_obj = hist_data["data"]
    assert history_obj["session_id"] == session_id
    assert history_obj["total_turns"] == 2
    assert history_obj["history"][0]["id"] == turn1_id
    assert history_obj["history"][1]["id"] == turn2_id


def test_chat_endpoint_with_metadata_filters(chat_test_env):
    """Verify passing metadata filters restricts candidate chunks accordingly."""
    client: TestClient = chat_test_env["client"]

    # Query with file_type filter = "md"
    payload = {
        "query": "Explain cross-encoders in DocMind",
        "top_k": 5,
        "filters": {"file_type": "md"},
    }

    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    sources = response.json()["data"]["sources"]

    assert len(sources) > 0
    for s in sources:
        assert s["filename"] == "doc2.md"


def test_chat_endpoint_no_relevant_documents(chat_test_env):
    """Verify querying an empty vectorstore returns low confidence and informative fallback."""
    client: TestClient = chat_test_env["client"]
    vector_store: VectorStore = chat_test_env["vector_store"]

    # Clear all documents
    vector_store.delete_by_filename("doc1.txt")
    vector_store.delete_by_filename("doc2.md")
    assert len(vector_store) == 0

    response = client.post(
        "/api/v1/chat",
        json={"query": "What is the secret formula?"},
    )
    assert response.status_code == 200
    res = response.json()["data"]

    assert res["sources"] == []
    assert res["confidence"]["score"] == 0.0
    assert res["confidence"]["level"] == "Low"
    assert "information" in res["answer"].lower()


def test_chat_endpoint_generator_fallback(chat_test_env):
    """Verify that when generator is None, pipeline still retrieves and reports context."""
    client: TestClient = chat_test_env["client"]

    # Temporarily override generator and provider manager to None
    app.dependency_overrides[get_generator] = lambda: None
    app.dependency_overrides[get_provider_manager] = lambda: None

    response = client.post(
        "/api/v1/chat",
        json={"query": "How does DocMind retrieval work?"},
    )
    assert response.status_code == 200
    res = response.json()["data"]

    assert len(res["sources"]) > 0
    assert "GROQ_API_KEY" in res["answer"]
    assert res["confidence"]["score"] > 0.0


def test_chat_request_id_uniqueness(chat_test_env):
    """Verify every chat request generates a unique UUID request_id."""
    client: TestClient = chat_test_env["client"]

    id_set = set()
    for _ in range(5):
        resp = client.post("/api/v1/chat", json={"query": "test query"})
        assert resp.status_code == 200
        req_id = resp.json()["data"]["request_id"]
        assert req_id not in id_set
        id_set.add(req_id)
    assert len(id_set) == 5


def test_chat_endpoint_query_rewrite_telemetry(chat_test_env):
    """Verify that query rewrite telemetry is populated in chat endpoint response."""
    client: TestClient = chat_test_env["client"]

    # 1. First turn: Establish context topic
    session_id = "test_rewrite_session_1"
    resp1 = client.post(
        "/api/v1/chat",
        json={"query": "What is Decision Trees?", "session_id": session_id},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]
    assert "query_rewrite" in data1
    assert data1["query_rewrite"]["is_rewritten"] is False
    assert data1["query_rewrite"]["status"] == "skipped"

    # 2. Follow-up turn: Incomplete aspect question
    resp2 = client.post(
        "/api/v1/chat",
        json={"query": "Advantages?", "session_id": session_id},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert "query_rewrite" in data2
    qr = data2["query_rewrite"]
    assert qr["is_rewritten"] is True
    assert qr["status"] == "rewritten"
    assert qr["original_query"] == "Advantages?"
    assert "advantages of Decision Trees" in qr["rewritten_query"]
    assert qr["rewrite_time_ms"] < 50.0


def test_chat_endpoint_retrieval_planner_telemetry(chat_test_env):
    """Verify Adaptive Retrieval Planner telemetry and orchestration on /api/v1/chat."""
    client: TestClient = chat_test_env["client"]

    # 1. Comparison query
    resp_comp = client.post(
        "/api/v1/chat",
        json={"query": "Compare dense retrieval and BM25 in DocMind AI", "use_memory": False},
    )
    assert resp_comp.status_code == 200
    data_comp = resp_comp.json()["data"]
    assert "retrieval_planner" in data_comp
    rp = data_comp["retrieval_planner"]
    assert rp["query_type"] == "comparison"
    assert rp["strategy_name"] == "comparison_search"
    assert rp["recommended_top_k"] == 10
    assert rp["recommended_rerank_count"] == 5
    assert rp["decision_time_ms"] < 2.0

    # 2. Multi-document query
    resp_multi = client.post(
        "/api/v1/chat",
        json={"query": "Compare across all uploaded documents", "use_memory": False},
    )
    assert resp_multi.status_code == 200
    rp_multi = resp_multi.json()["data"]["retrieval_planner"]
    assert rp_multi["query_type"] == "multi_document"
    assert rp_multi["strategy_name"] == "multi_document_search"
    assert rp_multi["recommended_top_k"] == 15
    assert rp_multi["recommended_rerank_count"] == 7


