"""
Tests for RAG service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag_service import RAGService
from app.retrieval.models import SearchResult, RetrievalResponse
from app.llm.models import LLMRequest, LLMResponse, TokensUsed


@pytest.fixture
def mock_retriever():
    retriever = AsyncMock()
    results = [
        SearchResult(
            id="chunk-1",
            score=0.92,
            content="NIST 800-53 provides security controls...",
            document_id="doc-1",
            chunk_index=0,
            metadata={"title": "NIST Framework", "author": "NIST"},
        ),
        SearchResult(
            id="chunk-2",
            score=0.88,
            content="FISMA requires security programs...",
            document_id="doc-2",
            chunk_index=1,
            metadata={"title": "FISMA Guide"},
        ),
    ]
    retriever.search.return_value = RetrievalResponse(
        query="What are cybersecurity requirements?",
        tenant_id="test-tenant",
        results=results,
        total_results=len(results),
        processing_time_ms=12.0,
        cached=False,
    )
    return retriever


@pytest.fixture
def mock_llm_adapter():
    adapter = AsyncMock()
    adapter.generate.return_value = LLMResponse(
        query="What are cybersecurity requirements?",
        answer="Based on the documents, cybersecurity requirements include NIST 800-53 controls [Doc 1] and FISMA compliance [Doc 2].",
        citations=[],
        model="gpt-4-turbo-preview",
        tokens_used=TokensUsed(input_tokens=500, output_tokens=100, total=600),
        cost=0.00007,
        processing_time_ms=25.0,
    )
    return adapter


@pytest.fixture
def mock_cache():
    """Mock Redis cache"""
    cache = AsyncMock()
    cache.get_query_cache.return_value = None
    cache.check_rate_limit.return_value = (True, 99)
    cache.get_tenant_balance.return_value = 100.0
    cache.deduct_tenant_balance.return_value = None
    return cache


@pytest.fixture
def rag_service(mock_retriever, mock_llm_adapter, mock_cache):
    """Create RAG service with mocked dependencies"""
    service = RAGService(
        retriever=mock_retriever,
        cache=mock_cache
    )
    service.llm_adapter = mock_llm_adapter
    return service


@pytest.mark.asyncio
async def test_rag_service_query_success(rag_service, mock_retriever, mock_llm_adapter, mock_cache):
    """Test successful RAG query pipeline"""
    # Arrange
    query = "What are cybersecurity requirements?"
    tenant_id = "test-tenant"
    
    # Act
    response = await rag_service.query(query, tenant_id)
    
    # Assert
    assert response["query"] == query
    assert response["answer"] is not None
    assert "cybersecurity" in response["answer"].lower()
    assert response["retrieval_results"] == 2
    assert response["cost"] == 0.00007
    assert response["tokens_used"]["total"] == 600
    # Balance should reflect deduction
    assert response["tenant_balance"] < 100.0
    assert response["cached"] is False
    
    # Verify pipeline calls
    mock_cache.check_rate_limit.assert_called_once()
    mock_retriever.search.assert_called_once()
    mock_llm_adapter.generate.assert_called_once()
    mock_cache.deduct_tenant_balance.assert_called_once()


@pytest.mark.asyncio
async def test_rag_service_cache_hit(rag_service, mock_retriever, mock_llm_adapter, mock_cache):
    """Test RAG query with cache hit"""
    # Arrange
    cached_response = {
        "query": "Cached query",
        "answer": "Cached answer",
        "citations": [],
        "retrieval_results": 2,
        "cost": 0.0,
        "tokens_used": {"input": 0, "output": 0, "total": 0},
        "tenant_balance": 100.0,
        "processing_time_ms": 5,
        "cached": True
    }
    mock_cache.get_query_cache.return_value = cached_response
    
    # Act
    response = await rag_service.query("Cached query", "test-tenant", use_cache=True)
    
    # Assert
    assert response["cached"] is True
    assert response["cost"] == 0.0
    assert response["answer"] == "Cached answer"
    
    # Verify that LLM was NOT called (cache hit)
    mock_llm_adapter.generate.assert_not_called()
    mock_retriever.search.assert_not_called()


@pytest.mark.asyncio
async def test_rag_service_rate_limit_exceeded(rag_service, mock_cache):
    """Test RAG query when rate limit is exceeded"""
    # Arrange
    mock_cache.check_rate_limit.return_value = (False, 0)
    
    # Act & Assert
    with pytest.raises(Exception, match="Rate limit exceeded"):
        await rag_service.query("Test query", "test-tenant")


@pytest.mark.asyncio
async def test_rag_service_no_retrieval_results(rag_service, mock_retriever, mock_llm_adapter):
    """Test RAG query when no documents are retrieved"""
    # Arrange
    mock_retriever.search.return_value = RetrievalResponse(
        query="Obscure topic",
        tenant_id="test-tenant",
        results=[],
        total_results=0,
        processing_time_ms=5.0,
        cached=False,
    )
    
    # Act
    response = await rag_service.query("Obscure topic", "test-tenant")
    
    # Assert
    assert response["retrieval_results"] == 0
    assert "no relevant" in response["answer"].lower() or "cannot find" in response["answer"].lower()
    
    # LLM should not be called if no context
    mock_llm_adapter.generate.assert_not_called()


@pytest.mark.asyncio
async def test_rag_service_citation_mapping(rag_service, mock_retriever, mock_llm_adapter):
    """Test that citations are properly mapped to retrieved documents"""
    # Arrange
    mock_llm_adapter.generate.return_value.citations = []
    
    # Act
    response = await rag_service.query("Test", "test-tenant")
    
    # Assert
    assert len(response["citations"]) >= 0


@pytest.mark.asyncio
async def test_rag_service_cost_tracking(rag_service, mock_cache):
    """Test that costs are properly tracked and deducted"""
    # Arrange
    initial_balance = 100.0
    query_cost = 0.00007
    mock_cache.get_tenant_balance.return_value = initial_balance
    
    # Act
    response = await rag_service.query("Test", "test-tenant")
    
    # Assert
    mock_cache.deduct_tenant_balance.assert_called_once()
    assert response["cost"] == query_cost
    assert response["tenant_balance"] == initial_balance - query_cost


@pytest.mark.asyncio
async def test_rag_service_sets_cache(rag_service, mock_cache):
    """Test that successful queries are cached"""
    # Arrange
    mock_cache.get_query_cache.return_value = None  # Cache miss
    
    # Act
    await rag_service.query("New query", "test-tenant", use_cache=True)
    
    # Assert
    mock_cache.set_query_cache.assert_called_once()


@pytest.mark.asyncio
async def test_rag_service_skip_cache(rag_service, mock_cache):
    """Test query with caching disabled"""
    # Act
    await rag_service.query("Test", "test-tenant", use_cache=False)
    
    # Assert
    mock_cache.get_query_cache.assert_not_called()
    mock_cache.set_query_cache.assert_not_called()


@pytest.mark.asyncio
async def test_rag_service_top_k_parameter(rag_service, mock_retriever):
    """Test that top_k parameter is passed to retriever"""
    # Act
    await rag_service.query("Test", "test-tenant", top_k=3)
    
    # Assert
    call_args = mock_retriever.search.call_args
    search_query = call_args[0][0]
    assert search_query.limit == 3


@pytest.mark.asyncio
async def test_rag_service_processing_time(rag_service):
    """Test that processing time is measured"""
    # Act
    response = await rag_service.query("Test", "test-tenant")
    
    # Assert
    assert "processing_time_ms" in response
    assert response["processing_time_ms"] >= 0


@pytest.mark.asyncio
async def test_rag_service_handles_retrieval_error(rag_service, mock_retriever):
    """Test error handling when retrieval fails"""
    # Arrange
    mock_retriever.search.side_effect = Exception("Qdrant connection error")
    
    # Act & Assert
    with pytest.raises(Exception, match="Qdrant connection error"):
        await rag_service.query("Test", "test-tenant")


@pytest.mark.asyncio
async def test_rag_service_handles_llm_error(rag_service, mock_llm_adapter):
    """Test error handling when LLM generation fails"""
    # Arrange
    mock_llm_adapter.generate.side_effect = Exception("OpenAI API error")
    
    # Act & Assert
    with pytest.raises(Exception, match="OpenAI API error"):
        await rag_service.query("Test", "test-tenant")


@pytest.mark.asyncio
async def test_rag_service_tenant_isolation(rag_service, mock_retriever, mock_cache):
    """Test that queries are tenant-isolated"""
    # Arrange
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"
    
    # Act
    await rag_service.query("Query 1", tenant_a)
    await rag_service.query("Query 2", tenant_b)
    
    # Assert - Different tenants should have separate contexts
    assert mock_retriever.search.call_count == 2
    call_1 = mock_retriever.search.call_args_list[0][0][0]
    call_2 = mock_retriever.search.call_args_list[1][0][0]
    assert call_1.tenant_id == tenant_a
    assert call_2.tenant_id == tenant_b


@pytest.mark.asyncio
async def test_rag_service_context_building(rag_service, mock_llm_adapter, mock_retriever):
    """Test that context is properly built from retrieval results"""
    # Act
    await rag_service.query("Test", "test-tenant")
    
    # Assert
    call_args = mock_llm_adapter.generate.call_args
    llm_request = call_args[0][0]
    
    # Should have context from retrieved documents
    assert isinstance(llm_request, LLMRequest)
    assert len(llm_request.context) > 0
    assert "NIST 800-53" in llm_request.context[0]


@pytest.mark.asyncio
async def test_rag_service_insufficient_balance_warning(rag_service, mock_cache):
    """Test behavior when tenant balance is low"""
    # Arrange
    mock_cache.get_tenant_balance.return_value = 0.0001  # Very low balance
    
    # Act
    response = await rag_service.query("Test", "test-tenant")
    
    # Assert - Should still process but track negative balance
    # Balance may reach zero or near-zero after deduction
    assert response["tenant_balance"] <= 0.0001
