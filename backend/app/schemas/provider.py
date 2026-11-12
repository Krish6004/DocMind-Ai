"""
Pydantic schemas and data contracts for AI Provider Management.
Production-ready schema loading exclusively from backend .env variables.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

ProviderStatusType = Literal["Connected", "Not Configured", "Coming Soon", "connected", "not_connected", "error"]


class ProviderInfo(BaseModel):
    """
    Public metadata and status for an AI Provider.
    API keys are NEVER exposed in this schema.
    """

    id: str = Field(..., description="Unique provider ID (gemini, groq, openai, anthropic, ollama)")
    name: str = Field(..., description="Display name of provider")
    tagline: str = Field(..., description="Short marketing or functional description")
    description: str = Field(..., description="Full descriptive overview")
    credential_source: str = Field(default="Backend (.env)", description="Source of API credentials")
    status: str = Field(..., description="'Connected', 'Not Configured', or 'Coming Soon'")
    has_api_key: bool = Field(default=False, description="Whether an API key is detected in .env")
    active_model: str = Field(..., description="Currently active model identifier")
    selected_model: str = Field(..., description="Same as active_model for compatibility")
    supported_models: list[str] = Field(default_factory=list, description="List of recognized models")
    is_default: bool = Field(default=False, description="Whether this is the preferred default provider")
    is_fallback: bool = Field(default=False, description="Whether this is the configured fallback provider")
    is_coming_soon: bool = Field(default=False, description="Whether this provider is reserved for future release")
    is_active: bool = Field(default=False, description="Whether this provider is currently active")
    priority_order: int = Field(default=0, description="Priority rank for fallback execution")
    last_latency_ms: float | None = Field(default=None, description="Latency in ms from latest health ping")
    last_tested_at: str | None = Field(default=None, description="ISO timestamp of last test")

    model_config = ConfigDict(from_attributes=True)


class ProviderListResponse(BaseModel):
    """List response for providers dashboard."""

    active_provider: str = Field(..., description="ID of primary active provider")
    fallback_provider: str | None = Field(default="groq", description="ID of fallback provider")
    priority_order: list[str] = Field(..., description="Ordered list of provider IDs for fallback")
    providers: list[ProviderInfo] = Field(..., description="List of configured providers")


class ProviderTestRequest(BaseModel):
    """Input payload to test a provider connection."""

    model: str | None = Field(default=None, description="Optional model to test")


class ProviderTestResponse(BaseModel):
    """Telemetry and status result from testing provider connection."""

    provider_id: str = Field(..., description="Provider tested")
    status: str = Field(..., description="Result status: 'Connected', 'Not Configured', or 'Failed'")
    latency_ms: float | None = Field(default=None, description="Round-trip ping latency in ms")
    model: str = Field(..., description="Model tested")
    message: str = Field(..., description="Human-readable result summary")
    error_message: str | None = Field(default=None, description="Error detail if test failed")


class ProviderUpdateRequest(BaseModel):
    """Payload to update a provider's model or active status."""

    selected_model: str | None = Field(default=None, description="Selected model identifier")
    is_active: bool | None = Field(default=None, description="Set as primary active provider")


class ProviderPriorityUpdateRequest(BaseModel):
    """Payload to reorder provider fallback priority."""

    priority_order: list[str] = Field(..., description="Ordered list of provider IDs")
    active_provider: str | None = Field(default=None, description="Optional primary active provider ID")
