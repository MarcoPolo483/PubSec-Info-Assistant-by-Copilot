"""Tests for OpenAIEmbeddingGenerator retry behavior and factory skip paths."""
import pytest
from unittest.mock import AsyncMock, patch

from app.ingestion.embeddings import OpenAIEmbeddingGenerator, EmbeddingGeneratorFactory
from app.ingestion.models import EmbeddingConfig, Chunk


@pytest.mark.asyncio
async def test_openai_embeddings_retry_success(monkeypatch):
    # Arrange: mock AsyncOpenAI to fail twice then succeed
    client = AsyncMock()
    attempts = {"count": 0}

    async def create(input, model):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise Exception("transient error")
        class DataItem:
            def __init__(self):
                self.embedding = [0.1, 0.2, 0.3]
        return type("Resp", (), {"data": [DataItem() for _ in input]})

    client.embeddings.create.side_effect = create

    with patch("app.ingestion.embeddings.AsyncOpenAI", return_value=client):
        gen = OpenAIEmbeddingGenerator(api_key="sk-test")
        cfg = EmbeddingConfig(batch_size=2, max_retries=3, retry_delay_seconds=0.01)
        # Prepare chunks
        from uuid import uuid4
        doc_id = uuid4()
        chunks = [
            Chunk(document_id=doc_id, tenant_id="t", content="A", chunk_index=0, start_char=0, end_char=1, metadata={}),
            Chunk(document_id=doc_id, tenant_id="t", content="B", chunk_index=1, start_char=2, end_char=3, metadata={}),
        ]
        # Act
        out = await gen.generate_batch(chunks, cfg)
        # Assert
        assert len(out) == 2
        assert all(c.embedding for c in out)
        assert attempts["count"] >= 3


@pytest.mark.asyncio
async def test_embedding_factory_skip_noop(monkeypatch):
    monkeypatch.setenv("SKIP_SENTENCE_TRANSFORMERS", "1")
    gen = EmbeddingGeneratorFactory.create(use_openai=False)
    cfg = EmbeddingConfig()
    vecs = await gen.generate(["x", "y"], cfg)
    assert len(vecs) == 2
    assert all(isinstance(v, list) and len(v) > 0 for v in vecs)
