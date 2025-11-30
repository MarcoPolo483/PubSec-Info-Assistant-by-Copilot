"""Tests for LLM adapters cost & citation extraction."""
import pytest
from unittest.mock import AsyncMock, patch

from app.llm.adapters import OpenAIAdapter, LLMAdapterFactory
from app.llm.models import LLMRequest
from app.retrieval.models import SearchResult


@pytest.mark.asyncio
async def test_openai_adapter_basic_generation(monkeypatch):
    fake_client = AsyncMock()
    fake_response = AsyncMock()
    fake_choice = AsyncMock()
    fake_choice.message.content = "Answer referencing [Doc 1] clearly."
    fake_response.choices = [fake_choice]
    fake_response.usage = AsyncMock(prompt_tokens=300, completion_tokens=120, total_tokens=420)
    fake_client.chat.completions.create.return_value = fake_response

    with patch("app.llm.adapters.AsyncOpenAI", return_value=fake_client):
        adapter = OpenAIAdapter(api_key="sk-test", model="gpt-test")
        request = LLMRequest(
            query="Explain zero trust",
            tenant_id="t1",
            context=["Zero trust architecture mandates continuous verification."],
            temperature=0.2,
            max_tokens=256,
        )
        search_results = [
            SearchResult(
                id="c1",
                score=0.9,
                content="Zero trust architecture mandates continuous verification.",
                document_id="doc-1",
                chunk_index=0,
                metadata={"title": "Zero Trust Whitepaper"},
            )
        ]
        response = await adapter.generate(request, search_results=search_results)
        assert response.tokens_used["total"] == 420
        assert response.cost >= 0.0
        assert len(response.citations) == 1
        assert response.citations[0].document_id == "doc-1"


def test_llm_factory_openai():
    adapter = LLMAdapterFactory.create(provider="openai", model="gpt-x")
    assert isinstance(adapter, OpenAIAdapter)


def test_llm_factory_invalid():
    with pytest.raises(ValueError):
        LLMAdapterFactory.create(provider="unsupported")