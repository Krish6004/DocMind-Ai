"""
Enterprise Authentication, User Settings, and MongoDB Session Service (Sprint 7.0).

Security Guarantees:
- Passwords are hashed using bcrypt (never stored in plaintext).
- Short-lived JWT Access Tokens + MongoDB-tracked Refresh Tokens.
- Strictly scoped by user_id across sessions and settings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.db.mongo import MongoManager
from backend.app.schemas.auth import (
    AuthTokenResponse,
    ChatSessionDetail,
    ChatSessionSummary,
    UserOut,
    UserSettingsSchema,
)

logger = get_logger(__name__)


class AuthService:
    """
    Handles bcrypt hashing, JWT issuance/verification, MongoDB user persistence,
    user settings, and cross-device chat session synchronization.
    """

    ALGORITHM = "HS256"

    def __init__(self, mongo: MongoManager, settings: Settings | None = None) -> None:
        self.mongo = mongo
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Password Hashing (bcrypt)
    # ------------------------------------------------------------------

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    # ------------------------------------------------------------------
    # JWT Token Management
    # ------------------------------------------------------------------

    def create_access_token(self, user_id: str, email: str) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self.settings.JWT_SECRET, algorithm=self.ALGORITHM)

    def create_refresh_token(self, user_id: str, email: str) -> tuple[str, str, datetime]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        jti = uuid.uuid4().hex
        payload = {
            "sub": user_id,
            "email": email,
            "jti": jti,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(payload, self.settings.JWT_REFRESH_SECRET, algorithm=self.ALGORITHM)
        return token, jti, exp

    def verify_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self.settings.JWT_SECRET, algorithms=[self.ALGORITHM])
            if payload.get("type") != "access" or not payload.get("sub"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token type.",
                )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has expired.",
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            ) from exc

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self.settings.JWT_REFRESH_SECRET, algorithms=[self.ALGORITHM])
            if payload.get("type") != "refresh" or not payload.get("sub") or not payload.get("jti"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token.",
                )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            ) from exc

    # ------------------------------------------------------------------
    # Auth Operations (Register, Login, Refresh, Logout, Me)
    # ------------------------------------------------------------------

    def _doc_to_user_out(self, doc: dict[str, Any]) -> UserOut:
        return UserOut(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            avatar_url=doc.get("avatar_url"),
            is_active=bool(doc.get("is_active", True)),
            created_at=doc["created_at"],
            last_login=doc.get("last_login"),
        )

    def _issue_session_tokens(self, user_doc: dict[str, Any]) -> AuthTokenResponse:
        user_id = str(user_doc["_id"])
        email = user_doc["email"]
        access_token = self.create_access_token(user_id, email)
        refresh_token, jti, exp = self.create_refresh_token(user_id, email)

        self.mongo.refresh_tokens.insert_one({
            "jti": jti,
            "user_id": user_id,
            "revoked": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": exp,
        })

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=self._doc_to_user_out(user_doc),
        )

    def register(self, name: str, email: str, password: str) -> AuthTokenResponse:
        norm_email = email.strip().lower()
        if "@" not in norm_email or "." not in norm_email.split("@")[-1]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Please provide a valid email address.",
            )

        existing = self.mongo.users.find_one({"email": norm_email})
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4().hex
        user_doc = {
            "_id": user_id,
            "name": name.strip(),
            "email": norm_email,
            "password_hash": self.hash_password(password),
            "avatar_url": None,
            "created_at": now,
            "updated_at": now,
            "last_login": now,
            "is_active": True,
        }
        self.mongo.users.insert_one(user_doc)

        # Initialize default per-user settings
        self.mongo.user_settings.insert_one({
            "user_id": user_id,
            "preferred_provider": self.settings.DEFAULT_PROVIDER,
            "preferred_model": self.settings.DEFAULT_MODEL,
            "theme": "dark",
            "temperature": 0.2,
            "top_k": self.settings.TOP_K,
            "memory_enabled": True,
            "updated_at": now,
        })

        logger.info("Registered new DocMind user '%s' (id=%s)", norm_email, user_id)
        return self._issue_session_tokens(user_doc)

    def login(self, email: str, password: str) -> AuthTokenResponse:
        norm_email = email.strip().lower()
        user_doc = self.mongo.users.find_one({"email": norm_email})
        if user_doc is None or not self.verify_password(password, user_doc.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive.",
            )

        now = datetime.now(timezone.utc)
        self.mongo.users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": now, "updated_at": now}},
        )
        user_doc["last_login"] = now
        return self._issue_session_tokens(user_doc)

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        payload = self.verify_refresh_token(refresh_token)
        jti = payload["jti"]
        user_id = payload["sub"]

        stored = self.mongo.refresh_tokens.find_one({"jti": jti, "user_id": user_id})
        if stored is None or stored.get("revoked", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or is unknown.",
            )

        user_doc = self.mongo.users.find_one({"_id": user_id})
        if user_doc is None or not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive.",
            )

        # Rotate refresh token
        self.mongo.refresh_tokens.update_one({"jti": jti}, {"$set": {"revoked": True}})
        return self._issue_session_tokens(user_doc)

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = self.verify_refresh_token(refresh_token)
            self.mongo.refresh_tokens.update_one(
                {"jti": payload["jti"]},
                {"$set": {"revoked": True}},
            )
        except HTTPException:
            pass

    def get_user_by_id(self, user_id: str) -> UserOut | None:
        doc = self.mongo.users.find_one({"_id": user_id})
        return self._doc_to_user_out(doc) if doc else None

    # ------------------------------------------------------------------
    # Per-User Settings (MongoDB user_settings)
    # ------------------------------------------------------------------

    def get_user_settings(self, user_id: str) -> UserSettingsSchema:
        doc = self.mongo.user_settings.find_one({"user_id": user_id})
        if doc is None:
            return UserSettingsSchema(
                preferred_provider=self.settings.DEFAULT_PROVIDER,
                preferred_model=self.settings.DEFAULT_MODEL,
                top_k=self.settings.TOP_K,
            )
        return UserSettingsSchema(
            preferred_provider=doc.get("preferred_provider", self.settings.DEFAULT_PROVIDER),
            preferred_model=doc.get("preferred_model", self.settings.DEFAULT_MODEL),
            theme=doc.get("theme", "dark"),
            temperature=float(doc.get("temperature", 0.2)),
            top_k=int(doc.get("top_k", self.settings.TOP_K)),
            memory_enabled=bool(doc.get("memory_enabled", True)),
        )

    def update_user_settings(self, user_id: str, updates: UserSettingsSchema) -> UserSettingsSchema:
        now = datetime.now(timezone.utc)
        payload = updates.model_dump()
        payload["user_id"] = user_id
        payload["updated_at"] = now
        self.mongo.user_settings.update_one(
            {"user_id": user_id},
            {"$set": payload},
            upsert=True,
        )
        return updates

    # ------------------------------------------------------------------
    # Per-User Chat Sessions (MongoDB chat_sessions)
    # ------------------------------------------------------------------

    def list_sessions(self, user_id: str, search: str | None = None) -> list[ChatSessionSummary]:
        query: dict[str, Any] = {"user_id": user_id}
        if search and search.strip():
            query["title"] = {"$regex": search.strip(), "$options": "i"}
        cursor = self.mongo.chat_sessions.find(query).sort([("is_pinned", -1), ("updated_at", -1)])
        items: list[ChatSessionSummary] = []
        for doc in cursor:
            msgs = doc.get("messages", [])
            items.append(
                ChatSessionSummary(
                    conversation_id=doc["conversation_id"],
                    user_id=doc["user_id"],
                    title=doc.get("title", "New Chat"),
                    last_message=doc.get("last_message", ""),
                    is_pinned=bool(doc.get("is_pinned", False)),
                    message_count=len(msgs),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            )
        return items

    def get_session(self, user_id: str, conversation_id: str) -> ChatSessionDetail | None:
        doc = self.mongo.chat_sessions.find_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
        })
        if doc is None:
            return None
        msgs = doc.get("messages", [])
        return ChatSessionDetail(
            conversation_id=doc["conversation_id"],
            user_id=doc["user_id"],
            title=doc.get("title", "New Chat"),
            last_message=doc.get("last_message", ""),
            is_pinned=bool(doc.get("is_pinned", False)),
            message_count=len(msgs),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            messages=msgs,
        )

    def create_session(self, user_id: str, conversation_id: str | None = None, title: str = "New Chat") -> ChatSessionSummary:
        cid = conversation_id or f"session-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        existing = self.mongo.chat_sessions.find_one({"user_id": user_id, "conversation_id": cid})
        if existing is None:
            doc = {
                "user_id": user_id,
                "conversation_id": cid,
                "title": title,
                "last_message": "",
                "is_pinned": False,
                "messages": [],
                "created_at": now,
                "updated_at": now,
            }
            self.mongo.chat_sessions.insert_one(doc)
        else:
            doc = existing
        return ChatSessionSummary(
            conversation_id=doc["conversation_id"],
            user_id=doc["user_id"],
            title=doc.get("title", title),
            last_message=doc.get("last_message", ""),
            is_pinned=bool(doc.get("is_pinned", False)),
            message_count=len(doc.get("messages", [])),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    def append_chat_turn(
        self,
        user_id: str,
        conversation_id: str,
        user_msg: dict[str, Any],
        assistant_msg: dict[str, Any],
    ) -> None:
        """Persist user & assistant messages into user's MongoDB chat_sessions document."""
        if not user_id or user_id == "default":
            return
        try:
            now = datetime.now(timezone.utc)
            existing = self.mongo.chat_sessions.find_one({
                "user_id": user_id,
                "conversation_id": conversation_id,
            })
            q_text = str(user_msg.get("content", ""))
            auto_title = q_text[:38] + ("..." if len(q_text) > 38 else "")
            last_preview = str(assistant_msg.get("content", ""))[:90]

            if existing is None:
                self.mongo.chat_sessions.insert_one({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "title": auto_title or "New Chat",
                    "last_message": last_preview,
                    "is_pinned": False,
                    "messages": [user_msg, assistant_msg],
                    "created_at": now,
                    "updated_at": now,
                })
            else:
                update_fields: dict[str, Any] = {
                    "last_message": last_preview,
                    "updated_at": now,
                }
                if existing.get("title", "New Chat").startswith("New Chat") and auto_title:
                    update_fields["title"] = auto_title
                self.mongo.chat_sessions.update_one(
                    {"user_id": user_id, "conversation_id": conversation_id},
                    {
                        "$set": update_fields,
                        "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
                    },
                )
        except Exception as exc:
            logger.warning("Could not sync chat turn to MongoDB chat_sessions: %s", exc)

    def update_session(
        self,
        user_id: str,
        conversation_id: str,
        title: str | None = None,
        is_pinned: bool | None = None,
    ) -> ChatSessionSummary | None:
        update_doc: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if title is not None:
            update_doc["title"] = title.strip()
        if is_pinned is not None:
            update_doc["is_pinned"] = is_pinned

        self.mongo.chat_sessions.update_one(
            {"user_id": user_id, "conversation_id": conversation_id},
            {"$set": update_doc},
        )
        doc = self.mongo.chat_sessions.find_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
        })
        if doc is None:
            return None
        return ChatSessionSummary(
            conversation_id=doc["conversation_id"],
            user_id=doc["user_id"],
            title=doc.get("title", "New Chat"),
            last_message=doc.get("last_message", ""),
            is_pinned=bool(doc.get("is_pinned", False)),
            message_count=len(doc.get("messages", [])),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    def delete_session(self, user_id: str, conversation_id: str) -> bool:
        res = self.mongo.chat_sessions.delete_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
        })
        return res.deleted_count > 0
