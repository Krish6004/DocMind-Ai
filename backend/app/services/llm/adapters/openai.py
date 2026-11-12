"""
OpenAI LLM Adapter.
Direct REST integration with OpenAI API.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from backend.app.core.logging import get_logger
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """
    Adapter for OpenAI models (GPT-4o, GPT-4o-mini, o3-mini).
    """

    provider_id = "openai"
    name = "OpenAI"
    tagline = "Industry standard intelligence."
    description = (
        "Pioneering frontier models including GPT-4o and lightweight GPT-4o-mini "
        "with exceptional instruction following and factual coherence."
    )
    default_model = "gpt-4o-mini"
    supported_models = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "o3-mini",
    ]
    default_base_url = "https://api.openai.com/v1"
    requires_api_key = True

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
            raise ValueError("OpenAI API key is required but was not provided.")

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": active_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        # o3-mini does not support temperature customization
        if not active_model.startswith("o"):
            payload["temperature"] = temperature

        logger.debug("Dispatching OpenAI chat completion (model: %s)", active_model)
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if not resp.ok:
            error_msg = f"OpenAI API error (HTTP {resp.status_code}): {resp.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        try:
            choice = data["choices"][0]
            answer = choice["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Failed to parse OpenAI response: {data}") from exc

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

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
                "message": "Missing API Key. Please provide an OpenAI API key.",
            }

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
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

