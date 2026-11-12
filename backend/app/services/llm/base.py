"""
Base abstraction and contract for all LLM Adapters in DocMind AI.
"""

from __future__ import annotations

import abc
import time
from typing import Any

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


def mask_key(api_key: str | None) -> str | None:
    """
    Mask an API key for safe display in administrative dashboards.
    Returns something like 'AIza...3B8f' or 'sk-...9d21'.
    Never exposes full key material.
    """
    if not api_key:
        return None
    key = api_key.strip()
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:4]}••••{key[-4:]}"


class BaseLLMAdapter(abc.ABC):
    """
    Abstract base adapter for LLM inference providers.
    Encapsulates provider-specific serialization, endpoints, and error handling.
    """

    provider_id: str
    name: str
    tagline: str
    description: str
    default_model: str
    supported_models: list[str]
    default_base_url: str
    requires_api_key: bool = True

    @abc.abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: int = 45,
    ) -> dict[str, Any]:
        """
        Execute generation against the provider endpoint.

        Args:
            messages: Standard [{"role": "system"|"user"|"assistant", "content": "..."}]
            model: Optional model override
            api_key: Resolved active API key
            base_url: Resolved active base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: HTTP timeout in seconds

        Returns:
            Dict containing:
              - "answer": str
              - "model": str
              - "prompt_tokens": int
              - "completion_tokens": int
              - "provider": str
        """
        pass

    @abc.abstractmethod
    def test_connection(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """
        Ping provider to verify credentials, reachability, and model availability.

        Returns:
            Dict containing:
              - "success": bool
              - "latency_ms": float | None
              - "model": str
              - "error": str | None
              - "message": str
        """
        pass

