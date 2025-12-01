"""Application configuration using Pydantic Settings."""
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "EVA Domain Assistant 2.0"
    app_version: str = "0.1.0"
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # API Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 4

    # Security
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",  # Added to support local Vite dev & contract tests
    ]

    # Multi-Tenancy
    tenant_header_name: str = "X-Tenant-ID"
    default_tenant_id: str = "default"
    max_tenants: int = 1000

    # Qdrant Vector DB
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_https: bool = False
    qdrant_prefix: str = "tenant"
    vector_size: int = 1536  # OpenAI ada-002 embedding size

    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_ttl_seconds: int = 3600
    redis_max_connections: int = 50

    # OpenAI
    openai_api_key: str = Field(..., min_length=1)
    openai_org_id: str | None = None
    openai_embedding_model: str = "text-embedding-ada-002"
    openai_llm_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.0

    # Document Ingestion
    chunk_size: int = 512
    chunk_overlap: int = 102  # 20% overlap
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".html", ".pdf", ".docx", ".txt"]
    ocr_enabled: bool = True
    ocr_language: str = "eng"

    # Observability
    metrics_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = False
    tracing_endpoint: str = "http://localhost:4317"
    tracing_sample_rate: float = 0.1

    # Cost Tracking
    cost_tracking_enabled: bool = True
    cost_per_1k_input_tokens: float = 0.0001
    cost_per_1k_output_tokens: float = 0.0002
    cost_per_1k_embeddings: float = 0.0001


settings = Settings()
