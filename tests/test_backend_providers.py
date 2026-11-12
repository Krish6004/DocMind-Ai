"""
Unit and integration tests for AI Provider Management Architecture.
Verifies production-ready backend .env loading, no key exposure,
Gemini default, Groq fallback, and Coming Soon placeholders.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.provider import ProviderInfo, ProviderListResponse


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_list_providers_endpoint(client: TestClient):
    """Verify listing all supported AI providers."""
    response = client.get("/api/v1/providers")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    provider_data = data["data"]

    assert "active_provider" in provider_data
    assert "priority_order" in provider_data
    providers = provider_data["providers"]

    # Verify all 5 providers exist
    provider_ids = [p["id"] for p in providers]
    assert "gemini" in provider_ids
    assert "groq" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "ollama" in provider_ids

    # Verify Gemini is default recommended
    gemini = next(p for p in providers if p["id"] == "gemini")
    assert gemini["name"] == "Google Gemini"
    assert gemini["is_default"] is True
    assert gemini["credential_source"] == "Backend (.env)"

    # Verify Groq is fallback
    groq = next(p for p in providers if p["id"] == "groq")
    assert groq["name"] == "Groq"
    assert groq["is_fallback"] is True
    assert groq["credential_source"] == "Backend (.env)"

    # Verify OpenAI, Claude, Ollama are Coming Soon
    for coming_soon_id in ("openai", "anthropic", "ollama"):
        p = next(x for x in providers if x["id"] == coming_soon_id)
        assert p["is_coming_soon"] is True
        assert p["status"] == "Coming Soon"

    # Verify raw keys are NEVER exposed
    for p in providers:
        assert "custom_api_key" not in p
        assert "api_key" not in p
        assert "key" not in p


def test_get_single_provider(client: TestClient):
    """Verify retrieving a specific provider."""
    response = client.get("/api/v1/providers/gemini")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == "gemini"
    assert data["data"]["name"] == "Google Gemini"
    assert data["data"]["credential_source"] == "Backend (.env)"


def test_test_provider_connection_groq(client: TestClient):
    """Verify testing Groq connection using backend .env."""
    response = client.post("/api/v1/providers/groq/test")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["provider_id"] == "groq"
    assert data["data"]["status"] == "Connected"
    assert data["data"]["latency_ms"] is not None


def test_update_provider_model(client: TestClient):
    """Verify updating provider selected model."""
    response = client.put(
        "/api/v1/providers/groq",
        json={"selected_model": "openai/gpt-oss-120b"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["selected_model"] == "openai/gpt-oss-120b"
    assert data["data"]["active_model"] == "openai/gpt-oss-120b"


def test_coming_soon_provider_test(client: TestClient):
    """Verify testing a Coming Soon provider returns clean placeholder response."""
    response = client.post("/api/v1/providers/openai/test")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "Coming Soon"
