"""
Unit tests for DocMind AI FastAPI Backend health and root endpoints.

Tests:
  - GET /health
  - GET /api/v1/health
  - GET /
  - GET /api/v1/
  - OpenAPI & Swagger UI endpoints (/docs, /redoc, /api/v1/openapi.json)
  - CORS header validation
  - Custom error handling and 404 responses
  - Dependency injection overrides

Run with: pytest tests/test_backend_health.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import DocMindAPIException, ResourceNotFoundException
from backend.app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient with lifecycle events."""
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# 1. Health Endpoint Tests
# ---------------------------------------------------------------------------


def test_health_endpoint_root(client: TestClient):
    """Verify top-level GET /health responds with 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "services" in data
    assert data["services"]["api"] == "operational"
    assert data["services"]["ai_engine"] == "ready"


def test_health_endpoint_v1(client: TestClient):
    """Verify versioned GET /api/v1/health responds with 200 OK and matching schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["api"] == "operational"


# ---------------------------------------------------------------------------
# 2. Root Endpoint Tests
# ---------------------------------------------------------------------------


def test_root_endpoint(client: TestClient):
    """Verify GET / returns application information and navigation URLs."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "DocMind AI Backend"
    assert "version" in data
    assert "documentation" in data
    assert data["documentation"]["swagger_ui"] == "/docs"
    assert data["documentation"]["redoc"] == "/redoc"
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/health"


def test_api_v1_root_endpoint(client: TestClient):
    """Verify GET /api/v1/ returns API root information."""
    response = client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DocMind AI Backend"


# ---------------------------------------------------------------------------
# 3. Documentation & Swagger UI Tests
# ---------------------------------------------------------------------------


def test_swagger_ui_available(client: TestClient):
    """Verify Swagger UI is reachable at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_redoc_ui_available(client: TestClient):
    """Verify ReDoc documentation is reachable at /redoc."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_json_schema(client: TestClient):
    """Verify OpenAPI 3 JSON specification is served and valid."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert schema["info"]["title"] == "DocMind AI Backend"
    assert "/health" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]


# ---------------------------------------------------------------------------
# 4. CORS Header Tests
# ---------------------------------------------------------------------------


def test_cors_headers(client: TestClient):
    """Verify CORS middleware attaches appropriate Access-Control headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# ---------------------------------------------------------------------------
# 5. Error Handling Tests
# ---------------------------------------------------------------------------


def test_not_found_error_payload(client: TestClient):
    """Verify 404 on undefined routes returns structured JSON error envelope."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["status_code"] == 404


def test_custom_domain_exception(client: TestClient):
    """Verify custom DocMindAPIException returns formatted error payload."""
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/test-custom-error")
    def trigger_error():
        raise ResourceNotFoundException(message="Custom test resource missing")

    app.include_router(test_router)

    try:
        response = client.get("/test-custom-error")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "resource_not_found"
        assert data["error"]["message"] == "Custom test resource missing"
    finally:
        # Clean up route from app
        app.routes[:] = [r for r in app.routes if getattr(r, "path", "") != "/test-custom-error"]


# ---------------------------------------------------------------------------
# 6. Dependency Injection Override Tests
# ---------------------------------------------------------------------------


def test_settings_dependency_override(client: TestClient):
    """Verify dependency injection supports clean testing overrides."""

    def custom_settings():
        return Settings(PROJECT_NAME="Mocked DocMind Backend", VERSION="9.9.9")

    app.dependency_overrides[get_settings] = custom_settings
    try:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == "9.9.9"
    finally:
        app.dependency_overrides.clear()
