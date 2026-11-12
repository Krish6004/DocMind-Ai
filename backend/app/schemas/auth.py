"""
Pydantic schemas for Enterprise Authentication, User Settings, and MongoDB
Chat Sessions (Sprint 7.0).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full display name")
    email: str = Field(..., min_length=5, max_length=255, description="Unique user email")
    password: str = Field(..., min_length=6, max_length=128, description="Account password")


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None, description="Refresh JWT (optional if sent via HttpOnly cookie)")


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime | str
    last_login: datetime | str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class UserSettingsSchema(BaseModel):
    preferred_provider: str = "gemini"
    preferred_model: str = "gemini-2.5-flash"
    theme: str = "dark"
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    top_k: int = Field(default=8, ge=1, le=50)
    memory_enabled: bool = True


class ChatSessionSummary(BaseModel):
    conversation_id: str
    user_id: str
    title: str
    last_message: str = ""
    is_pinned: bool = False
    message_count: int = 0
    created_at: datetime | str
    updated_at: datetime | str


class ChatSessionDetail(ChatSessionSummary):
    messages: list[dict[str, Any]] = Field(default_factory=list)


class ChatSessionCreateRequest(BaseModel):
    conversation_id: str | None = None
    title: str = "New Chat"


class ChatSessionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    is_pinned: bool | None = None
