"""
Groq LLM Adapter.
Direct REST integration with Groq Cloud ultra-fast LPU inference.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from backend.app.core.logging import get_logger
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class GroqAdapter(BaseLLMAdapter):
    """
    Adapter for Groq LPU inference models.
    """

    provider_id = "groq"
    name = "Groq"
    tagline = "Ultra-fast inference."
    description = (
        "LPU-accelerated token generation delivering near-instant responses with "
        "open-weights architectures like Llama-3 and Mixtral."
    )
    default_model = "openai/gpt-oss-120b"
    supported_models = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]
    default_base_url = "https://api.groq.com/openai/v1"
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
            raise ValueError("Groq API key is required but was not provided.")

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.debug("Dispatching Groq chat completion (model: %s)", active_model)
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if not resp.ok:
            error_msg = f"Groq API error (HTTP {resp.status_code}): {resp.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        try:
            choice = data["choices"][0]
            answer = choice["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Failed to parse Groq response: {data}") from exc

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
                "message": "Missing API Key. Please provide a Groq API key.",
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

