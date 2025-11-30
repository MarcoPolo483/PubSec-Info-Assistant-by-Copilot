import pytest
from unittest.mock import AsyncMock

from app.retrieval.retriever import Retriever
from app.retrieval.models import SearchQuery
from app.ingestion import embeddings as embeddings_module


class DummyVectorStore:
    def __init__(self, results):
        self._results = results
        self.close = AsyncMock()

    async def search(self, tenant_id, query_vector, limit, score_threshold, filter_conditions):
        return self._results


class DummyEmbeddingGen:
    def __init__(self):
        self.generate = AsyncMock(return_value=[[0.0] * 10])


@pytest.mark.asyncio
async def test_retriever_empty_results(monkeypatch):
    monkeypatch.setattr(embeddings_module.EmbeddingGeneratorFactory, "create", lambda use_openai=True: DummyEmbeddingGen())
    vs = DummyVectorStore([])
    r = Retriever(vector_store=vs)
    q = SearchQuery(query="no results", tenant_id="t1", limit=5, score_threshold=0.2)
    resp = await r.search(q)
    assert resp.results == [] and resp.total_results == 0

@pytest.mark.asyncio
async def test_retriever_threshold_filters_all(monkeypatch):
    monkeypatch.setattr(embeddings_module.EmbeddingGeneratorFactory, "create", lambda use_openai=True: DummyEmbeddingGen())
    raw = [
        {"id": "a", "score": 0.1, "content": "low", "document_id": "docA"},
        {"id": "b", "score": 0.19, "content": "still low", "document_id": "docB"},
    ]
    vs = DummyVectorStore(raw)
    r = Retriever(vector_store=vs)
    q = SearchQuery(query="filter all", tenant_id="t1", limit=5, score_threshold=0.5)
    resp = await r.search(q)
    assert resp.results == [] and resp.total_results == 0

@pytest.mark.asyncio
async def test_retriever_limit_and_sort(monkeypatch):
    monkeypatch.setattr(embeddings_module.EmbeddingGeneratorFactory, "create", lambda use_openai=True: DummyEmbeddingGen())
    raw = [
        {"id": "a", "score": 0.3, "content": "c1", "document_id": "docA"},
        {"id": "b", "score": 0.9, "content": "c2", "document_id": "docB"},
        {"id": "c", "score": 0.6, "content": "c3", "document_id": "docC"},
        {"id": "d", "score": 0.7, "content": "c4", "document_id": "docD"},
    ]
    vs = DummyVectorStore(raw)
    r = Retriever(vector_store=vs)
    q = SearchQuery(query="sorted", tenant_id="t1", limit=2, score_threshold=0.0)
    resp = await r.search(q)
    # Should sort descending and limit to 2: scores 0.9, 0.7
    scores = [sr.score for sr in resp.results]
    assert scores == [0.9, 0.7]
    assert resp.total_results == 2
