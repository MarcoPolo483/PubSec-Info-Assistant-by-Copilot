"""Qdrant vector store integration with tenant isolation."""
import logging
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from ..config import settings
from .models import Chunk

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant vector store with multi-tenant support."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        api_key: str | None = None,
        https: bool | None = None,
    ) -> None:
        """Initialize Qdrant client."""
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.api_key = api_key or settings.qdrant_api_key
        self.https = https if https is not None else settings.qdrant_https
        self.vector_size = settings.vector_size

        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            https=self.https,
        )
        logger.info(f"Initialized Qdrant client: {self.host}:{self.port}")

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get tenant-specific collection name."""
        return f"{settings.qdrant_prefix}_{tenant_id}"

    async def create_collection(self, tenant_id: str) -> None:
        """Create collection for tenant if it doesn't exist."""
        collection_name = self._get_collection_name(tenant_id)

        try:
            collections = await self.client.get_collections()
            existing_names = [col.name for col in collections.collections]

            if collection_name not in existing_names:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.debug(f"Collection already exists: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    async def delete_collection(self, tenant_id: str) -> None:
        """Delete tenant collection."""
        collection_name = self._get_collection_name(tenant_id)

        try:
            await self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    async def upsert_chunks(self, chunks: list[Chunk]) -> None:
        """Upsert chunks to tenant collection."""
        if not chunks:
            return

        tenant_id = chunks[0].tenant_id
        collection_name = self._get_collection_name(tenant_id)

        # Ensure collection exists
        await self.create_collection(tenant_id)

        # Prepare points
        points: list[PointStruct] = []
        for chunk in chunks:
            if not chunk.embedding:
                logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                continue

            point = PointStruct(
                id=str(chunk.id),
                vector=chunk.embedding,
                payload={
                    "document_id": str(chunk.document_id),
                    "tenant_id": chunk.tenant_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "metadata": chunk.metadata,
                    "created_at": chunk.created_at.isoformat(),
                },
            )
            points.append(point)

        if not points:
            logger.warning("No valid points to upsert")
            return

        try:
            await self.client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Upserted {len(points)} chunks to {collection_name}")
        except Exception as e:
            logger.error(f"Failed to upsert chunks to {collection_name}: {e}")
            raise

    async def search(
        self,
        tenant_id: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.5,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks in tenant collection."""
        collection_name = self._get_collection_name(tenant_id)

        try:
            search_results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
            )

            results = []
            for result in search_results:
                results.append(
                    {
                        "id": result.id,
                        "score": result.score,
                        "content": result.payload.get("content", ""),
                        "document_id": result.payload.get("document_id"),
                        "chunk_index": result.payload.get("chunk_index"),
                        "metadata": result.payload.get("metadata", {}),
                    }
                )

            logger.info(f"Found {len(results)} results for tenant {tenant_id}")
            return results

        except Exception as e:
            logger.error(f"Search failed for {collection_name}: {e}")
            raise

    async def delete_document(self, tenant_id: str, document_id: UUID) -> None:
        """Delete all chunks for a document."""
        collection_name = self._get_collection_name(tenant_id)

        try:
            # Delete by filter
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            await self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id)),
                        )
                    ]
                ),
            )
            logger.info(f"Deleted document {document_id} from {collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    async def get_collection_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get collection statistics."""
        collection_name = self._get_collection_name(tenant_id)

        try:
            collection_info = await self.client.get_collection(collection_name=collection_name)
            return {
                "collection_name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant client."""
        await self.client.close()
        logger.info("Closed Qdrant client")
