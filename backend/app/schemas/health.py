"""
Health check and system status response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Schema for system health check response.
    """

    status: str = Field(default="healthy", description="Overall health status of the API")
    version: str = Field(default="1.0.0", description="API version")
    environment: str = Field(default="development", description="Current deployment environment")
    timestamp: datetime = Field(description="UTC timestamp of the health check")
    services: dict[str, str] = Field(
        default_factory=lambda: {
            "api": "operational",
            "ai_engine": "ready",
            "storage": "available",
        },
        description="Health status of internal subsystems",
    )


class RootResponse(BaseModel):
    """
    Schema for API root endpoint response.
    """

    name: str = Field(description="Application name")
    version: str = Field(description="Application version")
    description: str = Field(description="Service description")
    documentation: dict[str, str] = Field(description="Links to interactive API documentation")
    endpoints: dict[str, str] = Field(description="Key entry point endpoints")
