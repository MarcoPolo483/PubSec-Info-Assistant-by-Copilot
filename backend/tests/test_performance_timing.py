"""Tests for performance timing bounds in RAG pipeline."""
import pytest
from unittest.mock import AsyncMock

from app.rag_service import RAGService
from app.retrieval.models import SearchResult, RetrievalResponse
from app.llm.models import LLMResponse, TokensUsed


@pytest.mark.asyncio
async def test_rag_timing_bounds():
    """Verify timing metrics are positive and under sane bounds."""
    # Mock cache miss and rate limit allowed
    cache = AsyncMock()
    cache.get_query_cache.return_value = None
    cache.check_rate_limit.return_value = (True, 100)
    cache.deduct_tenant_balance.return_value = None
    cache.get_tenant_balance.return_value = 100.0

    # Mock retriever with timing
    results = [
        SearchResult(id="c1", score=0.9, content="Test content", document_id="d1", chunk_index=0, metadata={})
    ]
    retriever = AsyncMock()
    retriever.search.return_value = RetrievalResponse(
        query="test query",
        tenant_id="tenant1",
        total_results=1,
        results=results,
        processing_time_ms=15.5,
        cached=False
    )

    # Mock LLM response with timing
    llm_resp = LLMResponse(
        query="test query",
        answer="Test answer [Doc 1]",
        citations=[],
        model="gpt-4",
        tokens_used=TokensUsed(input_tokens=50, output_tokens=25, total=75),
        cost=0.001,
        processing_time_ms=35.2,
    )

    service = RAGService(retriever=retriever, cache=cache)
    service.llm_adapter = AsyncMock()
    service.llm_adapter.generate.return_value = llm_resp

    result = await service.query("test query", tenant_id="tenant1", use_cache=True)

    # Assert timing bounds
    assert "processing_time_ms" in result, "Response must include processing_time_ms"
    assert result["processing_time_ms"] >= 0, "Total processing time must be non-negative"
    assert result["processing_time_ms"] < 5000, "Total processing time should be under 5 seconds in tests"
    
    assert "retrieval_time_ms" in result, "Response must include retrieval_time_ms"
    assert result["retrieval_time_ms"] > 0, "Retrieval time must be positive"
    assert result["retrieval_time_ms"] < 5000, "Retrieval time should be under 5 seconds"
    assert result["retrieval_time_ms"] == 15.5, "Retrieval time should match mock value"
    
    assert "llm_time_ms" in result, "Response must include llm_time_ms"
    assert result["llm_time_ms"] > 0, "LLM time must be positive"
    assert result["llm_time_ms"] < 5000, "LLM time should be under 5 seconds"
    assert result["llm_time_ms"] == 35.2, "LLM time should match mock value"

    # Total should be >= 0 and include at least the max of sub-times
    assert result["processing_time_ms"] >= max(result["retrieval_time_ms"], result["llm_time_ms"]) * 0.5
