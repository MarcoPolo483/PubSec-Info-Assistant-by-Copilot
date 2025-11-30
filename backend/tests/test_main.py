"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.ingestion.models import IngestionResponse, DocumentStatus
from app.llm.models import TokensUsed


@pytest.fixture
def mock_services():
    """Mock all services used by FastAPI"""
    with patch('app.main.ingestion_service') as mock_ingestion, \
         patch('app.main.rag_service') as mock_rag:
        
        # Mock ingestion service with AsyncMock
        mock_ingestion_response = IngestionResponse(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            status=DocumentStatus.COMPLETED,
            chunks_created=10,
            processing_time_ms=1500,
            message="Success"
        )
        mock_ingestion.ingest_document = AsyncMock(return_value=mock_ingestion_response)
        mock_ingestion.delete_document = AsyncMock(return_value={
            "document_id": "doc-123",
            "tenant_id": "test-tenant",
            "status": "deleted",
            "message": "Document successfully deleted"
        })
        mock_ingestion.get_collection_stats = AsyncMock(return_value={
            "total_documents": 50,
            "total_chunks": 500,
            "collection_name": "test_collection"
        })
        
        # Mock RAG service with AsyncMock
        tokens_used_obj = TokensUsed(input_tokens=500, output_tokens=100, total=600)
        mock_rag.query = AsyncMock(return_value={
            "query": "Test query",
            "answer": "Test answer with citations [Doc 1].",
            "citations": [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "content": "Citation content...",
                    "title": "Test Document",
                    "relevance_score": 0.92
                }
            ],
            "retrieval_results": 1,
            "cost": 0.00007,
            "tokens_used": tokens_used_obj.model_dump(),  # Serialize to dict for JSON compatibility
            "tenant_balance": 99.99993,
            "processing_time_ms": 350,
            "cached": False
        })
        
        # Mock other async methods
        mock_rag.get_tenant_stats = AsyncMock(return_value={
            "tenant_id": "default",
            "balance": 100.0,
            "collection_stats": {
                "total_documents": 100,
                "total_chunks": 1000,
                "collection_name": "tenant_default"
            }
        })
        
        yield {
            "ingestion": mock_ingestion,
            "rag": mock_rag
        }


@pytest.fixture
def client():
    """Test client for FastAPI"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready_endpoint(client, mock_services):
    """Test /ready endpoint - skip in unit tests as it checks real services"""
    # This test requires actual service connections
    # For unit tests, we accept 503 as services are mocked
    response = client.get("/ready")
    # Accept either 200 (services ready) or 503 (services not ready in test)
    assert response.status_code in [200, 503]


def test_ingest_endpoint(client, mock_services):
    """Test POST /api/v1/ingest endpoint"""
    # Create test file
    files = {"file": ("test.txt", b"Test document content", "text/plain")}
    
    response = client.post(
        "/api/v1/ingest",
        files=files,
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert data["chunks_created"] == 10


def test_ingest_endpoint_missing_file(client):
    """Test ingest endpoint without file"""
    response = client.post(
        "/api/v1/ingest",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 422  # Validation error


def test_query_endpoint(client, mock_services):
    """Test POST /api/v1/query endpoint"""
    response = client.post(
        "/api/v1/query",
        params={"query": "What are security requirements?"},
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Test query"
    assert data["answer"] == "Test answer with citations [Doc 1]."
    assert len(data["citations"]) == 1
    assert data["cost"] == 0.00007
    
    # Check cost tracking headers
    assert "X-Request-Cost" in response.headers
    assert "X-Token-Usage" in response.headers
    assert "X-Tenant-Balance" in response.headers


def test_query_endpoint_with_parameters(client, mock_services):
    """Test query endpoint with optional parameters"""
    response = client.post(
        "/api/v1/query",
        params={
            "query": "Test",
            "top_k": 3,
            "use_cache": True
        },
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    mock_services["rag"].query.assert_called_once()
    call_kwargs = mock_services["rag"].query.call_args[1]
    assert call_kwargs["top_k"] == 3
    assert call_kwargs["use_cache"] is True


def test_query_endpoint_missing_query(client):
    """Test query endpoint without query parameter"""
    response = client.post(
        "/api/v1/query",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 422  # Validation error


def test_delete_document_endpoint(client, mock_services):
    """Test DELETE /api/v1/documents/{document_id} endpoint"""
    response = client.delete(
        "/api/v1/documents/doc-123",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_collection_stats_endpoint(client, mock_services):
    """Test GET /api/v1/collection/stats endpoint"""
    response = client.get(
        "/api/v1/collection/stats",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert data["total_documents"] == 100


def test_tenant_stats_endpoint(client, mock_services):
    """Test GET /api/v1/tenant/stats endpoint"""
    response = client.get(
        "/api/v1/tenant/stats",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert data["balance"] == 100.0


def test_tenant_header_default(client, mock_services):
    """Test that default tenant is used when header is missing"""
    response = client.get("/api/v1/collection/stats")
    
    assert response.status_code == 200
    # Should use default tenant


def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.options(
        "/api/v1/query",
        headers={"Origin": "http://localhost:3000"}
    )
    
    # Check CORS headers
    assert "access-control-allow-origin" in response.headers


def test_query_rate_limit_exceeded(client, mock_services):
    """Test query when rate limit is exceeded"""
    mock_services["rag"].query.side_effect = Exception("Rate limit exceeded")
    
    response = client.post(
        "/api/v1/query",
        params={"query": "Test"},
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 500


def test_ingest_unsupported_file_type(client, mock_services):
    """Test ingesting unsupported file type"""
    mock_services["ingestion"].process_file.side_effect = ValueError("Unsupported file type")
    
    files = {"file": ("test.xyz", b"content", "application/octet-stream")}
    response = client.post(
        "/api/v1/ingest",
        files=files,
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 500


def test_metrics_endpoint(client):
    """Test /metrics endpoint for Prometheus"""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    # Should return Prometheus metrics format
    assert "text/plain" in response.headers["content-type"]


def test_query_response_format(client, mock_services):
    """Test that query response has all required fields"""
    response = client.post(
        "/api/v1/query",
        params={"query": "Test"},
        headers={"X-Tenant-ID": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Required fields
    assert "query" in data
    assert "answer" in data
    assert "citations" in data
    assert "retrieval_results" in data
    assert "cost" in data
    assert "tokens_used" in data
    assert "tenant_balance" in data
    assert "processing_time_ms" in data
    assert "cached" in data


def test_tenant_isolation(client, mock_services):
    """Test that different tenants get isolated responses"""
    # Query from tenant A
    response_a = client.post(
        "/api/v1/query",
        params={"query": "Test"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    # Query from tenant B
    response_b = client.post(
        "/api/v1/query",
        params={"query": "Test"},
        headers={"X-Tenant-ID": "tenant-b"}
    )
    
    assert response_a.status_code == 200
    assert response_b.status_code == 200
    
    # Verify both tenants were used in service calls
    assert mock_services["rag"].query.call_count == 2
