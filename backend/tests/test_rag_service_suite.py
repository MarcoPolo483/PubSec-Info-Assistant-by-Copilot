"""Tests for RAGService covering cache hit, happy path, and empty retrieval."""
import pytest
from unittest.mock import AsyncMock

from app.rag_service import RAGService
from app.retrieval.models import SearchResult, RetrievalResponse
from app.llm.models import LLMResponse, TokensUsed


@pytest.mark.asyncio
async def test_rag_cache_hit(monkeypatch):
    # Mock cache to return cached result
    cached = {"query": "q", "answer": "cached", "citations": [], "retrieval_results": 0, "cost": 0.0}
    cache = AsyncMock()
    cache.get_query_cache.return_value = cached

    # Stub retriever and llm adapter (unused in cache hit)
    retriever = AsyncMock()
    service = RAGService(retriever=retriever, cache=cache)

    result = await service.query("q", tenant_id="t", use_cache=True)
    assert result["cached"] is True
    assert result["answer"] == "cached"


@pytest.mark.asyncio
async def test_rag_empty_retrieval(monkeypatch):
    # Mock cache miss and rate limit allowed
    cache = AsyncMock()
    cache.get_query_cache.return_value = None
    cache.check_rate_limit.return_value = (True, 99)

    # Mock retriever returns empty results
    retriever = AsyncMock()
    retriever.search.return_value = RetrievalResponse(
        query="q",
        tenant_id="t",
        total_results=0,
        results=[],
        processing_time_ms=5.0,
    )

    service = RAGService(retriever=retriever, cache=cache)
    result = await service.query("q", tenant_id="t", use_cache=True)
    assert result["retrieval_results"] == 0
    assert "couldn't find any" in result["answer"].lower()


@pytest.mark.asyncio
async def test_rag_happy_path(monkeypatch):
    # Cache miss and rate limit allowed
    cache = AsyncMock()
    cache.get_query_cache.return_value = None
    cache.check_rate_limit.return_value = (True, 100)
    cache.deduct_tenant_balance.return_value = None
    cache.get_tenant_balance.return_value = 10.0

    # Retriever returns a couple of results
    results = [
        SearchResult(id="c1", score=0.9, content="A", document_id="d1", chunk_index=0, metadata={}),
        SearchResult(id="c2", score=0.8, content="B", document_id="d2", chunk_index=1, metadata={}),
    ]
    retriever = AsyncMock()
    retriever.search.return_value = RetrievalResponse(
        query="q",
        tenant_id="t",
        total_results=len(results),
        results=results,
        processing_time_ms=7.5,
    )

    # LLM adapter returns a response
    llm_resp = LLMResponse(
        query="q",
        answer="Answer [Doc 1]",
        citations=[],
        model="gpt-4",
        tokens_used=TokensUsed(input_tokens=100, output_tokens=50, total=150),
        cost=0.0001,
        processing_time_ms=25.0,
    )

    service = RAGService(retriever=retriever, cache=cache)
    # Monkeypatch adapter to our stub
    service.llm_adapter = AsyncMock()
    service.llm_adapter.generate.return_value = llm_resp

    result = await service.query("q", tenant_id="t", use_cache=True)

    assert result["retrieval_results"] == 2
    assert result["model"] == "gpt-4"
    assert result["tokens_used"]["total"] == 150
    assert result["tenant_balance"] == 10.0
