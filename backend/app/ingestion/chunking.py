"""Chunking strategies for document splitting."""
import logging
from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from .models import Chunk, ChunkingConfig, Document

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
