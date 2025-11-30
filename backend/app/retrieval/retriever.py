"""Retriever for semantic search with reranking."""
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
            results = await self.vector_store.search(
                tenant_id=query.tenant_id,
                query_vector=query_vector,
                limit=query.limit,
                score_threshold=query.score_threshold,
                filter_conditions=query.filters,
            )

            # Convert to SearchResult models
            search_results = [
                SearchResult(
                    id=str(result["id"]),
                    score=result["score"],
                    content=result["content"],
                    document_id=result["document_id"],
                    chunk_index=result["chunk_index"],
                    metadata=result["metadata"],
                )
                for result in results
            ]

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
