"""
API v1 Router aggregation.

Wires together all v1 endpoints under /api/v1.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.endpoints import chat, documents, evaluation, health, providers, root, upload

api_router = APIRouter()

# Core system endpoints
api_router.include_router(root.router, tags=["System"])
api_router.include_router(health.router, tags=["System"])

# Document Ingestion & Management endpoints
api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(upload.router, prefix="/documents", tags=["Upload"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Conversational RAG & Chat endpoints
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & RAG"])

# AI Provider Management endpoints
api_router.include_router(providers.router, prefix="/providers", tags=["AI Providers"])

# Enterprise Evaluation & Benchmarking endpoints
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation & Benchmarking"])
