"""Tests for Retriever timing and threshold filtering behavior."""
import pytest
from unittest.mock import AsyncMock

from app.retrieval.retriever import Retriever
from app.retrieval.models import SearchQuery, SearchResult, RetrievalResponse

class StubVectorStore:
    async def search(self, tenant_id, query_vector, limit, score_threshold, filter_conditions):
        # Produce 5 results with descending scores
        return [
            {"id": f"r{i}", "score": s, "content": f"C{i}", "document_id": f"d{i}", "chunk_index": i, "metadata": {}}
            for i, s in enumerate([0.95, 0.85, 0.60, 0.40, 0.20])
        ]
    async def close(self):
        pass

@pytest.mark.asyncio
async def test_retriever_threshold_filters_partial(monkeypatch):
    # Force embedding generator to return a fixed vector
    mock_gen = AsyncMock()
    mock_gen.generate.return_value = [[0.1, 0.2, 0.3]]

    retriever = Retriever(vector_store=StubVectorStore(), use_openai_embeddings=False)
    retriever.embedding_generator = mock_gen

    query = SearchQuery(query='q', tenant_id='t', limit=10, score_threshold=0.6)
    resp = await retriever.search(query)
    assert resp.total_results == 3  # scores >= 0.6
    assert resp.processing_time_ms > 0
    # Sorted descending
    scores = [r.score for r in resp.results]
    assert scores == sorted(scores, reverse=True)
