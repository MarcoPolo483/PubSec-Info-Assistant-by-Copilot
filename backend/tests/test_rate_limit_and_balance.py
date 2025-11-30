"""Tests for rate limit exhaustion and negative tenant balance handling."""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app, MAX_REQUESTS_PER_WINDOW, _rate_window
from app.rag_service import RAGService
from app.llm.models import LLMResponse, TokensUsed
from app.retrieval.models import SearchResult, RetrievalResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_rate_limit_exhaustion(monkeypatch, client):
    # Populate window with current timestamps within rate window
    from time import time
    api_key = 'k'
    now = time()
    dq = _rate_window[api_key]
    dq.clear()
    for _ in range(MAX_REQUESTS_PER_WINDOW + 5):
        dq.append(now)  # all within window so pruning won't remove

    # Ensure rag_service global is set to avoid 503 if dependency order changes
    import app.main as main_mod
    if main_mod.rag_service is None:
        stub = AsyncMock()
        stub.query.return_value = {"query": "test", "answer": "stub", "citations": []}
        main_mod.rag_service = stub

    resp = client.post('/api/v1/query', params={'query': 'test'}, headers={'X-API-Key': api_key})
    assert resp.status_code == 429, resp.text
    assert 'Rate limit' in resp.text


@pytest.mark.asyncio
async def test_negative_balance(monkeypatch):
    # Mock cache so balance deduction drives below zero
    cache = AsyncMock()
    cache.get_query_cache.return_value = None
    cache.check_rate_limit.return_value = (True, 10)
    # Start with tiny balance
    cache.get_tenant_balance.return_value = -5.0
    cache.deduct_tenant_balance.return_value = -10.0

    # Mock retriever results
    retriever = AsyncMock()
    retriever.search.return_value = RetrievalResponse(
        query='q', tenant_id='t', total_results=1,
        results=[SearchResult(id='c1', score=0.9, content='A', document_id='d1', chunk_index=0, metadata={})],
        processing_time_ms=5.0, cached=False
    )

    # Mock LLM adapter response with cost
    llm_resp = LLMResponse(
        query='q', answer='Answer', citations=[], model='gpt-4',
        tokens_used=TokensUsed(input_tokens=10, output_tokens=5, total=15),
        cost=50.0, processing_time_ms=10.0
    )
    service = RAGService(retriever=retriever, cache=cache)
    service.llm_adapter = AsyncMock()
    service.llm_adapter.generate.return_value = llm_resp

    result = await service.query('q', tenant_id='t', use_cache=True)
    assert result['tenant_balance'] <= 0.0
