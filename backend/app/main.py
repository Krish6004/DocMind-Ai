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
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
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
