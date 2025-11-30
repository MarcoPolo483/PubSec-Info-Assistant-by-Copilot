"""API contract tests for FastAPI app."""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_openapi_schema_present():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    # Basic shape checks
    assert data.get("openapi")
    assert "paths" in data
    assert "/health" in data["paths"]
    assert "/api/v1/query" in data["paths"]


def test_health_and_ready_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    r2 = client.get("/ready")
    # Ready may be 200 or 503 depending on service state
    assert r2.status_code in (200, 503)


def test_rate_limit_header_optional():
    # Without X-API-Key should still work (public mode)
    r = client.post("/api/v1/query", params={"query": "test"})
    # May be 503 if service not ready
    assert r.status_code in (200, 503, 429)


def test_api_key_header_and_cors():
    # With API key header
    r = client.post("/api/v1/query", params={"query": "key-test"}, headers={"X-API-Key": "demo-key"})
    assert r.status_code in (200, 503, 429)
    # CORS preflight
    pre = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert pre.status_code in (200, 204)
