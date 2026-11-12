"""
ProviderManager: Simplified Production AI Provider Orchestrator for DocMind AI.

Objective:
- Use ONLY backend .env variables for API credentials.
- Load GEMINI_API_KEY and GROQ_API_KEY automatically.
- Never expose keys to the frontend.
- Automatic provider hierarchy:
    1. Google Gemini (Default Preferred)
    2. Groq (Automatic Fallback)
- OpenAI, Claude, and Ollama marked as "Coming Soon".
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.schemas.provider import (
    ProviderInfo,
    ProviderListResponse,
    ProviderTestResponse,
)
from backend.app.services.llm.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    GroqAdapter,
    OllamaAdapter,
    OpenAIAdapter,
)
from backend.app.services.llm.base import BaseLLMAdapter

logger = get_logger(__name__)


class ProviderManager:
    """
    Production-ready AI Provider Manager.
    Decoupled from retrieval, reranking, and embeddings.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        # Registered adapters
        self.adapters: dict[str, BaseLLMAdapter] = {
            "gemini": GeminiAdapter(),
            "groq": GroqAdapter(),
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
            "ollama": OllamaAdapter(),
        }

        # Model defaults
        self._models: dict[str, str] = {
            "gemini": getattr(self.settings, "DEFAULT_MODEL", "gemini-2.5-flash"),
            "groq": getattr(self.settings, "GROQ_MODEL", "openai/gpt-oss-120b"),
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022",
            "ollama": "llama3.2",
        }

        # Cache for connection test latency
        self._test_cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Key Detection & Status
    # ------------------------------------------------------------------

    def _get_env_key(self, provider_id: str) -> str | None:
        """Resolve credential exclusively from backend environment (.env)."""
        if provider_id == "gemini":
            val = self.settings.GEMINI_API_KEY
        elif provider_id == "groq":
            val = self.settings.GROQ_API_KEY
        else:
            val = None

        return val.strip() if val and val.strip() else None

    def has_key(self, provider_id: str) -> bool:
        """Check whether valid non-empty credential exists in .env."""
        return bool(self._get_env_key(provider_id))

    def get_active_provider_id(self, db: Any = None) -> str:
        """
        Default Provider Hierarchy:
          If GEMINI_API_KEY exists → use Gemini automatically.
          Else if GROQ_API_KEY exists → use Groq.
          Else → 'none'.
        """
        if self.has_key("gemini"):
            return "gemini"
        elif self.has_key("groq"):
            return "groq"
        return "none"

    def get_priority_order(self, db: Any = None) -> list[str]:
        """Preferred priority order."""
        return ["gemini", "groq"]

    # ------------------------------------------------------------------
    # Listing & Public Metadata
    # ------------------------------------------------------------------

    def list_providers(self, db: Any = None) -> list[ProviderInfo]:
        """
        Return provider status list for the frontend.
        Exposes NO keys. Returns 'Connected', 'Not Configured', or 'Coming Soon'.
        """
        active_id = self.get_active_provider_id()
        results: list[ProviderInfo] = []

        # 1. Google Gemini (Default Recommended)
        gemini_has_key = self.has_key("gemini")
        gemini_test = self._test_cache.get("gemini", {})
        gemini_status = "Connected" if gemini_has_key else "Not Configured"
        results.append(
            ProviderInfo(
                id="gemini",
                name="Google Gemini",
                tagline="Google's flagship multimodal models.",
                description="Default recommended provider with state-of-the-art context processing and strict grounding.",
                credential_source="Backend (.env)",
                status=gemini_status,
                has_api_key=gemini_has_key,
                active_model=self._models["gemini"],
                selected_model=self._models["gemini"],
                supported_models=["gemini-2.5-flash", "gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-pro"],
                is_default=True,
                is_fallback=False,
                is_coming_soon=False,
                is_active=(active_id == "gemini"),
                priority_order=0,
                last_latency_ms=gemini_test.get("latency_ms"),
                last_tested_at=gemini_test.get("tested_at"),
            )
        )

        # 2. Groq (Automatic Fallback)
        groq_has_key = self.has_key("groq")
        groq_test = self._test_cache.get("groq", {})
        groq_status = "Connected" if groq_has_key else "Not Configured"
        results.append(
            ProviderInfo(
                id="groq",
                name="Groq",
                tagline="Ultra-fast LPU inference.",
                description="Ultra-fast fallback inference powered by Groq LPU hardware acceleration.",
                credential_source="Backend (.env)",
                status=groq_status,
                has_api_key=groq_has_key,
                active_model=self._models["groq"],
                selected_model=self._models["groq"],
                supported_models=["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "qwen/qwen3.8-27b"],
                is_default=False,
                is_fallback=True,
                is_coming_soon=False,
                is_active=(active_id == "groq"),
                priority_order=1,
                last_latency_ms=groq_test.get("latency_ms"),
                last_tested_at=groq_test.get("tested_at"),
            )
        )

        # 3. OpenAI (Coming Soon)
        results.append(
            ProviderInfo(
                id="openai",
                name="OpenAI",
                tagline="Industry standard intelligence.",
                description="Frontier models including GPT-4o and o3-mini (coming in next release).",
                credential_source="Backend (.env)",
                status="Coming Soon",
                has_api_key=False,
                active_model="gpt-4o-mini",
                selected_model="gpt-4o-mini",
                supported_models=["gpt-4o-mini", "gpt-4o"],
                is_default=False,
                is_fallback=False,
                is_coming_soon=True,
                is_active=False,
                priority_order=2,
            )
        )

        # 4. Anthropic Claude (Coming Soon)
        results.append(
            ProviderInfo(
                id="anthropic",
                name="Anthropic Claude",
                tagline="Nuanced, constitutional reasoning.",
                description="Claude 3.7 Sonnet and 3.5 Haiku reasoning engine (coming in next release).",
                credential_source="Backend (.env)",
                status="Coming Soon",
                has_api_key=False,
                active_model="claude-3-5-haiku-20241022",
                selected_model="claude-3-5-haiku-20241022",
                supported_models=["claude-3-5-haiku-20241022", "claude-3-7-sonnet-20250219"],
                is_default=False,
                is_fallback=False,
                is_coming_soon=True,
                is_active=False,
                priority_order=3,
            )
        )

        # 5. Ollama Local (Coming Soon)
        results.append(
            ProviderInfo(
                id="ollama",
                name="Ollama (Local)",
                tagline="Air-gapped on-premise execution.",
                description="Offline local daemon inference with zero data egress (coming in next release).",
                credential_source="Backend (.env)",
                status="Coming Soon",
                has_api_key=False,
                active_model="llama3.2",
                selected_model="llama3.2",
                supported_models=["llama3.2", "mistral", "deepseek-r1"],
                is_default=False,
                is_fallback=False,
                is_coming_soon=True,
                is_active=False,
                priority_order=4,
            )
        )

        return results

    # ------------------------------------------------------------------
    # Test Connection
    # ------------------------------------------------------------------

    def test_provider(
        self,
        provider_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        db: Any = None,
    ) -> ProviderTestResponse:
        """
        Verify connection using backend .env credentials without exposing keys.
        """
        if provider_id in ("openai", "anthropic", "ollama"):
            return ProviderTestResponse(
                provider_id=provider_id,
                status="Coming Soon",
                latency_ms=None,
                model=self._models.get(provider_id, "unknown"),
                message=f"{provider_id.capitalize()} support is currently marked as Coming Soon.",
                error_message=None,
            )

        adapter = self.adapters.get(provider_id)
        if not adapter:
            return ProviderTestResponse(
                provider_id=provider_id,
                status="Failed",
                latency_ms=None,
                model="unknown",
                message=f"Provider '{provider_id}' is not recognized.",
                error_message="Unknown provider ID.",
            )

        key = self._get_env_key(provider_id)
        if not key:
            return ProviderTestResponse(
                provider_id=provider_id,
                status="Not Configured",
                latency_ms=None,
                model=self._models[provider_id],
                message=f"No {provider_id.upper()}_API_KEY found in backend .env.",
                error_message="Missing credentials in .env",
            )

        active_model = model or self._models.get(provider_id) or adapter.default_model

        test_res = adapter.test_connection(
            model=active_model,
            api_key=key,
            timeout=10,
        )

        status = "Connected" if test_res["success"] else "Failed"

        self._test_cache[provider_id] = {
            "status": status,
            "latency_ms": test_res["latency_ms"],
            "tested_at": datetime.now(timezone.utc).isoformat(),
        }

        return ProviderTestResponse(
            provider_id=provider_id,
            status=status,
            latency_ms=test_res["latency_ms"],
            model=test_res["model"],
            message=test_res["message"],
            error_message=test_res["error"],
        )

    # ------------------------------------------------------------------
    # Model Selection & Priority
    # ------------------------------------------------------------------

    def update_provider_config(
        self,
        provider_id: str,
        selected_model: str | None = None,
        is_active: bool | None = None,
        **kwargs: Any,
    ) -> ProviderInfo:
        """Update active model in memory."""
        if selected_model and provider_id in self._models:
            self._models[provider_id] = selected_model.strip()

        return [p for p in self.list_providers() if p.id == provider_id][0]

    def set_priority_order(
        self,
        priority_order: list[str],
        active_provider: str | None = None,
        **kwargs: Any,
    ) -> list[str]:
        return ["gemini", "groq"]

    # ------------------------------------------------------------------
    # Generation Pipeline with Automatic Fallback
    # ------------------------------------------------------------------

    def execute_generation(
        self,
        messages: list[dict[str, str]],
        requested_provider: str | None = None,
        requested_model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        db: Any = None,
    ) -> dict[str, Any]:
        """
        Chat Pipeline Generation:
          1. Gemini (preferred, if GEMINI_API_KEY exists)
          2. Groq (automatic fallback, if GROQ_API_KEY exists)
          3. Else: Return "No LLM configured."
        """
        gemini_key = self._get_env_key("gemini")
        groq_key = self._get_env_key("groq")

        if not gemini_key and not groq_key:
            raise RuntimeError("No LLM configured.")

        # Candidate execution sequence
        candidates: list[tuple[str, str, str]] = []
        if gemini_key:
            candidates.append(("gemini", gemini_key, self._models["gemini"]))
        if groq_key:
            candidates.append(("groq", groq_key, self._models["groq"]))

        attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None

        for provider_id, key, default_model in candidates:
            adapter = self.adapters[provider_id]
            target_model = requested_model if (requested_model and provider_id == requested_provider) else default_model

            t0 = time.perf_counter()
            try:
                logger.info(
                    "Executing generation with %s (model: %s)",
                    provider_id.upper(),
                    target_model,
                )
                res = adapter.generate(
                    messages=messages,
                    model=target_model,
                    api_key=key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30,
                )

                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                attempts.append({
                    "provider": provider_id,
                    "model": target_model,
                    "status": "success",
                    "latency_ms": latency_ms,
                })
                res["fallback_occurred"] = (provider_id != candidates[0][0])
                res["attempts"] = attempts
                return res

            except Exception as exc:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                logger.warning(
                    "%s generation failed (%s). Triggering automatic fallback.",
                    provider_id.upper(),
                    exc,
                )
                attempts.append({
                    "provider": provider_id,
                    "model": target_model,
                    "status": "failed",
                    "latency_ms": latency_ms,
                    "error": str(exc),
                })
                last_error = exc

        raise RuntimeError(
            f"All configured LLM providers failed. Last error: {last_error}"
        )
