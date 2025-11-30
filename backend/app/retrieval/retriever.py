"""Retriever implementing semantic search with post-filtering.

Enhancements:
- Applies score threshold filtering locally for consistency even if vector store does not.
- Enforces result limit after filtering.
- Sorts results by score descending (stable) for deterministic ordering.
- Measures processing time.
"""
import logging
import time
from typing import Any

from ..ingestion.embeddings import EmbeddingGeneratorFactory
from ..ingestion.models import EmbeddingConfig
from ..ingestion.vector_store import QdrantVectorStore
from .models import SearchQuery, SearchResult, RetrievalResponse

logger = logging.getLogger(__name__)


class Retriever:
    """Retriever for semantic search."""

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        use_openai_embeddings: bool = True,
    ) -> None:
        """Initialize retriever."""
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_generator = EmbeddingGeneratorFactory.create(use_openai=use_openai_embeddings)
        logger.info("Initialized Retriever")

    async def search(
        self,
        query: SearchQuery,
        embedding_config: EmbeddingConfig | None = None,
    ) -> RetrievalResponse:
        """Search for relevant documents."""
        start_time = time.time()

        try:
            # Generate query embedding
            embedding_cfg = embedding_config or EmbeddingConfig()
            query_embeddings = await self.embedding_generator.generate(
                [query.query], embedding_cfg
            )
            query_vector = query_embeddings[0]

            # Search vector store
            raw_results = await self.vector_store.search(
                tenant_id=query.tenant_id,
                query_vector=query_vector,
                limit=query.limit,  # upstream hint (best-effort)
                score_threshold=query.score_threshold,
                filter_conditions=query.filters,
            )

            # Normalize & convert
            converted = [
                SearchResult(
                    id=str(r.get("id")),
                    score=float(r.get("score", 0.0)),
                    content=r.get("content", ""),
                    document_id=r.get("document_id"),
                    chunk_index=r.get("chunk_index", 0),
                    metadata=r.get("metadata", {}) or {},
                )
                for r in raw_results
            ]

            # Apply local score filtering (>= threshold)
            if query.score_threshold is not None:
                filtered = [sr for sr in converted if sr.score >= query.score_threshold]
            else:
                filtered = converted

            # Sort by score descending (stable)
            filtered.sort(key=lambda x: x.score, reverse=True)

            # Apply hard limit
            limited = filtered[: query.limit] if query.limit else filtered

            search_results = limited

            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Retrieved {len(search_results)} results for tenant {query.tenant_id} "
                f"in {processing_time_ms:.2f}ms"
            )

            return RetrievalResponse(
                query=query.query,
                tenant_id=query.tenant_id,
                results=search_results,
                total_results=len(search_results),
                processing_time_ms=processing_time_ms,
                cached=False,
            )

        except Exception as e:
            logger.error(f"Search failed for tenant {query.tenant_id}: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close retriever resources."""
        await self.vector_store.close()
        logger.info("Closed Retriever")
