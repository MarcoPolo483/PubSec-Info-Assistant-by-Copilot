"""Ingestion service orchestrating document processing pipeline."""
import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from ..config import settings
from .chunking import ChunkingStrategyFactory
from .embeddings import EmbeddingGeneratorFactory
from .loaders import DocumentLoaderFactory
from .models import (
    ChunkingConfig,
    Document,
    DocumentStatus,
    DocumentType,
    EmbeddingConfig,
    IngestionRequest,
    IngestionResponse,
)
from .vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting and indexing documents."""

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        chunking_strategy: str = "sentence",
        use_openai_embeddings: bool = True,
    ) -> None:
        """Initialize ingestion service."""
        self.vector_store = vector_store or QdrantVectorStore()
        self.chunking_strategy = ChunkingStrategyFactory.get_strategy(chunking_strategy)
        self.embedding_generator = EmbeddingGeneratorFactory.create(use_openai=use_openai_embeddings)
        logger.info("Initialized IngestionService")

    async def ingest_document(
        self,
        request: IngestionRequest,
        chunking_config: ChunkingConfig | None = None,
        embedding_config: EmbeddingConfig | None = None,
    ) -> IngestionResponse:
        """Ingest and index a document."""
        start_time = time.time()

        try:
            # Validate file size
            if request.content and len(request.content) > settings.max_file_size_mb * 1024 * 1024:
                raise ValueError(
                    f"File size exceeds maximum allowed size of {settings.max_file_size_mb} MB"
                )

            # Determine document type from filename
            file_ext = Path(request.filename).suffix
            if file_ext not in settings.allowed_extensions:
                raise ValueError(
                    f"Unsupported file extension: {file_ext}. "
                    f"Allowed: {', '.join(settings.allowed_extensions)}"
                )

            # Load document
            loader = DocumentLoaderFactory.get_loader_by_extension(file_ext)
            if not request.content:
                raise ValueError("Document content is required")

            document = loader.load(
                content=request.content, filename=request.filename, tenant_id=request.tenant_id
            )

            # Update metadata from request
            if request.metadata:
                document.metadata.title = request.metadata.title or document.metadata.title
                document.metadata.author = request.metadata.author or document.metadata.author
                document.metadata.source_url = (
                    request.source_url or document.metadata.source_url
                )

            document.status = DocumentStatus.PROCESSING
            logger.info(f"Loaded document {document.id} ({document.filename})")

            # Chunk document
            chunking_cfg = chunking_config or ChunkingConfig(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            chunks = self.chunking_strategy.chunk(document, chunking_cfg)
            if not chunks:
                raise ValueError("No chunks created from document")

            logger.info(f"Created {len(chunks)} chunks from document {document.id}")

            # Generate embeddings
            embedding_cfg = embedding_config or EmbeddingConfig(
                model_name=settings.openai_embedding_model
            )
            chunks_with_embeddings = await self.embedding_generator.generate_batch(
                chunks, embedding_cfg
            )
            logger.info(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")

            # Store in vector DB
            await self.vector_store.upsert_chunks(chunks_with_embeddings)
            logger.info(f"Stored {len(chunks_with_embeddings)} chunks in vector DB")

            # Update document status
            document.status = DocumentStatus.COMPLETED
            processing_time_ms = (time.time() - start_time) * 1000

            return IngestionResponse(
                document_id=document.id,
                status=document.status,
                chunks_created=len(chunks_with_embeddings),
                processing_time_ms=processing_time_ms,
                message=f"Successfully ingested {request.filename}",
            )

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to ingest document {request.filename}: {e}", exc_info=True)

            # Return error response
            return IngestionResponse(
                document_id=document.id if "document" in locals() else None,  # type: ignore
                status=DocumentStatus.FAILED,
                chunks_created=0,
                processing_time_ms=processing_time_ms,
                message=f"Failed to ingest document: {str(e)}",
            )

    async def delete_document(self, tenant_id: str, document_id: str) -> dict[str, Any]:
        """Delete a document and its chunks."""
        try:
            from uuid import UUID

            doc_uuid = UUID(document_id)
            await self.vector_store.delete_document(tenant_id, doc_uuid)

            return {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "status": "deleted",
                "message": "Document successfully deleted",
            }

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "status": "error",
                "message": f"Failed to delete document: {str(e)}",
            }

    async def get_collection_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get statistics for tenant collection."""
        try:
            return await self.vector_store.get_collection_stats(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get collection stats for {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close all connections."""
        await self.vector_store.close()
        logger.info("Closed IngestionService")
