"""Tests for chunking strategies."""
import pytest

from app.ingestion.chunking import (
    ChunkingStrategyFactory,
    FixedSizeChunkingStrategy,
    SentenceChunkingStrategy,
)
from app.ingestion.loaders import TXTLoader
from app.ingestion.models import ChunkingConfig


class TestSentenceChunkingStrategy:
    """Tests for sentence-based chunking strategy."""

    def test_chunk_document(self, sample_text_content: bytes, test_tenant_id: str) -> None:
        """Test chunking a document."""
        loader = TXTLoader()
        document = loader.load(sample_text_content, "test.txt", test_tenant_id)

        strategy = SentenceChunkingStrategy()
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20)
        chunks = strategy.chunk(document, config)

        assert len(chunks) > 0
        assert all(chunk.tenant_id == test_tenant_id for chunk in chunks)
        assert all(chunk.document_id == document.id for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))
        assert all(chunk.content for chunk in chunks)

    def test_chunk_with_overlap(self, test_tenant_id: str) -> None:
        """Test chunking with overlap."""
        from app.ingestion.models import Document, DocumentMetadata, DocumentType

        document = Document(
            tenant_id=test_tenant_id,
            filename="test.txt",
            doc_type=DocumentType.TXT,
            content="A" * 500 + "\n\n" + "B" * 500,
            metadata=DocumentMetadata(),
        )

        strategy = SentenceChunkingStrategy()
        config = ChunkingConfig(chunk_size=300, chunk_overlap=50)
        chunks = strategy.chunk(document, config)

        assert len(chunks) >= 2
        # Check that chunks have proper indices
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1


class TestFixedSizeChunkingStrategy:
    """Tests for fixed-size chunking strategy."""

    def test_chunk_document(self, sample_text_content: bytes, test_tenant_id: str) -> None:
        """Test fixed-size chunking."""
        loader = TXTLoader()
        document = loader.load(sample_text_content, "test.txt", test_tenant_id)

        strategy = FixedSizeChunkingStrategy()
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20)
        chunks = strategy.chunk(document, config)

        assert len(chunks) > 0
        assert all(len(chunk.content) <= config.chunk_size for chunk in chunks)
        assert all(chunk.tenant_id == test_tenant_id for chunk in chunks)

    def test_chunk_with_exact_size(self, test_tenant_id: str) -> None:
        """Test chunking with exact sizes."""
        from app.ingestion.models import Document, DocumentMetadata, DocumentType

        content = "A" * 1000
        document = Document(
            tenant_id=test_tenant_id,
            filename="test.txt",
            doc_type=DocumentType.TXT,
            content=content,
            metadata=DocumentMetadata(),
        )

        strategy = FixedSizeChunkingStrategy()
        config = ChunkingConfig(chunk_size=100, chunk_overlap=10)
        chunks = strategy.chunk(document, config)

        # With 1000 chars, chunk_size 100, overlap 10:
        # Step size = 100 - 10 = 90
        # Expected chunks = ceil((1000 - 100) / 90) + 1 = 11
        assert len(chunks) >= 10
        assert all(chunk.start_char < chunk.end_char for chunk in chunks)


class TestChunkingStrategyFactory:
    """Tests for chunking strategy factory."""

    def test_get_sentence_strategy(self) -> None:
        """Test getting sentence chunking strategy."""
        strategy = ChunkingStrategyFactory.get_strategy("sentence")
        assert isinstance(strategy, SentenceChunkingStrategy)

    def test_get_fixed_strategy(self) -> None:
        """Test getting fixed-size chunking strategy."""
        strategy = ChunkingStrategyFactory.get_strategy("fixed")
        assert isinstance(strategy, FixedSizeChunkingStrategy)

    def test_get_unknown_strategy(self) -> None:
        """Test getting unknown strategy."""
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            ChunkingStrategyFactory.get_strategy("unknown")
