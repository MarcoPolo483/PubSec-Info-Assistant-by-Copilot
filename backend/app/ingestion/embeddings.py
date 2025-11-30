"""Embedding generation with OpenAI and sentence-transformers fallback."""
import asyncio
import logging
from typing import Protocol

import openai
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from ..config import settings
from .models import Chunk, EmbeddingConfig

logger = logging.getLogger(__name__)


class EmbeddingGeneratorProtocol(Protocol):
    """Protocol for embedding generators."""

    async def generate(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """Generate embeddings for texts."""
        ...

    async def generate_batch(
        self, chunks: list[Chunk], config: EmbeddingConfig
    ) -> list[Chunk]:
        """Generate embeddings for chunk batch."""
        ...


class OpenAIEmbeddingGenerator:
    """Embedding generator using OpenAI API."""

    def __init__(self, api_key: str | None = None, org_id: str | None = None) -> None:
        """Initialize OpenAI embedding generator."""
        self.client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            organization=org_id or settings.openai_org_id,
        )
        self.model = settings.openai_embedding_model

    async def generate(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        if not texts:
            return []

        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=config.model_name or self.model,
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings using OpenAI")
            return embeddings

        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    async def generate_batch(
        self, chunks: list[Chunk], config: EmbeddingConfig
    ) -> list[Chunk]:
        """Generate embeddings for chunks in batches."""
        if not chunks:
            return []

        result_chunks = []
        batch_size = config.batch_size

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.content for chunk in batch]

            # Retry logic
            for attempt in range(config.max_retries):
                try:
                    embeddings = await self.generate(texts, config)

                    # Assign embeddings to chunks
                    for chunk, embedding in zip(batch, embeddings):
                        chunk.embedding = embedding
                        result_chunks.append(chunk)

                    break  # Success, exit retry loop

                except Exception as e:
                    if attempt < config.max_retries - 1:
                        wait_time = config.retry_delay_seconds * (2**attempt)
                        logger.warning(
                            f"Embedding generation failed (attempt {attempt + 1}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Embedding generation failed after {config.max_retries} attempts"
                        )
                        raise

        logger.info(f"Generated embeddings for {len(result_chunks)} chunks")
        return result_chunks


class SentenceTransformerEmbeddingGenerator:
    """Fallback embedding generator using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize sentence-transformers embedding generator."""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded sentence-transformer model: {model_name}")

    async def generate(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """Generate embeddings using sentence-transformers."""
        if not texts:
            return []

        try:
            # sentence-transformers is synchronous, run in executor
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.model.encode, texts)

            # Convert to list of lists
            embeddings_list = [emb.tolist() for emb in embeddings]
            logger.info(f"Generated {len(embeddings_list)} embeddings using sentence-transformers")
            return embeddings_list

        except Exception as e:
            logger.error(f"Sentence-transformer embedding generation failed: {e}")
            raise

    async def generate_batch(
        self, chunks: list[Chunk], config: EmbeddingConfig
    ) -> list[Chunk]:
        """Generate embeddings for chunks in batches."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        embeddings = await self.generate(texts, config)

        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        logger.info(f"Generated embeddings for {len(chunks)} chunks using sentence-transformers")
        return chunks


class HybridEmbeddingGenerator:
    """Hybrid embedding generator with OpenAI primary and sentence-transformers fallback."""

    def __init__(
        self,
        primary_api_key: str | None = None,
        fallback_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize hybrid embedding generator."""
        self.primary = OpenAIEmbeddingGenerator(api_key=primary_api_key)
        self.fallback = SentenceTransformerEmbeddingGenerator(model_name=fallback_model)

    async def generate(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """Generate embeddings with fallback."""
        try:
            return await self.primary.generate(texts, config)
        except Exception as e:
            logger.warning(f"Primary embedding generator failed, using fallback: {e}")
            return await self.fallback.generate(texts, config)

    async def generate_batch(
        self, chunks: list[Chunk], config: EmbeddingConfig
    ) -> list[Chunk]:
        """Generate embeddings for chunks with fallback."""
        try:
            return await self.primary.generate_batch(chunks, config)
        except Exception as e:
            logger.warning(f"Primary embedding generator failed, using fallback: {e}")
            return await self.fallback.generate_batch(chunks, config)


class EmbeddingGeneratorFactory:
    """Factory for creating embedding generators."""

    @staticmethod
    def create(
        use_openai: bool = True,
        api_key: str | None = None,
        fallback_model: str = "all-MiniLM-L6-v2",
    ) -> EmbeddingGeneratorProtocol:
        """Create embedding generator."""
        if use_openai:
            try:
                return HybridEmbeddingGenerator(
                    primary_api_key=api_key, fallback_model=fallback_model
                )
            except Exception as e:
                logger.warning(f"Failed to create OpenAI generator, using fallback: {e}")
                return SentenceTransformerEmbeddingGenerator(model_name=fallback_model)
        else:
            return SentenceTransformerEmbeddingGenerator(model_name=fallback_model)
