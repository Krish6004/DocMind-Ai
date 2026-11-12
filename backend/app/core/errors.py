"""
Custom exceptions and global exception handlers for DocMind AI Backend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base & Domain Exceptions
# ---------------------------------------------------------------------------


class DocMindAPIException(Exception):
    """Base exception for all domain-level DocMind AI API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "internal_error",
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details


class ResourceNotFoundException(DocMindAPIException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Any = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="resource_not_found",
            details=details,
        )


HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class ValidationException(DocMindAPIException):
    """Raised when domain validation fails."""

    def __init__(self, message: str = "Validation failed", details: Any = None) -> None:
        super().__init__(
            message=message,
            status_code=HTTP_422,
            error_type="validation_error",
            details=details,
        )


class ServiceUnavailableException(DocMindAPIException):
    """Raised when a downstream service (e.g. LLM provider) is unavailable."""

    def __init__(self, message: str = "Service unavailable", details: Any = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="service_unavailable",
            details=details,
        )


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------


def make_error_payload(
    error_type: str,
    message: str,
    status_code: int,
    details: Any = None,
) -> dict[str, Any]:
    """Build a standardized error response dictionary."""
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


async def docmind_api_exception_handler(request: Request, exc: DocMindAPIException) -> JSONResponse:
    """Handle custom DocMind domain exceptions."""
    logger.warning(
        "DocMindAPIException: %s (status_code=%d, type=%s) on %s %s",
        exc.message,
        exc.status_code,
        exc.error_type,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(
            error_type=exc.error_type,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors with clear error details."""
    logger.info("RequestValidationError on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=HTTP_422,
        content=make_error_payload(
            error_type="validation_error",
            message="Request input validation failed",
            status_code=HTTP_422,
            details=exc.errors(),
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI/Starlette HTTP exceptions."""
    logger.warning("HTTPException: %s on %s %s", exc.detail, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(
            error_type="http_error",
            message=str(exc.detail),
            status_code=exc.status_code,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=make_error_payload(
            error_type="internal_server_error",
            message="An unexpected error occurred while processing your request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application."""
    app.add_exception_handler(DocMindAPIException, docmind_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
