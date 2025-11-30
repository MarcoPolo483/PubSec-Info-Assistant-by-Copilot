"""FastAPI endpoint tests with dependency overrides."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app, rag_service, ingestion_service
from app.rag_service import RAGService
from app.llm.models import LLMResponse
from app.retrieval.models import SearchResult, RetrievalResponse


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def mock_rag_service():
    service = AsyncMock(spec=RAGService)
    results = [
        SearchResult(
            id="chunk-1",
            score=0.9,
            content="Zero trust requires continuous verification.",
            document_id="doc-1",
            chunk_index=0,
            metadata={"title": "ZT Guide"},
        )
    ]
    retrieval_response = RetrievalResponse(
        query="What is zero trust?",
        tenant_id="tenant-a",
        results=results,
        total_results=1,
        processing_time_ms=10.0,
        cached=False,
    )
    llm_response = {
        "query": "What is zero trust?",
        "answer": "Zero trust is a security model [Doc 1].",
        "citations": [],
        "retrieval_results": 1,
        "model": "gpt-test",
        "tokens_used": {"input": 100, "output": 50, "total": 150},
        "cost": 0.001,
        "tenant_balance": 9999.0,
        "cached": False,
        "processing_time_ms": 12.0,
        "retrieval_time_ms": 5.0,
        "llm_time_ms": 7.0,
    }
    service.query.return_value = llm_response
    service.get_tenant_stats.return_value = {"tenant_id": "tenant-a", "balance": 9999.0, "collection_stats": {}}
    return service


@pytest.fixture(autouse=True)
def override_services(mock_rag_service):
    # Override global rag_service & ingestion_service for tests
    import app.main as main_mod
    main_mod.rag_service = mock_rag_service
    main_mod.ingestion_service = AsyncMock()
    yield
    main_mod.rag_service = None
    main_mod.ingestion_service = None


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_ready(client):
    # ingestion_service overridden to mock so ready
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_query_endpoint(client):
    r = client.post("/api/v1/query", params={"query": "What is zero trust?"})
    assert r.status_code == 200
    body = r.json()
    assert body["retrieval_results"] == 1
    assert "Zero trust" in body["answer"]
    assert r.headers.get("X-Request-Cost") is not None


def test_tenant_stats(client):
    r = client.get("/api/v1/tenant/stats")
    assert r.status_code == 200
    assert r.json()["tenant_id"] == "tenant-a"


def test_rate_limit_headers(client):
    r = client.post("/api/v1/query", params={"query": "What is zero trust?", "top_k": 1})
    assert "X-Request-Cost" in r.headers
    assert "X-Token-Usage" in r.headers


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["health"] == "/health"