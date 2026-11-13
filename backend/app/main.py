"""
Main FastAPI application entry point for DocMind AI.

Run locally with:
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.api import api_router
from backend.app.api.v1.endpoints import auth as auth_endpoints
from backend.app.api.v1.endpoints import health, root
from backend.app.core.config import get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import get_logger, setup_backend_logging

logger = get_logger(__name__)

# Strong references for background tasks to prevent Python GC collection
_background_tasks: set[Any] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management (startup and shutdown events).
    """
    settings = get_settings()

    # --- Startup Event ---
    setup_backend_logging()
    logger.info(
        "DocMind AI Backend starting up (version: %s, environment: %s, debug: %s)",
        settings.VERSION,
        settings.ENVIRONMENT,
        settings.DEBUG,
    )

    # Ensure required data storage directories exist
    try:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        settings.STORE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directories verified at '%s'", settings.DATA_DIR)
    except Exception as exc:
        logger.error("Failed to initialize storage directories: %s", exc)

    # Initialize SQLite database schema
    try:
        from backend.app.db.session import init_db

        init_db()
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc)

    # Pre-warm AI models (VectorStore & Hugging Face EmbeddingModel) in background
    # so first upload/chat doesn't stall downloading weights on user requests
    import asyncio

    async def _prewarm_ai_models() -> None:
        try:
            logger.info("Background pre-warming: initializing VectorStore and EmbeddingModel...")
            from backend.app.api.deps import get_embedding_model, get_vector_store

            await asyncio.to_thread(get_vector_store, settings)
            await asyncio.to_thread(get_embedding_model)
            logger.info("AI models pre-warmed successfully; ready for document ingestion.")
        except Exception as exc:
            logger.warning("Could not pre-warm AI models at startup: %s", exc)

    prewarm_task = asyncio.create_task(_prewarm_ai_models())
    _background_tasks.add(prewarm_task)
    prewarm_task.add_done_callback(_background_tasks.discard)

    yield

    # --- Shutdown Event ---
    logger.info("DocMind AI Backend shutting down cleanly...")


def create_application() -> FastAPI:
    """
    FastAPI application factory.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    allow_origins = settings.CORS_ORIGINS
    # Starlette CORSMiddleware rejects allow_origins=["*"] when allow_credentials=True.
    # To support Vercel preview & production URLs, Render, localhost, and custom domains safely:
    if "*" in allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ],
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app|.*\.onrender\.com)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.debug("CORS middleware initialized with regex for Vercel/Render/localhost")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.debug("CORS middleware initialized with origins: %s", settings.CORS_ORIGINS)

    # Register custom and global exception handlers
    register_exception_handlers(app)

    # Mount top-level health and root endpoints
    app.include_router(root.router, tags=["Root"])
    app.include_router(health.router, tags=["Health"])

    # Mount Authentication endpoints (/api/auth/*)
    app.include_router(auth_endpoints.router, prefix="/api/auth", tags=["Authentication"])

    # Mount versioned API routes (/api/v1)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
