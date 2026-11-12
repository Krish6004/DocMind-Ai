"""
Common standardized schemas used across DocMind AI API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper."""

    success: bool = Field(default=True, description="Whether the operation succeeded")
    data: T | None = Field(default=None, description="Response payload")
    message: str | None = Field(default=None, description="Optional informational message")


class ErrorDetail(BaseModel):
    """Detailed error structure."""

    type: str = Field(description="Error classification type")
    message: str = Field(description="Human-readable error description")
    status_code: int = Field(description="HTTP status code")
    details: Any = Field(default=None, description="Optional granular error diagnostics")
    timestamp: datetime = Field(description="Error timestamp in UTC")


class ErrorResponse(BaseModel):
    """Standardized error envelope."""

    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(description="Error metadata and details")
