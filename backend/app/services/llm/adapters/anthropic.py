"""
Anthropic Claude LLM Adapter.
Direct REST integration with Anthropic Claude Messages API.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from backend.app.core.logging import get_logger
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class AnthropicAdapter(BaseLLMAdapter):
    """
    Adapter for Anthropic Claude models (Claude 3.7 Sonnet, 3.5 Sonnet, 3.5 Haiku).
    """

    provider_id = "anthropic"
    name = "Anthropic Claude"
    tagline = "Nuanced, constitutional reasoning."
    description = (
        "Enterprise-favorite reasoning engine with deep contextual synthesis, "
        "impeccable adherence to system contracts, and reduced sycophancy."
    )
    default_model = "claude-3-5-haiku-20241022"
    supported_models = [
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]
    default_base_url = "https://api.anthropic.com/v1"
    requires_api_key = True

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Convert chat messages into Anthropic system string and messages list."""
        system_prompt: str | None = None
        formatted_messages: list[dict[str, str]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role in ("assistant", "model"):
                formatted_messages.append({"role": "assistant", "content": content})
            else:
                formatted_messages.append({"role": "user", "content": content})

        if not formatted_messages:
            formatted_messages.append({"role": "user", "content": "Hello"})

        return system_prompt, formatted_messages

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
        if not api_key:
            raise ValueError("Anthropic API key is required but was not provided.")

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/messages"

        system_prompt, formatted_messages = self._convert_messages(messages)

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": active_model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        logger.debug("Dispatching Anthropic message request (model: %s)", active_model)
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if not resp.ok:
            error_msg = f"Anthropic API error (HTTP {resp.status_code}): {resp.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        try:
            content_blocks = data.get("content", [])
            answer = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        except Exception as exc:
            raise ValueError(f"Failed to parse Anthropic response: {data}") from exc

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)

        return {
            "answer": answer,
            "model": data.get("model", active_model),
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "provider": self.provider_id,
        }

    def test_connection(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        if not api_key:
            return {
                "success": False,
                "latency_ms": None,
                "model": model or self.default_model,
                "error": "No API key configured.",
                "message": "Missing API Key. Please provide an Anthropic Claude API key.",
            }

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/messages"

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": active_model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }

        t0 = time.perf_counter()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            if resp.ok:
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "model": active_model,
                    "error": None,
                    "message": f"Connected successfully ({latency_ms}ms).",
                }
            else:
                return {
                    "success": False,
                    "latency_ms": latency_ms,
                    "model": active_model,
                    "error": resp.text[:200],
                    "message": f"Connection rejected (HTTP {resp.status_code}).",
                }
        except Exception as exc:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return {
                "success": False,
                "latency_ms": latency_ms,
                "model": active_model,
                "error": str(exc),
                "message": f"Connection failed: {exc}",
            }

