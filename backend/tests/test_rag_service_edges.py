import pytest
from unittest.mock import AsyncMock

from app.rag_service import RAGService
from app.retrieval.models import SearchResult, RetrievalResponse
from app.llm.models import LLMResponse
from app import config as config_module
from app.ingestion import embeddings as embeddings_module
from app.llm import adapters as adapters_module


@pytest.mark.asyncio
async def test_rag_service_cache_hit(monkeypatch):
    # Prepare cached result
    cached = {
        "query": "cached q",
        "answer": "cached answer",
        "citations": [],
        "retrieval_results": 2,
        "cost": 0.1234,
        "tenant_balance": 9999.0,
        "tokens_used": {"input": 10, "output": 5},
    }

    # Avoid real embedding and LLM adapters
    embeddings_module.EmbeddingGeneratorFactory.create = lambda use_openai=True: AsyncMock(generate=lambda texts, cfg: [[0.0]*10])
    dummy_llm = AsyncMock()
    dummy_llm.generate = AsyncMock(side_effect=AssertionError("LLM should not be called for cache hit"))
    adapters_module.LLMAdapterFactory.create = lambda provider="openai", api_key=None, model=None: dummy_llm
    service = RAGService()
    # Monkeypatch internal components
    service.cache.get_query_cache = AsyncMock(return_value=cached)
    service.cache.set_query_cache = AsyncMock()
    service.retriever.search = AsyncMock()
    service.llm_adapter.generate = AsyncMock()

    resp = await service.query("cached q", tenant_id="t1", use_cache=True)

    assert resp["cached"] is True
    assert resp["answer"] == "cached answer"
    # Ensure retriever & llm were not called
    service.retriever.search.assert_not_called()
    service.llm_adapter.generate.assert_not_called()


@pytest.mark.asyncio
async def test_rag_service_cost_tracking_disabled(monkeypatch):
    # Disable cost tracking
    original = config_module.settings.cost_tracking_enabled
    config_module.settings.cost_tracking_enabled = False

    embeddings_module.EmbeddingGeneratorFactory.create = lambda use_openai=True: AsyncMock(generate=lambda texts, cfg: [[0.0]*10])
    dummy_llm = AsyncMock()
    # Will be invoked
    adapters_module.LLMAdapterFactory.create = lambda provider="openai", api_key=None, model=None: dummy_llm
    service = RAGService()

    # Mock retriever to return results
    search_results = [
        SearchResult(id="c1", score=0.9, content="alpha", document_id="d1", chunk_index=0, metadata={}),
        SearchResult(id="c2", score=0.8, content="beta", document_id="d2", chunk_index=1, metadata={}),
    ]
    retrieval_response = RetrievalResponse(
        query="q",
        tenant_id="t1",
        results=search_results,
        total_results=len(search_results),
        processing_time_ms=12.3,
        cached=False,
    )
    service.retriever.search = AsyncMock(return_value=retrieval_response)

    # Mock LLM adapter
    llm_response = LLMResponse(
        query="q",
        answer="generated answer",
        citations=[],
        model="gpt-test",
        tokens_used={"input": 20, "output": 10, "total": 30},
        cost=0.42,
        processing_time_ms=25.0,
    )
    service.llm_adapter.generate = AsyncMock(return_value=llm_response)

    # Spy on balance methods
    service.cache.deduct_tenant_balance = AsyncMock()
    service.cache.get_tenant_balance = AsyncMock(return_value=555.0)

    resp = await service.query("q", tenant_id="t1", use_cache=False, top_k=2)

    assert resp["cached"] is False
    assert resp["answer"] == "generated answer"
    assert resp["tenant_balance"] == 0.0  # cost tracking disabled branch
    service.cache.deduct_tenant_balance.assert_not_called()
    # Restore flag
    config_module.settings.cost_tracking_enabled = original

    # (restored above)
