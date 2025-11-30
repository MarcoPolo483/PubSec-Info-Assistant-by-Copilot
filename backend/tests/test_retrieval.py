"""Updated tests for Retriever matching current implementation."""
from unittest.mock import AsyncMock, patch

import pytest

from app.retrieval.retriever import Retriever
from app.retrieval.models import SearchQuery


@pytest.fixture
def mock_embeddings():
    gen = AsyncMock()
    gen.generate.return_value = [[0.05] * 10]
    return gen


@pytest.fixture
def mock_vector_store():
    store = AsyncMock()
    return store


@pytest.fixture
def retriever(mock_embeddings, mock_vector_store):
    with patch("app.retrieval.retriever.EmbeddingGeneratorFactory.create", return_value=mock_embeddings):
        return Retriever(vector_store=mock_vector_store, use_openai_embeddings=False)


@pytest.mark.asyncio
async def test_search_success(retriever, mock_embeddings, mock_vector_store):
    query = SearchQuery(query="FedRAMP controls", tenant_id="tenant-a", limit=3, score_threshold=0.1)
    mock_vector_store.search.return_value = [
        {
            "id": 1,
            "score": 0.91,
            "content": "FedRAMP requires continuous monitoring.",
            "document_id": "doc-1",
            "chunk_index": 0,
            "metadata": {"source": "fedramp-guide"},
        },
        {
            "id": 2,
            "score": 0.85,
            "content": "FedRAMP impact levels: Low, Moderate, High.",
            "document_id": "doc-2",
            "chunk_index": 1,
            "metadata": {},
        },
    ]
    response = await retriever.search(query)
    assert response.total_results == 2
    assert response.results[0].score == 0.91
    assert response.processing_time_ms >= 0
    mock_embeddings.generate.assert_called_once()
    mock_vector_store.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_no_results(retriever, mock_vector_store):
    query = SearchQuery(query="No hits", tenant_id="tenant-a")
    mock_vector_store.search.return_value = []
    response = await retriever.search(query)
    assert response.total_results == 0
    assert response.results == []


@pytest.mark.asyncio
async def test_search_error_embedding(retriever, mock_embeddings):
    query = SearchQuery(query="Trigger error", tenant_id="tenant-a")
    mock_embeddings.generate.side_effect = Exception("Embedding failure")
    with pytest.raises(Exception, match="Embedding failure"):
        await retriever.search(query)


@pytest.mark.asyncio
async def test_search_error_vector_store(retriever, mock_vector_store):
    query = SearchQuery(query="Trigger VS error", tenant_id="tenant-a")
    mock_vector_store.search.side_effect = Exception("Vector store down")
    with pytest.raises(Exception, match="Vector store down"):
        await retriever.search(query)


@pytest.mark.asyncio
async def test_search_respects_limit(retriever, mock_vector_store):
    query = SearchQuery(query="Limit test", tenant_id="tenant-a", limit=2)
    mock_vector_store.search.return_value = [
        {"id": i, "score": 0.5 + i / 10, "content": f"C{i}", "document_id": f"d{i}", "chunk_index": i, "metadata": {}}
        for i in range(5)
    ]
    response = await retriever.search(query)
    assert response.total_results == 2


@pytest.mark.asyncio
async def test_search_score_threshold_filters(retriever, mock_vector_store):
    query = SearchQuery(query="Threshold", tenant_id="tenant-a", score_threshold=0.8, limit=10)
    mock_vector_store.search.return_value = [
        {"id": 1, "score": 0.95, "content": "High", "document_id": "d1", "chunk_index": 0, "metadata": {}},
        {"id": 2, "score": 0.60, "content": "Low", "document_id": "d2", "chunk_index": 1, "metadata": {}},
        {"id": 3, "score": 0.82, "content": "Med", "document_id": "d3", "chunk_index": 2, "metadata": {}},
    ]
    response = await retriever.search(query)
    scores = [r.score for r in response.results]
    assert all(s >= 0.8 for s in scores)
    assert 0.60 not in scores


@pytest.mark.asyncio
async def test_close_calls_vector_store_close(retriever, mock_vector_store):
    await retriever.close()
    mock_vector_store.close.assert_called_once()
