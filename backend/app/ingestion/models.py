"""Data models and schemas for document ingestion."""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""

    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """Metadata extracted from documents."""

    title: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    source_url: str | None = None
    language: str = "en"
    file_size_bytes: int = 0
    page_count: int | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document model."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: str
    filename: str
    doc_type: DocumentType
    content: str
    metadata: DocumentMetadata
    status: DocumentStatus = DocumentStatus.PENDING
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class Chunk(BaseModel):
    """Document chunk model for vector storage."""

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    tenant_id: str
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""

    tenant_id: str
    filename: str
    content: bytes | None = None
    source_url: str | None = None
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class IngestionResponse(BaseModel):
    """Response model for document ingestion.

    document_id is optional for failure cases where a document UUID was never created.
    """

    document_id: UUID | None
    status: DocumentStatus
    chunks_created: int
    processing_time_ms: float
    message: str | None = None


class ChunkingConfig(BaseModel):
    """Configuration for chunking strategy."""

    chunk_size: int = 512
    chunk_overlap: int = 102
    separator: str = "\n\n"
    keep_separator: bool = True
    # Extended fields used by tests for tokenizer sizing
    max_chunk_size: int | None = None
    overlap_size: int | None = None


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str = "text-embedding-ada-002"
    batch_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
