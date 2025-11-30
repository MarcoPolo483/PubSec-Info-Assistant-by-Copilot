"""Data models for LLM interactions."""
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..retrieval.models import Citation


class LLMRequest(BaseModel):
    """Request model for LLM."""

    query: str = Field(..., min_length=1, max_length=1000)
    tenant_id: str
    context: list[str]
    model: str = "gpt-4-turbo-preview"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=4000)
    system_prompt: str | None = None


class LLMResponse(BaseModel):
    """Response model from LLM."""

    query: str
    answer: str
    citations: list[Citation]
    model: str
    tokens_used: 'TokensUsed'
    cost: float
    processing_time_ms: float
    confidence_score: float | None = None
    hallucination_score: float | None = None


class TokensUsed(BaseModel):
    """Structured token usage details."""
    input_tokens: int = 0
    output_tokens: int = 0
    total: int = 0

    def __getitem__(self, key: str) -> int:
        mapping = {
            "input": "input_tokens",
            "output": "output_tokens",
            "total": "total",
            "input_tokens": "input_tokens",
            "output_tokens": "output_tokens",
        }
        attr = mapping.get(key, key)
        return getattr(self, attr)

    def get(self, key: str, default: int = 0) -> int:
        try:
            return self[key]
        except Exception:
            return default


class LLMConfig(BaseModel):
    """Configuration for LLM adapter."""

    provider: Literal["openai", "anthropic", "local"] = "openai"
    model_name: str = "gpt-4-turbo-preview"
    api_key: str | None = None
    org_id: str | None = None
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_seconds: float = 30.0
