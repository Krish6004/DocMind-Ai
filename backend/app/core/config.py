"""
Configuration management for DocMind AI Backend.

Loads environment variables from .env or system environment with type validation
using Pydantic Settings.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings and configuration parameters.
    """

    # Project metadata
    PROJECT_NAME: str = "DocMind AI Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Enterprise-grade Retrieval-Augmented Generation (RAG) backend API "
        "built with FastAPI."
    )
    API_V1_STR: str = "/api/v1"

    # Environment & Debug
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DOCMIND_LOG_LEVEL: str = "INFO"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS configuration
    CORS_ORIGINS: list[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["*"]

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    STORE_DIR: Path = BASE_DIR / "data" / "store"
    DATABASE_URL: str = "sqlite:///./data/docmind.db"

    # Upload validation constraints
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".md"}

    # Active LLM Provider & Priority
    DEFAULT_PROVIDER: str = "gemini"
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    PROVIDER_PRIORITY: list[str] = ["gemini", "groq"]

    # Retrieval & Model Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    TOP_K: int = 8
    RRF_K: int = 60
    SIMILARITY_THRESHOLD: float = 0.25
    ENABLE_QUERY_REWRITE: bool = True
    ENABLE_RETRIEVAL_PLANNER: bool = True

    # Storage Settings
    VECTOR_PATH: str = "data/vector_store"
    UPLOAD_FOLDER: str = "data/uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Provider: Google Gemini (Default Recommended)
    GEMINI_API_KEY: str | None = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Provider: Groq (Fallback)
    GROQ_API_KEY: str | None = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Future Providers (Coming Soon)
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # MongoDB Atlas & Enterprise Auth (Sprint 7.0)
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "docmind_ai"
    JWT_SECRET: str = "docmind_dev_jwt_secret_change_in_prod"
    JWT_REFRESH_SECRET: str = "docmind_dev_refresh_secret_change_in_prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    REQUIRE_AUTH: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached instance of the application settings.
    """
    return Settings()
