"""
Integration tests for DocMind AI Backend document upload, listing, deletion,
and SQLite metadata persistence (Sprint 4.2).
"""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import (
    get_app_settings,
    get_database_session,
    get_embedding_model,
    get_vector_store,
)
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import ChatHistoryModel, DocumentModel
from backend.app.main import app
from src.vectorstore import VectorStore


# ---------------------------------------------------------------------------
# Test Fixtures: Isolated SQLite DB and VectorStore
# ---------------------------------------------------------------------------


class MockEmbedder:
    """Mock embedder returning fixed-dimension unit vectors for fast testing."""

    EMBEDDING_DIM = 384

    def embed_texts(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        n = len(texts)
        if n == 0:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)
        vectors = np.ones((n, self.EMBEDDING_DIM), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms


@pytest.fixture
def test_env():
    """
    Creates an isolated temporary test directory with its own SQLite database,
    uploads directory, and vector store storage directory.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="docmind_test_"))
    upload_dir = temp_dir / "uploads"
    store_dir = temp_dir / "store"
    db_file = temp_dir / "test_docmind.db"

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

    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_app_settings] = override_get_settings
    app.dependency_overrides[get_vector_store] = override_get_vector_store
    app.dependency_overrides[get_embedding_model] = override_get_embedder

    with TestClient(app) as client:
        yield {
            "client": client,
            "session_factory": TestingSessionLocal,
            "settings": test_settings,
            "vector_store": test_vector_store,
            "temp_dir": temp_dir,
        }

    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_upload_txt_file_success(test_env):
    """Verify uploading a valid .txt file processes text, chunks, embeds, and saves to DB."""
    client: TestClient = test_env["client"]
    session_factory = test_env["session_factory"]
    vector_store: VectorStore = test_env["vector_store"]
    settings: Settings = test_env["settings"]

    file_content = b"DocMind AI is an enterprise document intelligence and hybrid RAG system.\nIt delivers explainable and reliable AI generation."
    files = {"file": ("enterprise_overview.txt", io.BytesIO(file_content), "text/plain")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    doc = data["data"]
    assert doc["filename"] == "enterprise_overview.txt"
    assert doc["file_type"] == "txt"
    assert doc["file_size"] == len(file_content)
    assert doc["chunk_count"] > 0
    assert "id" in doc

    doc_id = doc["id"]

    # 1. Verify SQLite metadata persistence
    with session_factory() as db:
        db_doc = db.query(DocumentModel).filter_by(id=doc_id).first()
        assert db_doc is not None
        assert db_doc.filename == "enterprise_overview.txt"
        assert db_doc.chunk_count == doc["chunk_count"]
        assert db_doc.status == "indexed"

    # 2. Verify VectorStore contains the document chunks
    assert "enterprise_overview.txt" in vector_store.get_all_filenames()
    assert len(vector_store) == doc["chunk_count"]

    # 3. Verify disk persistence: physical file saved in upload_dir
    saved_file = settings.UPLOAD_DIR / "enterprise_overview.txt"
    assert saved_file.exists()
    assert saved_file.read_bytes() == file_content


def test_upload_markdown_file_success(test_env):
    """Verify uploading a markdown (.md) file succeeds and preserves structure."""
    client: TestClient = test_env["client"]

    md_content = b"# DocMind Guide\n\n## Section 1\nMarkdown documents provide hierarchical structure for RAG."
    files = {"file": ("guide.md", io.BytesIO(md_content), "text/markdown")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["filename"] == "guide.md"
    assert data["data"]["file_type"] == "md"
    assert data["data"]["chunk_count"] > 0


def test_upload_unsupported_extension_fails(test_env):
    """Verify uploading an unsupported file format returns 422 with standardized error envelope."""
    client: TestClient = test_env["client"]

    bad_content = b"binary content"
    files = {"file": ("malicious_executable.exe", io.BytesIO(bad_content), "application/octet-stream")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "validation_error"
    assert "Unsupported file type" in data["error"]["message"]


def test_upload_empty_file_fails(test_env):
    """Verify uploading an empty (0 byte) file returns validation error."""
    client: TestClient = test_env["client"]

    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "validation_error"
    assert "empty" in data["error"]["message"].lower()


def test_list_documents(test_env):
    """Verify GET /api/v1/documents returns all indexed document records."""
    client: TestClient = test_env["client"]

    # Upload two documents
    client.post(
        "/api/v1/upload",
        files={"file": ("doc_a.txt", io.BytesIO(b"Document A content for retrieval testing."), "text/plain")},
    )
    client.post(
        "/api/v1/upload",
        files={"file": ("doc_b.md", io.BytesIO(b"# Document B\nContent for second document."), "text/markdown")},
    )

    response = client.get("/api/v1/documents")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["total"] >= 2
    filenames = [d["filename"] for d in data["documents"]]
    assert "doc_a.txt" in filenames
    assert "doc_b.md" in filenames


def test_get_document_by_id(test_env):
    """Verify GET /api/v1/documents/{doc_id} retrieves a specific document record."""
    client: TestClient = test_env["client"]

    up_resp = client.post(
        "/api/v1/upload",
        files={"file": ("lookup.txt", io.BytesIO(b"Test lookup content by UUID."), "text/plain")},
    )
    doc_id = up_resp.json()["data"]["id"]

    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == doc_id
    assert data["data"]["filename"] == "lookup.txt"


def test_get_document_by_id_not_found(test_env):
    """Verify GET /api/v1/documents/{non_existent} returns 404."""
    client: TestClient = test_env["client"]

    response = client.get(f"/api/v1/documents/{uuid.uuid4().hex}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "resource_not_found"


def test_delete_document_success(test_env):
    """
    Verify DELETE /api/v1/documents/{doc_id}:
      1. Removes metadata from SQLite.
      2. Invokes delete_by_filename in VectorStore.
      3. Deletes uploaded file from disk.
    """
    client: TestClient = test_env["client"]
    session_factory = test_env["session_factory"]
    vector_store: VectorStore = test_env["vector_store"]
    settings: Settings = test_env["settings"]

    # Upload document
    up_resp = client.post(
        "/api/v1/upload",
        files={"file": ("to_delete.txt", io.BytesIO(b"Content that will be deleted from the system."), "text/plain")},
    )
    doc_id = up_resp.json()["data"]["id"]
    file_on_disk = settings.UPLOAD_DIR / "to_delete.txt"

    assert file_on_disk.exists()
    assert "to_delete.txt" in vector_store.get_all_filenames()

    # Execute deletion
    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200

    del_data = del_resp.json()
    assert del_data["success"] is True
    assert del_data["data"]["id"] == doc_id
    assert del_data["data"]["filename"] == "to_delete.txt"
    assert del_data["data"]["removed_chunks"] > 0

    # 1. Verify removed from SQLite
    with session_factory() as db:
        assert db.query(DocumentModel).filter_by(id=doc_id).first() is None

    # 2. Verify removed from VectorStore
    assert "to_delete.txt" not in vector_store.get_all_filenames()

    # 3. Verify deleted from disk
    assert not file_on_disk.exists()


def test_delete_document_not_found(test_env):
    """Verify DELETE /api/v1/documents/{non_existent} returns 404."""
    client: TestClient = test_env["client"]

    response = client.delete(f"/api/v1/documents/{uuid.uuid4().hex}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "resource_not_found"


def test_chat_history_table_model(test_env):
    """Verify chat_history table in SQLite correctly stores conversational interaction metadata."""
    session_factory = test_env["session_factory"]

    with session_factory() as db:
        chat_entry = ChatHistoryModel(
            session_id="session_abc_123",
            query="What is DocMind AI?",
            answer="DocMind AI is an enterprise document intelligence and hybrid RAG system.",
            retrieved_sources='[{"filename": "doc_a.txt", "chunk_index": 0, "score": 0.92}]',
            confidence_score=0.89,
            latency_ms=142.5,
        )
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)

        assert chat_entry.id is not None

        # Query back
        fetched = db.query(ChatHistoryModel).filter_by(session_id="session_abc_123").first()
        assert fetched is not None
        assert fetched.query == "What is DocMind AI?"
        assert fetched.confidence_score == 0.89
        assert fetched.latency_ms == 142.5


def test_reupload_same_filename_replaces(test_env):
    """Verify re-uploading the same filename updates the SQLite entry and replaces vector chunks."""
    client: TestClient = test_env["client"]
    session_factory = test_env["session_factory"]
    vector_store: VectorStore = test_env["vector_store"]

    # Initial upload
    resp1 = client.post(
        "/api/v1/upload",
        files={"file": ("reupload.txt", io.BytesIO(b"Version 1 of the document with initial text."), "text/plain")},
    )
    doc_id_1 = resp1.json()["data"]["id"]

    # Re-upload same filename with new content
    resp2 = client.post(
        "/api/v1/upload",
        files={"file": ("reupload.txt", io.BytesIO(b"Version 2 updated content replacing previous version."), "text/plain")},
    )
    assert resp2.status_code == 201
    doc_id_2 = resp2.json()["data"]["id"]

    assert doc_id_1 == doc_id_2

    # Verify single record in SQLite
    with session_factory() as db:
        docs = db.query(DocumentModel).filter_by(filename="reupload.txt").all()
        assert len(docs) == 1

    # Verify VectorStore contains reupload.txt once
    filenames = vector_store.get_all_filenames()
    assert filenames.count("reupload.txt") == 1
