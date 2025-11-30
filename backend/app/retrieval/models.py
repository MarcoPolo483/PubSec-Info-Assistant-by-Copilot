"""Data models for retrieval."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., min_length=1, max_length=1000)
    tenant_id: str
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    filters: dict[str, Any] | None = None


class SearchResult(BaseModel):
    """Search result model."""

    id: str
    score: float
    content: str
    document_id: str
    chunk_index: int
    metadata: dict[str, Any]
    rerank_score: float | None = None


class RetrievalResponse(BaseModel):
    """Response model for retrieval."""

    query: str
    tenant_id: str
    results: list[SearchResult]
    total_results: int
    processing_time_ms: float
    cached: bool = False


class Citation(BaseModel):
    """Citation model for source attribution."""

    document_id: str
    chunk_id: str
    content: str
    title: str | None = None
    author: str | None = None
    source_url: str | None = None
    page_number: int | None = None
    relevance_score: float
