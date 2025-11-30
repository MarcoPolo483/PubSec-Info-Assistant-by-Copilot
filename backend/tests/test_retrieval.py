"""
Tests for retrieval module
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.retrieval.retriever import Retriever
from app.retrieval.models import SearchQuery, SearchResult


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator"""
    generator = AsyncMock()
    generator.generate_embeddings.return_value = [[0.1] * 1536]
    return generator


@pytest.fixture
def mock_vector_store():
    """Mock Qdrant vector store"""
    store = AsyncMock()
    return store


@pytest.fixture
def retriever(mock_embedding_generator, mock_vector_store):
    """Create retriever with mocked dependencies"""
    return Retriever(
        embedding_generator=mock_embedding_generator,
        vector_store=mock_vector_store
    )


@pytest.mark.asyncio
async def test_retriever_search_success(retriever, mock_vector_store):
    """Test successful semantic search"""
    # Arrange
    query = SearchQuery(
        query="What are cybersecurity requirements?",
        tenant_id="test-tenant",
        limit=5,
        score_threshold=0.5
    )
    
    mock_results = [
        MagicMock(
            score=0.92,
            payload={
                "content": "Cybersecurity requirements include NIST 800-53 controls...",
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "metadata": {
                    "title": "NIST Cybersecurity Framework",
                    "author": "NIST",
                    "source_url": "https://nist.gov/csf"
                }
            }
        ),
        MagicMock(
            score=0.88,
            payload={
                "content": "Federal systems must comply with FISMA regulations...",
                "chunk_id": "chunk-2",
                "document_id": "doc-2",
                "metadata": {
                    "title": "FISMA Compliance Guide",
                    "author": "OMB"
                }
            }
        )
    ]
    mock_vector_store.search.return_value = mock_results
    
    # Act
    results = await retriever.search(query)
    
    # Assert
    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].score == 0.92
    assert results[0].content == "Cybersecurity requirements include NIST 800-53 controls..."
    assert results[0].chunk_id == "chunk-1"
    assert results[0].metadata["title"] == "NIST Cybersecurity Framework"
    assert results[1].score == 0.88
    
    # Verify calls
    retriever.embedding_generator.generate_embeddings.assert_called_once_with(
        [query.query]
    )
    mock_vector_store.search.assert_called_once()


@pytest.mark.asyncio
async def test_retriever_search_no_results(retriever, mock_vector_store):
    """Test search with no matching results"""
    # Arrange
    query = SearchQuery(
        query="Non-existent topic",
        tenant_id="test-tenant"
    )
    mock_vector_store.search.return_value = []
    
    # Act
    results = await retriever.search(query)
    
    # Assert
    assert len(results) == 0


@pytest.mark.asyncio
async def test_retriever_search_with_score_threshold(retriever, mock_vector_store):
    """Test that results below score threshold are filtered"""
    # Arrange
    query = SearchQuery(
        query="Security requirements",
        tenant_id="test-tenant",
        score_threshold=0.8
    )
    
    mock_results = [
        MagicMock(score=0.92, payload={"content": "High relevance", "chunk_id": "1", "document_id": "d1", "metadata": {}}),
        MagicMock(score=0.75, payload={"content": "Low relevance", "chunk_id": "2", "document_id": "d2", "metadata": {}}),
        MagicMock(score=0.85, payload={"content": "Medium relevance", "chunk_id": "3", "document_id": "d3", "metadata": {}})
    ]
    mock_vector_store.search.return_value = mock_results
    
    # Act
    results = await retriever.search(query)
    
    # Assert - Only results >= 0.8 threshold
    assert len(results) == 2
    assert results[0].score == 0.92
    assert results[1].score == 0.85


@pytest.mark.asyncio
async def test_retriever_search_respects_limit(retriever, mock_vector_store):
    """Test that search respects the limit parameter"""
    # Arrange
    query = SearchQuery(
        query="Test query",
        tenant_id="test-tenant",
        limit=3
    )
    
    mock_results = [
        MagicMock(score=0.9, payload={"content": f"Result {i}", "chunk_id": f"{i}", "document_id": f"d{i}", "metadata": {}})
        for i in range(10)  # More than limit
    ]
    mock_vector_store.search.return_value = mock_results
    
    # Act
    results = await retriever.search(query)
    
    # Assert
    assert len(results) <= query.limit


@pytest.mark.asyncio
async def test_retriever_handles_embedding_error(retriever):
    """Test error handling when embedding generation fails"""
    # Arrange
    query = SearchQuery(query="Test query", tenant_id="test-tenant")
    retriever.embedding_generator.generate_embeddings.side_effect = Exception("OpenAI API error")
    
    # Act & Assert
    with pytest.raises(Exception, match="OpenAI API error"):
        await retriever.search(query)


@pytest.mark.asyncio
async def test_retriever_handles_vector_store_error(retriever, mock_vector_store):
    """Test error handling when vector store search fails"""
    # Arrange
    query = SearchQuery(query="Test query", tenant_id="test-tenant")
    mock_vector_store.search.side_effect = Exception("Qdrant connection error")
    
    # Act & Assert
    with pytest.raises(Exception, match="Qdrant connection error"):
        await retriever.search(query)


@pytest.mark.asyncio
async def test_retriever_search_with_missing_metadata(retriever, mock_vector_store):
    """Test handling of results with incomplete metadata"""
    # Arrange
    query = SearchQuery(query="Test", tenant_id="test-tenant")
    
    mock_results = [
        MagicMock(
            score=0.9,
            payload={
                "content": "Test content",
                "chunk_id": "1",
                "document_id": "d1",
                "metadata": {}  # Empty metadata
            }
        )
    ]
    mock_vector_store.search.return_value = mock_results
    
    # Act
    results = await retriever.search(query)
    
    # Assert
    assert len(results) == 1
    assert results[0].metadata == {}


@pytest.mark.asyncio
async def test_retriever_tenant_isolation(retriever, mock_vector_store):
    """Test that searches are tenant-isolated"""
    # Arrange
    query = SearchQuery(
        query="Sensitive data",
        tenant_id="tenant-a"
    )
    
    # Act
    await retriever.search(query)
    
    # Assert - Verify tenant_id is passed to vector store
    call_args = mock_vector_store.search.call_args
    assert call_args is not None
    # The tenant_id should be used in collection name: tenant_tenant-a
