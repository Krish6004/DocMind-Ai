"""
Google Gemini LLM Adapter.
Direct REST integration with Google AI Studio / Gemini v1beta API.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from backend.app.core.logging import get_logger
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class GeminiAdapter(BaseLLMAdapter):
    """
    Adapter for Google Gemini models via Gemini API.
    """

    provider_id = "gemini"
    name = "Gemini"
    tagline = "Google's flagship multimodal models."
    description = (
        "Default recommended provider. Ultra-fast reasoning, large context windows, "
        "and superior grounded context comprehension."
    )
    default_model = "gemini-2.5-flash"
    supported_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    requires_api_key = True

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Convert standard chat messages into Gemini contents and systemInstruction."""
        system_instruction: dict[str, Any] | None = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role in ("assistant", "model"):
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        # Gemini requires at least one user turn
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        return system_instruction, contents

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
            raise ValueError("Gemini API key is required but was not provided.")

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/models/{active_model}:generateContent?key={api_key}"

        system_instruction, contents = self._convert_messages(messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        headers = {"Content-Type": "application/json"}

        logger.debug("Dispatching Gemini generateContent request (model: %s)", active_model)
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if not resp.ok:
            error_msg = f"Gemini API error (HTTP {resp.status_code}): {resp.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned no response candidates.")
            answer = candidates[0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Failed to parse Gemini response: {data}") from exc

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)

        return {
            "answer": answer,
            "model": active_model,
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
                "message": "Missing API Key. Please provide a valid Google Gemini API key.",
            }

        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/models/{active_model}:generateContent?key={api_key}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": "Ping"}]}],
            "generationConfig": {"maxOutputTokens": 2},
        }

        t0 = time.perf_counter()
        try:
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)
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

