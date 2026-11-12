"""
Dependency injection providers for DocMind AI Backend.

Provides cleanly decoupled dependencies for FastAPI endpoints:
  - Application configuration
  - Centralized logging
  - Database sessions (SQLite via SQLAlchemy)
  - Services (UploadService, DocumentService, ChatService)
  - AI Engine integration points (VectorStore, HybridRetriever, CrossEncoderReranker, LLMGenerator)
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.db.session import get_db

if TYPE_CHECKING:
    from backend.app.services.chat_service import ChatService
    from backend.app.services.document_service import DocumentService
    from backend.app.services.upload_service import UploadService
    from src.embeddings import EmbeddingModel
    from src.generator import LLMGenerator
    from src.reranker import CrossEncoderReranker
    from src.retriever import HybridRetriever
    from src.vectorstore import VectorStore

logger = get_logger(__name__)

# Module-level singletons for persistent in-memory components
_GLOBAL_VECTOR_STORE: VectorStore | None = None
_GLOBAL_EMBEDDER: Any | None = None
_GLOBAL_RERANKER: Any | None = None
_GLOBAL_PROVIDER_MANAGER: Any | None = None
_GLOBAL_QUERY_REWRITER: Any | None = None
_GLOBAL_RETRIEVAL_PLANNER: Any | None = None
_GLOBAL_EVALUATION_SERVICE: Any | None = None
_GLOBAL_MONGO_MANAGER: Any | None = None


# ---------------------------------------------------------------------------
# Configuration & Core Dependencies
# ---------------------------------------------------------------------------


def get_app_settings() -> Settings:
    """Provide application settings."""
    return get_settings()


def get_request_logger() -> logging.Logger:
    """Provide a request-scoped logger."""
    return get_logger("docmind.api")


# ---------------------------------------------------------------------------
# Database Session Dependency
# ---------------------------------------------------------------------------


def get_database_session() -> Generator[Session, None, None]:
    """Yield an active SQLAlchemy database session."""
    yield from get_db()


# ---------------------------------------------------------------------------
# AI Engine Singletons & Providers
# ---------------------------------------------------------------------------


def get_vector_store(
    settings: Settings = Depends(get_app_settings),
) -> VectorStore:
    """
    Dependency provider for VectorStore.
    Maintains a singleton VectorStore backed by NumPy/JSON on disk.
    """
    global _GLOBAL_VECTOR_STORE
    if _GLOBAL_VECTOR_STORE is None:
        from src.vectorstore import VectorStore

        _GLOBAL_VECTOR_STORE = VectorStore()
        store_path = settings.STORE_DIR / "vector_store"
        if (settings.STORE_DIR / "vector_store.json").exists() and (settings.STORE_DIR / "vector_store.npz").exists():
            try:
                _GLOBAL_VECTOR_STORE.load(str(store_path))
                logger.info("Loaded persisted VectorStore (%d chunks) from '%s'", len(_GLOBAL_VECTOR_STORE), store_path)
            except Exception as exc:
                logger.warning("Failed to load existing VectorStore from '%s': %s", store_path, exc)
    return _GLOBAL_VECTOR_STORE


def get_embedding_model() -> Any:
    """
    Dependency provider for sentence embedding model.
    Caches model weights in memory.
    """
    global _GLOBAL_EMBEDDER
    if _GLOBAL_EMBEDDER is None:
        from src.embeddings import EmbeddingModel

        _GLOBAL_EMBEDDER = EmbeddingModel()
    return _GLOBAL_EMBEDDER


def get_reranker() -> Any:
    """
    Dependency provider for CrossEncoderReranker.
    Caches cross-encoder model weights in memory.
    """
    global _GLOBAL_RERANKER
    if _GLOBAL_RERANKER is None:
        try:
            from src.reranker import CrossEncoderReranker

            _GLOBAL_RERANKER = CrossEncoderReranker()
        except Exception as exc:
            logger.warning("CrossEncoderReranker could not be loaded: %s", exc)
            return None
    return _GLOBAL_RERANKER


def get_retriever(
    settings: Settings = Depends(get_app_settings),
    vector_store: VectorStore = Depends(get_vector_store),
    embedder: Any = Depends(get_embedding_model),
) -> HybridRetriever:
    """
    Provide an active HybridRetriever combining VectorStore and BM25.
    Synchronizes BM25 with all current chunks in VectorStore.
    """
    from src.bm25 import BM25
    from src.retriever import HybridRetriever

    all_docs = vector_store.get_documents()
    bm25 = BM25()
    if all_docs:
        bm25.fit(all_docs)

    return HybridRetriever(
        vectorstore=vector_store,
        bm25=bm25,
        embedder=embedder,
    )


def get_generator(
    settings: Settings = Depends(get_app_settings),
) -> LLMGenerator | None:
    """
    Dependency provider for LLMGenerator.
    Configured from environment settings (Groq/OpenAI compatible).
    """
    if not settings.GROQ_API_KEY:
        return None

    try:
        from src.generator import LLMGenerator

        return LLMGenerator(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            model=settings.GROQ_MODEL,
        )
    except Exception as exc:
        logger.warning("LLMGenerator could not be loaded: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Business Service Providers
# ---------------------------------------------------------------------------


def get_document_service() -> DocumentService:
    """Provide DocumentService instance."""
    from backend.app.services.document_service import DocumentService

    return DocumentService()


def get_upload_service(
    settings: Settings = Depends(get_app_settings),
    vector_store: VectorStore = Depends(get_vector_store),
    embedding_model: Any = Depends(get_embedding_model),
) -> UploadService:
    """Provide UploadService instance configured with dependencies."""
    from backend.app.services.upload_service import UploadService

    return UploadService(
        settings=settings,
        vector_store=vector_store,
        embedding_model=embedding_model,
    )


def get_provider_manager(
    settings: Settings = Depends(get_app_settings),
) -> Any:
    """Provide singleton ProviderManager instance."""
    global _GLOBAL_PROVIDER_MANAGER
    if _GLOBAL_PROVIDER_MANAGER is None:
        from backend.app.services.llm.manager import ProviderManager

        _GLOBAL_PROVIDER_MANAGER = ProviderManager(settings=settings)
    return _GLOBAL_PROVIDER_MANAGER


def get_query_rewriter(
    settings: Settings = Depends(get_app_settings),
) -> Any:
    """Provide singleton QueryRewriter instance."""
    global _GLOBAL_QUERY_REWRITER
    if _GLOBAL_QUERY_REWRITER is None:
        from backend.app.services.query_rewriter import QueryRewriter

        _GLOBAL_QUERY_REWRITER = QueryRewriter(
            enabled=getattr(settings, "ENABLE_QUERY_REWRITE", True)
        )
    return _GLOBAL_QUERY_REWRITER


def get_retrieval_planner(
    settings: Settings = Depends(get_app_settings),
) -> Any:
    """Provide singleton RetrievalPlanner instance."""
    global _GLOBAL_RETRIEVAL_PLANNER
    if _GLOBAL_RETRIEVAL_PLANNER is None:
        from backend.app.services.retrieval_planner import RetrievalPlanner

        _GLOBAL_RETRIEVAL_PLANNER = RetrievalPlanner(
            enabled=getattr(settings, "ENABLE_RETRIEVAL_PLANNER", True)
        )
    return _GLOBAL_RETRIEVAL_PLANNER


def get_evaluation_service(
    settings: Settings = Depends(get_app_settings),
) -> Any:
    """Provide singleton EvaluationService instance."""
    global _GLOBAL_EVALUATION_SERVICE
    if _GLOBAL_EVALUATION_SERVICE is None:
        from backend.app.services.evaluation_service import EvaluationService

        _GLOBAL_EVALUATION_SERVICE = EvaluationService(settings=settings)
    return _GLOBAL_EVALUATION_SERVICE


def get_mongo_manager(
    settings: Settings = Depends(get_app_settings),
) -> Any:
    """Provide singleton MongoManager instance connected to MongoDB Atlas."""
    global _GLOBAL_MONGO_MANAGER
    if _GLOBAL_MONGO_MANAGER is None:
        from backend.app.db.mongo import MongoManager

        _GLOBAL_MONGO_MANAGER = MongoManager(settings=settings)
    return _GLOBAL_MONGO_MANAGER


def get_auth_service(
    settings: Settings = Depends(get_app_settings),
    mongo: Any = Depends(get_mongo_manager),
) -> Any:
    """Provide AuthService instance backed by MongoDB Atlas."""
    from backend.app.services.auth_service import AuthService

    return AuthService(mongo=mongo, settings=settings)


def get_current_user(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    auth_service: Any = Depends(get_auth_service),
) -> Any:
    """
    JWT verification dependency for protected routes.
    Reads Bearer token from Authorization header or 'access_token' HttpOnly cookie.
    """
    from backend.app.schemas.auth import UserOut

    token: str | None = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif request.cookies.get("access_token"):
        token = request.cookies.get("access_token")

    if not token:
        if not getattr(settings, "REQUIRE_AUTH", False) or getattr(settings, "ENVIRONMENT", "").lower() in ("test", "testing"):
            return UserOut(
                id="default",
                name="Default User",
                email="default@docmind.local",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = auth_service.verify_access_token(token)
    user_id = payload["sub"]
    user = auth_service.get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_id(
    current_user: Any = Depends(get_current_user),
) -> str:
    """Return authenticated user's ID string."""
    return str(current_user.id)


def get_chat_service(
    settings: Settings = Depends(get_app_settings),
    retriever: Any = Depends(get_retriever),
    reranker: Any = Depends(get_reranker),
    generator: Any = Depends(get_generator),
    provider_manager: Any = Depends(get_provider_manager),
    query_rewriter: Any = Depends(get_query_rewriter),
    retrieval_planner: Any = Depends(get_retrieval_planner),
) -> ChatService:
    """Provide ChatService instance configured with RAG pipeline and provider dependencies."""
    from backend.app.services.chat_service import ChatService

    return ChatService(
        settings=settings,
        hybrid_retriever=retriever,
        reranker=reranker,
        generator=generator,
        provider_manager=provider_manager,
        query_rewriter=query_rewriter,
        retrieval_planner=retrieval_planner,
    )
