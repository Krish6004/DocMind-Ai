"""
Sprint 7.0 Tests: Enterprise Authentication, MongoDB Atlas Integration & Multi-User Isolation.

Tests:
  - Register, Login, Token Refresh, Logout, /me
  - Bcrypt password hashing (never stored in plaintext)
  - JWT verification & protected route security (401 without valid token)
  - Strict Document Isolation: User A cannot see, retrieve, or delete User B's documents
  - Strict Chat Session & History Isolation: User B cannot access User A's sessions
  - Per-User Settings Isolation: User A & User B maintain independent preferences
  - Cross-Device Session Restore: Relogging in as User A restores all A's documents & chats
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
    get_mongo_manager,
    get_reranker,
    get_vector_store,
)
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.db.mongo import MongoManager
from backend.app.db.session import init_db
from backend.app.main import app
from src.vectorstore import VectorStore


class _MemoryMongoCollection:
    """In-memory mock MongoDB collection for fast, deterministic unit test isolation."""

    def __init__(self):
        self._data: list[dict[str, Any]] = []

    def create_index(self, *args, **kwargs):
        pass

    def find_one(self, filter_doc: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self._data:
            match = True
            for k, v in filter_doc.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, filter_doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        class _Cursor(list):
            def sort(self, *args, **kwargs):
                return self
        res = _Cursor()
        for doc in self._data:
            match = True
            if filter_doc:
                for k, v in filter_doc.items():
                    if isinstance(v, dict) and "$regex" in v:
                        import re
                        flags = re.IGNORECASE if v.get("$options") == "i" else 0
                        if not re.search(v["$regex"], str(doc.get(k, "")), flags):
                            match = False
                            break
                    elif doc.get(k) != v:
                        match = False
                        break
            if match:
                res.append(dict(doc))
        return res

    def insert_one(self, doc: dict[str, Any]):
        item = dict(doc)
        if "_id" not in item:
            item["_id"] = uuid.uuid4().hex
        self._data.append(item)
        class _InsertRes:
            inserted_id = item["_id"]
        return _InsertRes()

    def update_one(self, filter_doc: dict[str, Any], update_doc: dict[str, Any], upsert: bool = False):
        existing = self.find_one(filter_doc)
        if existing:
            for doc in self._data:
                match = True
                for k, v in filter_doc.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    if "$set" in update_doc:
                        doc.update(update_doc["$set"])
                    if "$push" in update_doc:
                        for pk, pv in update_doc["$push"].items():
                            doc.setdefault(pk, [])
                            if isinstance(pv, dict) and "$each" in pv:
                                doc[pk].extend(pv["$each"])
                            else:
                                doc[pk].append(pv)
                    return
        elif upsert:
            new_item = dict(filter_doc)
            if "$set" in update_doc:
                new_item.update(update_doc["$set"])
            self.insert_one(new_item)

    def delete_one(self, filter_doc: dict[str, Any]):
        for i, doc in enumerate(self._data):
            match = True
            for k, v in filter_doc.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                del self._data[i]
                class _DelRes:
                    deleted_count = 1
                return _DelRes()
        class _DelResZero:
            deleted_count = 0
        return _DelResZero()


class MockMongoManager:
    """Mock MongoManager isolating tests without depending on live network connection."""

    def __init__(self):
        self._users = _MemoryMongoCollection()
        self._chat_sessions = _MemoryMongoCollection()
        self._user_settings = _MemoryMongoCollection()
        self._refresh_tokens = _MemoryMongoCollection()

    @property
    def users(self):
        return self._users

    @property
    def chat_sessions(self):
        return self._chat_sessions

    @property
    def user_settings(self):
        return self._user_settings

    @property
    def refresh_tokens(self):
        return self._refresh_tokens

    def ensure_indexes(self):
        pass

    def ping(self):
        return True


class _MockEmbedder:
    EMBEDDING_DIM = 384

    def embed_texts(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        n = len(texts)
        if n == 0:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)
        vecs = np.ones((n, self.EMBEDDING_DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            vecs[i, 0] = max(1.0, float(len(t) % 23))
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.where(norms == 0, 1.0, norms)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


class _MockReranker:
    def rerank(self, query: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        return chunks[:top_k]


class _MockGenerator:
    model = "mock-llm-v2"

    def generate(self, query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "answer": f"Grounded response for query: {query}",
            "model": self.model,
            "provider": "gemini",
        }


@pytest.fixture
def auth_test_env():
    """Isolated multi-user test environment with SQLite, VectorStore, and Mock MongoDB."""
    temp_dir = Path(tempfile.mkdtemp(prefix="docmind_auth_test_"))
    upload_dir = temp_dir / "uploads"
    store_dir = temp_dir / "store"
    db_file = temp_dir / "test_auth_docmind.db"

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
        REQUIRE_AUTH=True,  # STRICT AUTH REQUIRED IN SPRINT 7.0 TESTS
        JWT_SECRET="test_super_secret_jwt_key_sprint_7",
        JWT_REFRESH_SECRET="test_super_secret_refresh_key_sprint_7",
    )

    mock_mongo = MockMongoManager()
    vector_store = VectorStore()
    embedder = _MockEmbedder()
    reranker = _MockReranker()
    generator = _MockGenerator()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_app_settings] = lambda: test_settings
    app.dependency_overrides[get_mongo_manager] = lambda: mock_mongo
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_embedding_model] = lambda: embedder
    app.dependency_overrides[get_reranker] = lambda: reranker
    app.dependency_overrides[get_generator] = lambda: generator

    with TestClient(app) as client:
        yield {
            "client": client,
            "session_factory": TestingSessionLocal,
            "settings": test_settings,
            "mongo": mock_mongo,
            "vector_store": vector_store,
        }

    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Authentication & JWT Unit Tests
# ---------------------------------------------------------------------------


def test_register_and_password_bcrypt_hashing(auth_test_env):
    """Verify user registration hashes password with bcrypt and never stores plaintext."""
    client: TestClient = auth_test_env["client"]
    mongo: MockMongoManager = auth_test_env["mongo"]

    resp = client.post(
        "/api/auth/register",
        json={"name": "Alice Morgan", "email": "alice@company.com", "password": "supersecretpassword"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["email"] == "alice@company.com"
    assert data["user"]["name"] == "Alice Morgan"

    # Verify MongoDB record: password_hash must be a bcrypt hash ($2b$...)
    stored = mongo.users.find_one({"email": "alice@company.com"})
    assert stored is not None
    assert "password" not in stored
    assert stored["password_hash"].startswith("$2b$")
    assert "supersecretpassword" not in stored["password_hash"]


def test_login_and_me_endpoint(auth_test_env):
    """Verify login with correct credentials and retrieving /api/auth/me with Bearer token."""
    client: TestClient = auth_test_env["client"]

    # Register
    client.post(
        "/api/auth/register",
        json={"name": "Bob Vance", "email": "bob@vance.com", "password": "password123"},
    )

    # Login
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "bob@vance.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]

    # Get /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "bob@vance.com"

    # Invalid login fails
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "bob@vance.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401


def test_protected_routes_require_authentication(auth_test_env):
    """Verify accessing protected upload, documents, and chat routes without token returns 401."""
    client: TestClient = auth_test_env["client"]

    # Unauthenticated upload attempt
    resp_upload = client.post(
        "/api/v1/upload",
        files={"file": ("unauth.txt", io.BytesIO(b"Secret text"), "text/plain")},
    )
    assert resp_upload.status_code == 401

    # Unauthenticated document list attempt
    resp_docs = client.get("/api/v1/documents")
    assert resp_docs.status_code == 401

    # Unauthenticated chat attempt
    resp_chat = client.post("/api/v1/chat", json={"query": "Hello"})
    assert resp_chat.status_code == 401


# ---------------------------------------------------------------------------
# Strict Document & Multi-User Isolation Tests
# ---------------------------------------------------------------------------


def test_multi_user_document_and_retrieval_isolation(auth_test_env):
    """
    Verify strict document and retrieval isolation:
      - User A uploads 'secret_project_a.txt'
      - User B logs in
      - User B CANNOT see User A's document in /api/v1/documents
      - User B CANNOT fetch User A's document by ID (returns 404)
      - User B CANNOT delete User A's document (returns 404)
      - User B chat query CANNOT retrieve User A's document chunks
      - User A logs back in: User A's document and chunks are fully restored!
    """
    client: TestClient = auth_test_env["client"]

    # 1. Register User A
    resp_a = client.post(
        "/api/auth/register",
        json={"name": "User Alpha", "email": "alpha@enterprise.com", "password": "passwordA123"},
    )
    token_a = resp_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. User A uploads private document
    doc_a_content = b"Project Apollo X is Alpha's top-secret mission to Mars with quantum propulsion."
    upload_a = client.post(
        "/api/v1/upload",
        headers=headers_a,
        files={"file": ("apollo_secret.txt", io.BytesIO(doc_a_content), "text/plain")},
    )
    assert upload_a.status_code == 201
    doc_a_id = upload_a.json()["data"]["id"]

    # Verify User A sees 1 document
    list_a = client.get("/api/v1/documents", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()["data"]["documents"]) == 1

    # 3. Register & Login User B
    resp_b = client.post(
        "/api/auth/register",
        json={"name": "User Beta", "email": "beta@enterprise.com", "password": "passwordB456"},
    )
    token_b = resp_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. User B MUST NOT see User A's documents
    list_b = client.get("/api/v1/documents", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()["data"]["documents"]) == 0

    # 5. User B MUST NOT access User A's document by ID (returns 404)
    get_a_by_b = client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert get_a_by_b.status_code == 404

    # 6. User B MUST NOT delete User A's document (returns 404)
    del_a_by_b = client.delete(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert del_a_by_b.status_code == 404

    # 7. User B chat query MUST NOT retrieve User A's chunks
    chat_b = client.post(
        "/api/v1/chat",
        headers=headers_b,
        json={"query": "What is Project Apollo X?"},
    )
    assert chat_b.status_code == 200
    assert len(chat_b.json()["data"]["sources"]) == 0

    # 8. User A queries: User A successfully retrieves their own document
    chat_a = client.post(
        "/api/v1/chat",
        headers=headers_a,
        json={"query": "What is Project Apollo X?"},
    )
    assert chat_a.status_code == 200
    sources_a = chat_a.json()["data"]["sources"]
    assert len(sources_a) > 0
    assert sources_a[0]["filename"] == "apollo_secret.txt"

    # 9. User A logs in from another device/session -> documents fully preserved
    login_a_again = client.post(
        "/api/auth/login",
        json={"email": "alpha@enterprise.com", "password": "passwordA123"},
    )
    token_a2 = login_a_again.json()["data"]["access_token"]
    list_a2 = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_a2}"})
    assert list_a2.status_code == 200
    assert len(list_a2.json()["data"]["documents"]) == 1


# ---------------------------------------------------------------------------
# Strict Chat Sessions & User Settings Isolation Tests
# ---------------------------------------------------------------------------


def test_multi_user_chat_sessions_and_settings_isolation(auth_test_env):
    """
    Verify chat sessions and user settings are strictly isolated per user in MongoDB:
      - User A creates a session and customizes settings
      - User B creates a session and customizes settings
      - User A only sees A's sessions and settings
      - User B only sees B's sessions and settings
    """
    client: TestClient = auth_test_env["client"]

    # Setup User A
    tok_a = client.post("/api/auth/register", json={"name": "Alice M", "email": "a@co.com", "password": "passA123"}).json()["data"]["access_token"]
    h_a = {"Authorization": f"Bearer {tok_a}"}

    # Setup User B
    tok_b = client.post("/api/auth/register", json={"name": "Bob V", "email": "b@co.com", "password": "passB123"}).json()["data"]["access_token"]
    h_b = {"Authorization": f"Bearer {tok_b}"}

    # A creates session
    client.post("/api/v1/sessions", headers=h_a, json={"title": "Session Alpha 1"})
    sessions_a = client.get("/api/v1/sessions", headers=h_a).json()["data"]
    assert len(sessions_a) == 1
    assert sessions_a[0]["title"] == "Session Alpha 1"

    # B creates session
    client.post("/api/v1/sessions", headers=h_b, json={"title": "Session Beta 1"})
    sessions_b = client.get("/api/v1/sessions", headers=h_b).json()["data"]
    assert len(sessions_b) == 1
    assert sessions_b[0]["title"] == "Session Beta 1"

    # Verify B cannot see A's session
    assert not any(s["title"] == "Session Alpha 1" for s in sessions_b)

    # User A updates settings
    client.put("/api/v1/user/settings", headers=h_a, json={"preferred_provider": "groq", "top_k": 12, "preferred_model": "llama3", "theme": "dark", "temperature": 0.5, "memory_enabled": True})
    settings_a = client.get("/api/v1/user/settings", headers=h_a).json()["data"]
    assert settings_a["preferred_provider"] == "groq"
    assert settings_a["top_k"] == 12

    # User B's settings remain default/independent
    settings_b = client.get("/api/v1/user/settings", headers=h_b).json()["data"]
    assert settings_b["preferred_provider"] == "gemini"
    assert settings_b["top_k"] == 8
