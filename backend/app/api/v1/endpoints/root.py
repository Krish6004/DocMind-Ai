"""
Root service descriptor endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.health import RootResponse

router = APIRouter()


@router.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="API Root Information",
    description="Returns service metadata, version, and documentation links.",
)
async def get_root(
    settings: Settings = Depends(get_settings),
) -> RootResponse:
    """
    Get root API information and documentation links.
    """
    return RootResponse(
        name=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        documentation={
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": f"{settings.API_V1_STR}/openapi.json",
        },
        endpoints={
            "root": "/",
            "health": "/health",
            "api_v1_health": f"{settings.API_V1_STR}/health",
            "api_v1_root": f"{settings.API_V1_STR}/",
        },
    )
