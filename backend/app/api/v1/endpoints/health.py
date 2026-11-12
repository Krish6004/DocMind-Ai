"""
System health check endpoint.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns the operational status, version, and environment of DocMind AI Backend.",
)
async def check_health(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Execute health check probe.
    """
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        services={
            "api": "operational",
            "ai_engine": "ready",
            "storage": "available",
        },
    )
