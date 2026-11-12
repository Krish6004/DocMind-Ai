"""
Enterprise Authentication Endpoints (/api/auth) for DocMind AI v2.0 (Sprint 7.0).

Routes:
  - POST /api/auth/register
  - POST /api/auth/login
  - POST /api/auth/logout
  - POST /api/auth/refresh
  - GET  /api/auth/me
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status

from backend.app.api.deps import get_app_settings, get_auth_service, get_current_user
from backend.app.core.config import Settings
from backend.app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UserOut,
)
from backend.app.schemas.common import BaseResponse
from backend.app.services.auth_service import AuthService

router = APIRouter()


def _set_auth_cookies(
    response: Response,
    tokens: AuthTokenResponse,
    settings: Settings,
) -> None:
    """Attach HttpOnly JWT cookies alongside JSON response."""
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


@router.post(
    "/register",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
def register(
    payload: RegisterRequest,
    response: Response,
    settings: Settings = Depends(get_app_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[AuthTokenResponse]:
    tokens = auth_service.register(
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )
    _set_auth_cookies(response, tokens, settings)
    return BaseResponse(
        success=True,
        message="Account created successfully.",
        data=tokens,
    )


@router.post(
    "/login",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
)
def login(
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_app_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[AuthTokenResponse]:
    tokens = auth_service.login(email=payload.email, password=payload.password)
    _set_auth_cookies(response, tokens, settings)
    return BaseResponse(
        success=True,
        message="Login successful.",
        data=tokens,
    )


@router.post(
    "/refresh",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
    settings: Settings = Depends(get_app_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[AuthTokenResponse]:
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
        )
    tokens = auth_service.refresh(refresh_token)
    _set_auth_cookies(response, tokens, settings)
    return BaseResponse(
        success=True,
        message="Token refreshed successfully.",
        data=tokens,
    )


@router.post(
    "/logout",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Logout & Revoke Refresh Token",
)
def logout(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> BaseResponse[dict]:
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    auth_service.logout(refresh_token)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return BaseResponse(
        success=True,
        message="Logged out successfully.",
        data={"logged_out": True},
    )


@router.get(
    "/me",
    response_model=BaseResponse[UserOut],
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User",
)
def get_me(
    current_user: UserOut = Depends(get_current_user),
) -> BaseResponse[UserOut]:
    return BaseResponse(
        success=True,
        message="Current user retrieved.",
        data=current_user,
    )
