"""
Ollama Local LLM Adapter.
Direct REST integration with local Ollama daemon (http://localhost:11434).
"""

from __future__ import annotations

import time
from typing import Any

import requests

from backend.app.core.logging import get_logger
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """
    Adapter for local Ollama instances. Zero external network calls.
    """

    provider_id = "ollama"
    name = "Ollama (Local)"
    tagline = "Air-gapped on-premise execution."
    description = (
        "Run open-source LLMs entirely offline on your local machine with "
        "zero data egress, absolute privacy, and hardware-accelerated local inference."
    )
    default_model = "llama3.2"
    supported_models = [
        "llama3.2",
        "llama3",
        "mistral",
        "deepseek-r1",
        "qwen2.5",
        "phi3",
    ]
    default_base_url = "http://localhost:11434"
    requires_api_key = False

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: int = 60,
    ) -> dict[str, Any]:
        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        url = f"{active_base}/api/chat"

        payload = {
            "model": active_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.debug("Dispatching Ollama chat request to %s (model: %s)", url, active_model)
        resp = requests.post(url, json=payload, timeout=timeout)

        if not resp.ok:
            error_msg = f"Ollama daemon error (HTTP {resp.status_code}): {resp.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        try:
            answer = data["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Failed to parse Ollama response: {data}") from exc

        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

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
        timeout: int = 8,
    ) -> dict[str, Any]:
        active_model = model or self.default_model
        active_base = (base_url or self.default_base_url).rstrip("/")
        tags_url = f"{active_base}/api/tags"

        t0 = time.perf_counter()
        try:
            resp = requests.get(tags_url, timeout=timeout)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            if resp.ok:
                data = resp.json()
                models_list = [m.get("name", "") for m in data.get("models", [])]
                model_note = f" (installed models: {', '.join(models_list[:3])})" if models_list else ""
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "model": active_model,
                    "error": None,
                    "message": f"Connected to local Ollama daemon ({latency_ms}ms){model_note}.",
                }
            else:
                return {
                    "success": False,
                    "latency_ms": latency_ms,
                    "model": active_model,
                    "error": resp.text[:200],
                    "message": f"Ollama daemon rejected request (HTTP {resp.status_code}).",
                }
        except Exception as exc:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return {
                "success": False,
                "latency_ms": latency_ms,
                "model": active_model,
                "error": str(exc),
                "message": f"Cannot connect to Ollama at {active_base}. Ensure 'ollama serve' is running.",
            }

