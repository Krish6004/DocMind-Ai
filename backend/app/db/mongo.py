"""
MongoDB Atlas client and collection manager for DocMind AI v2.0 (Sprint 7.0).

Hybrid Storage Architecture:
  - MongoDB Atlas stores ONLY: users, chat_sessions, user_settings, refresh_tokens.
  - SQLite & NumPy VectorStore remain locked for documents, chunks, embeddings,
    BM25 indices, and retrieval metadata.
"""

from __future__ import annotations

from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class MongoManager:
    """
    Manages the PyMongo client connection to MongoDB Atlas and ensures
    collection indexes for users, chat_sessions, user_settings, and refresh_tokens.
    """

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self._db: Database | None = None
        self._indexes_initialized = False

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            if not self.settings.MONGODB_URI:
                raise RuntimeError("MONGODB_URI is not configured in environment.")
            self._client = MongoClient(
                self.settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
        return self._client

    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = self.client[self.settings.MONGODB_DB_NAME]
        if not self._indexes_initialized:
            self.ensure_indexes()
        return self._db

    @property
    def users(self) -> Collection:
        return self.db["users"]

    @property
    def chat_sessions(self) -> Collection:
        return self.db["chat_sessions"]

    @property
    def user_settings(self) -> Collection:
        return self.db["user_settings"]

    @property
    def refresh_tokens(self) -> Collection:
        return self.db["refresh_tokens"]

    def ensure_indexes(self) -> None:
        """Create required unique & query-performance indexes idempotently."""
        if self._indexes_initialized:
            return
        try:
            db = self.client[self.settings.MONGODB_DB_NAME]
            db["users"].create_index([("email", ASCENDING)], unique=True)
            db["chat_sessions"].create_index(
                [("user_id", ASCENDING), ("conversation_id", ASCENDING)],
                unique=True,
            )
            db["chat_sessions"].create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
            db["user_settings"].create_index([("user_id", ASCENDING)], unique=True)
            db["refresh_tokens"].create_index([("jti", ASCENDING)], unique=True)
            db["refresh_tokens"].create_index([("user_id", ASCENDING)])
            self._indexes_initialized = True
            logger.info("MongoDB Atlas indexes verified for database '%s'.", self.settings.MONGODB_DB_NAME)
        except Exception as exc:
            logger.warning("Could not initialize MongoDB indexes yet: %s", exc)

    def ping(self) -> bool:
        """Verify MongoDB Atlas connectivity."""
        self.client.admin.command("ping")
        return True
