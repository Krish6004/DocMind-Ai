"""
Per-User MongoDB Chat Sessions & User Settings Endpoints (Sprint 7.0).
All routes are strictly scoped to the authenticated user_id.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_auth_service, get_current_user_id
from backend.app.schemas.auth import (
    ChatSessionCreateRequest,
    ChatSessionDetail,
    ChatSessionSummary,
    ChatSessionUpdateRequest,
    UserSettingsSchema,
)
from backend.app.schemas.common import BaseResponse
from backend.app.services.auth_service import AuthService

sessions_router = APIRouter()
user_settings_router = APIRouter()


@sessions_router.get(
    "",
    response_model=BaseResponse[list[ChatSessionSummary]],
    status_code=status.HTTP_200_OK,
    summary="List Authenticated User Chat Sessions",
)
def list_user_sessions(
    search: str | None = Query(default=None, description="Optional title filter"),
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[list[ChatSessionSummary]]:
    items = auth_service.list_sessions(user_id=user_id, search=search)
    return BaseResponse(
        success=True,
        message=f"Retrieved {len(items)} chat session(s).",
        data=items,
    )


@sessions_router.post(
    "",
    response_model=BaseResponse[ChatSessionSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Chat Session",
)
def create_user_session(
    payload: ChatSessionCreateRequest = ChatSessionCreateRequest(),
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[ChatSessionSummary]:
    session = auth_service.create_session(
        user_id=user_id,
        conversation_id=payload.conversation_id,
        title=payload.title,
    )
    return BaseResponse(
        success=True,
        message="Chat session ready.",
        data=session,
    )


@sessions_router.get(
    "/{conversation_id}",
    response_model=BaseResponse[ChatSessionDetail],
    status_code=status.HTTP_200_OK,
    summary="Get Chat Session Messages",
)
def get_user_session(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[ChatSessionDetail]:
    session = auth_service.get_session(user_id=user_id, conversation_id=conversation_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
    return BaseResponse(
        success=True,
        message="Chat session retrieved.",
        data=session,
    )


@sessions_router.patch(
    "/{conversation_id}",
    response_model=BaseResponse[ChatSessionSummary],
    status_code=status.HTTP_200_OK,
    summary="Rename or Pin Chat Session",
)
def update_user_session(
    conversation_id: str,
    payload: ChatSessionUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[ChatSessionSummary]:
    updated = auth_service.update_session(
        user_id=user_id,
        conversation_id=conversation_id,
        title=payload.title,
        is_pinned=payload.is_pinned,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
    return BaseResponse(
        success=True,
        message="Chat session updated.",
        data=updated,
    )


@sessions_router.delete(
    "/{conversation_id}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete Chat Session",
)
def delete_user_session(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[dict]:
    deleted = auth_service.delete_session(user_id=user_id, conversation_id=conversation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
    return BaseResponse(
        success=True,
        message="Chat session deleted.",
        data={"conversation_id": conversation_id, "deleted": True},
    )


@user_settings_router.get(
    "/settings",
    response_model=BaseResponse[UserSettingsSchema],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Settings",
)
def get_user_settings(
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[UserSettingsSchema]:
    return BaseResponse(
        success=True,
        message="User settings retrieved.",
        data=auth_service.get_user_settings(user_id),
    )


@user_settings_router.put(
    "/settings",
    response_model=BaseResponse[UserSettingsSchema],
    status_code=status.HTTP_200_OK,
    summary="Update Current User Settings",
)
def update_user_settings(
    payload: UserSettingsSchema,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[UserSettingsSchema]:
    return BaseResponse(
        success=True,
        message="User settings saved.",
        data=auth_service.update_user_settings(user_id, payload),
    )

