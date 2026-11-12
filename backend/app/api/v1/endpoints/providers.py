"""
API Endpoints for Enterprise AI Provider Management.
Provides CRUD, connection diagnostics, Mode A/B configuration, and priority ranking.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_database_session, get_provider_manager
from backend.app.core.logging import get_logger
from backend.app.schemas.common import BaseResponse
from backend.app.schemas.provider import (
    ProviderInfo,
    ProviderListResponse,
    ProviderPriorityUpdateRequest,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderUpdateRequest,
)
from backend.app.services.llm.manager import ProviderManager

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[ProviderListResponse],
    summary="List all AI Providers",
    description="Retrieve public configuration, connection states, and fallback priority for all supported AI providers.",
)
async def list_providers(
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[ProviderListResponse]:
    providers = provider_manager.list_providers(db=db)
    active_id = provider_manager.get_active_provider_id(db=db)
    priority_order = provider_manager.get_priority_order(db=db)

    return BaseResponse(
        success=True,
        data=ProviderListResponse(
            active_provider=active_id,
            priority_order=priority_order,
            providers=providers,
        ),
        message=f"Retrieved {len(providers)} AI provider configuration(s).",
    )


@router.get(
    "/{provider_id}",
    response_model=BaseResponse[ProviderInfo],
    summary="Get single AI Provider",
    description="Retrieve configuration and diagnostics for a specific provider.",
)
async def get_provider(
    provider_id: str,
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[ProviderInfo]:
    providers = [p for p in provider_manager.list_providers(db=db) if p.id == provider_id]
    if not providers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' is not recognized.",
        )
    return BaseResponse(
        success=True,
        data=providers[0],
        message=f"Provider '{provider_id}' details retrieved.",
    )


@router.post(
    "/{provider_id}/test",
    response_model=BaseResponse[ProviderTestResponse],
    summary="Test Provider Connection",
    description="Ping provider endpoint to verify credentials, model accessibility, and measure round-trip latency.",
)
async def test_provider_connection(
    provider_id: str,
    payload: ProviderTestRequest | None = None,
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[ProviderTestResponse]:
    if provider_id not in provider_manager.adapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found.",
        )

    api_key = payload.api_key if payload else None
    base_url = payload.base_url if payload else None
    model = payload.model if payload else None

    logger.info("Executing connection test for provider '%s' (model: %s)", provider_id, model)
    result = provider_manager.test_provider(
        provider_id=provider_id,
        model=model,
        db=db,
    )

    return BaseResponse(
        success=result.status.lower() == "connected",
        data=result,
        message=result.message,
    )


@router.put(
    "/{provider_id}",
    response_model=BaseResponse[ProviderInfo],
    summary="Update Provider Configuration",
    description="Update provider selected model or activation state.",
)
async def update_provider(
    provider_id: str,
    payload: ProviderUpdateRequest,
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[ProviderInfo]:
    if provider_id not in provider_manager.adapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found.",
        )

    updated = provider_manager.update_provider_config(
        provider_id=provider_id,
        selected_model=payload.selected_model,
        is_active=payload.is_active,
        db=db,
    )

    return BaseResponse(
        success=True,
        data=updated,
        message=f"Provider '{provider_id}' configuration updated successfully.",
    )


@router.put(
    "/priority/order",
    response_model=BaseResponse[list[str]],
    summary="Update Provider Priority Order",
    description="Reorder the fallback priority chain and optionally assign the primary active provider.",
)
async def update_provider_priority(
    payload: ProviderPriorityUpdateRequest,
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[list[str]]:
    new_order = provider_manager.set_priority_order(
        priority_order=payload.priority_order,
        active_provider=payload.active_provider,
        db=db,
    )

    return BaseResponse(
        success=True,
        data=new_order,
        message="Provider fallback priority order updated.",
    )


@router.post(
    "/active/{provider_id}",
    response_model=BaseResponse[str],
    summary="Set Active Provider",
    description="Quickly set a provider as the primary active generator.",
)
async def set_active_provider(
    provider_id: str,
    db: Session = Depends(get_database_session),
    provider_manager: ProviderManager = Depends(get_provider_manager),
) -> BaseResponse[str]:
    if provider_id not in provider_manager.adapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found.",
        )

    provider_manager.update_provider_config(
        provider_id=provider_id,
        is_active=True,
        db=db,
    )

    return BaseResponse(
        success=True,
        data=provider_id,
        message=f"Provider '{provider_id}' is now the primary active provider.",
    )

