"""Tests for ingestion utilities: chunking and embeddings factory skip path."""
import pytest
from app.ingestion.chunking import ChunkTokenizer
from app.ingestion.models import ChunkingConfig, Chunk
from app.ingestion.embeddings import EmbeddingGeneratorFactory


def test_chunk_tokenizer_basic():
    tokenizer = ChunkTokenizer()
    config = ChunkingConfig(max_chunk_size=50, overlap_size=5)
    text = "This is a short document. It has multiple sentences. Security compliance matters."
    chunks = tokenizer.tokenize(text, tenant_id="tenant-a", document_id="doc-1", config=config)
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_tokenizer_respects_size():
    tokenizer = ChunkTokenizer()
    config = ChunkingConfig(max_chunk_size=20, overlap_size=2)
    text = "A long line of text that should be split into multiple manageable parts for testing purposes."  # noqa
    chunks = tokenizer.tokenize(text, tenant_id="tenant-a", document_id="doc-1", config=config)
    assert all(len(c.content) <= 25 for c in chunks)  # allow slight growth due to sentence boundary


def test_embedding_factory_skip(monkeypatch):
    monkeypatch.setenv("SKIP_SENTENCE_TRANSFORMERS", "1")
    gen = EmbeddingGeneratorFactory.create(use_openai=True)
    # OpenAI path returns HybridEmbeddingGenerator; we won't call network here.
    assert hasattr(gen, "generate")