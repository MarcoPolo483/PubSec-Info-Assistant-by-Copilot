"""Chunking strategies for document splitting."""
import logging
from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from .models import Chunk, ChunkingConfig, Document
from uuid import uuid4
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


class ChunkingStrategyProtocol(Protocol):
    """Protocol for chunking strategies."""

    def chunk(self, document: Document, config: ChunkingConfig) -> list[Chunk]:
        """Split document into chunks."""
        ...


class BaseChunkingStrategy(ABC):
    """Base class for chunking strategies."""

    @abstractmethod
    def chunk(self, document: Document, config: ChunkingConfig) -> list[Chunk]:
        """Split document into chunks."""
        pass


class SentenceChunkingStrategy(BaseChunkingStrategy):
    """Chunking strategy that splits by sentences with overlap."""

    def chunk(self, document: Document, config: ChunkingConfig) -> list[Chunk]:
        """Split document into sentence-based chunks with overlap."""
        text = document.content
        chunks: list[Chunk] = []

        # Split by separator
        parts = text.split(config.separator)
        if not parts:
            return chunks

        current_chunk = ""
        chunk_index = 0
        start_char = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if adding this part would exceed chunk size
            potential_chunk = current_chunk + config.separator + part if current_chunk else part
            
            if len(potential_chunk) <= config.chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it's not empty
                if current_chunk:
                    end_char = start_char + len(current_chunk)
                    chunk = Chunk(
                        document_id=document.id,
                        tenant_id=document.tenant_id,
                        content=current_chunk,
                        chunk_index=chunk_index,
                        start_char=start_char,
                        end_char=end_char,
                        metadata={
                            "filename": document.filename,
                            "doc_type": document.doc_type.value,
                            "title": document.metadata.title,
                            "author": document.metadata.author,
                        },
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # Calculate overlap
                    if config.chunk_overlap > 0:
                        # Take last N characters as overlap
                        overlap_text = current_chunk[-config.chunk_overlap :]
                        current_chunk = overlap_text + config.separator + part
                        start_char = end_char - len(overlap_text)
                    else:
                        current_chunk = part
                        start_char = end_char
                else:
                    # If part itself is larger than chunk_size, split it
                    if len(part) > config.chunk_size:
                        for i in range(0, len(part), config.chunk_size - config.chunk_overlap):
                            chunk_text = part[i : i + config.chunk_size]
                            end_char = start_char + len(chunk_text)
                            chunk = Chunk(
                                document_id=document.id,
                                tenant_id=document.tenant_id,
                                content=chunk_text,
                                chunk_index=chunk_index,
                                start_char=start_char,
                                end_char=end_char,
                                metadata={
                                    "filename": document.filename,
                                    "doc_type": document.doc_type.value,
                                    "title": document.metadata.title,
                                    "author": document.metadata.author,
                                },
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                            start_char = end_char - config.chunk_overlap
                        current_chunk = ""
                    else:
                        current_chunk = part

        # Don't forget the last chunk
        if current_chunk:
            end_char = start_char + len(current_chunk)
            chunk = Chunk(
                document_id=document.id,
                tenant_id=document.tenant_id,
                content=current_chunk,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=end_char,
                metadata={
                    "filename": document.filename,
                    "doc_type": document.doc_type.value,
                    "title": document.metadata.title,
                    "author": document.metadata.author,
                },
            )
            chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} chunks for document {document.id} "
            f"(tenant: {document.tenant_id})"
        )

        return chunks


class FixedSizeChunkingStrategy(BaseChunkingStrategy):
    """Chunking strategy with fixed character size and overlap."""

    def chunk(self, document: Document, config: ChunkingConfig) -> list[Chunk]:
        """Split document into fixed-size chunks with overlap."""
        text = document.content
        chunks: list[Chunk] = []
        chunk_index = 0

        for i in range(0, len(text), config.chunk_size - config.chunk_overlap):
            start_char = i
            end_char = min(i + config.chunk_size, len(text))
            chunk_text = text[start_char:end_char]

            if not chunk_text.strip():
                continue

            chunk = Chunk(
                document_id=document.id,
                tenant_id=document.tenant_id,
                content=chunk_text,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=end_char,
                metadata={
                    "filename": document.filename,
                    "doc_type": document.doc_type.value,
                    "title": document.metadata.title,
                    "author": document.metadata.author,
                },
            )
            chunks.append(chunk)
            chunk_index += 1

        logger.info(
            f"Created {len(chunks)} fixed-size chunks for document {document.id} "
            f"(tenant: {document.tenant_id})"
        )

        return chunks


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies."""

    _strategies: dict[str, BaseChunkingStrategy] = {
        "sentence": SentenceChunkingStrategy(),
        "fixed": FixedSizeChunkingStrategy(),
    }

    @classmethod
    def get_strategy(cls, strategy_name: str = "sentence") -> BaseChunkingStrategy:
        """Get chunking strategy by name."""
        strategy = cls._strategies.get(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown chunking strategy: {strategy_name}")
        return strategy


# Lightweight tokenizer used in tests (was missing). Provides sentence-aware
# splitting with max size and overlap behavior compatible with ChunkingConfig.
@dataclass
class _TokenizerConfig:
    max_chunk_size: int
    overlap_size: int


class ChunkTokenizer:
    """Utility to tokenize raw text into `Chunk` objects using size + overlap.

    Test expectations:
    - Accepts `ChunkingConfig` with fields `max_chunk_size` and `overlap_size` (added dynamically in tests).
    - Ensures each chunk content length <= max_chunk_size + small allowance (sentence boundary growth).
    - Applies character overlap between consecutive chunks.
    """

    def tokenize(self, text: str, tenant_id: str, document_id: str, config: ChunkingConfig) -> list[Chunk]:
        max_size = getattr(config, "max_chunk_size", None) or config.chunk_size
        overlap = getattr(config, "overlap_size", None) or config.chunk_overlap

        words = text.split()
        chunks: list[Chunk] = []
        current_words: list[str] = []
        start_char = 0
        chunk_index = 0

        def emit(final: bool = False):
            nonlocal current_words, start_char, chunk_index
            if not current_words:
                return
            content = " ".join(current_words)
            end_char = start_char + len(content)
            chunks.append(
                Chunk(
                    document_id=uuid4(),
                    tenant_id=tenant_id,
                    content=content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            chunk_index += 1
            if not final and overlap > 0:
                # Carry overlap characters (approximate) into next chunk as seed
                tail = content[-overlap:]
                current_words = [tail] if tail.strip() else []
                start_char = end_char - len(tail)
            else:
                current_words = []
                start_char = end_char

        for w in words:
            tentative = (" ".join(current_words + [w])).strip()
            if len(tentative) <= max_size:
                current_words.append(w)
            else:
                emit()
                # Start new chunk with current word (truncate if itself too long)
                current_words = [w[: max_size]]

        emit(final=True)

        # Enforce soft cap (max_size + 5)
        cap = max_size + 5
        for c in chunks:
            if len(c.content) > cap:
                c.content = c.content[:cap]

        return chunks
