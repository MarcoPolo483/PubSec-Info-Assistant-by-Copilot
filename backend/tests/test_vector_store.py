"""Tests for QdrantVectorStore with mocked client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ingestion.vector_store import QdrantVectorStore
from app.ingestion.models import Chunk
from uuid import uuid4


@pytest.fixture
def mock_qdrant():
    client = AsyncMock()
    client.get_collections.return_value = MagicMock(collections=[])
    client.get_collection.return_value = MagicMock(
        vectors_count=10, indexed_vectors_count=10, points_count=10, status="ok"
    )
    client.search.return_value = [
        MagicMock(id="p1", score=0.91, payload={"content": "Alpha", "document_id": "d1", "chunk_index": 0, "metadata": {}}),
        MagicMock(id="p2", score=0.75, payload={"content": "Beta", "document_id": "d2", "chunk_index": 1, "metadata": {}}),
    ]
    return client


@pytest.fixture
def store(mock_qdrant):
    with patch("app.ingestion.vector_store.AsyncQdrantClient", return_value=mock_qdrant):
        return QdrantVectorStore(host="localhost", port=6333, api_key=None, https=False)


@pytest.mark.asyncio
async def test_create_collection(store, mock_qdrant):
    await store.create_collection("tenant-a")
    mock_qdrant.create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_chunks_skips_without_embeddings(store, mock_qdrant):
    chunk = Chunk(
        tenant_id="tenant-a",
        document_id=uuid4(),
        content="Test content",
        chunk_index=0,
        start_char=0,
        end_char=12,
        metadata={},
    )
    await store.upsert_chunks([chunk])
    mock_qdrant.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_chunks_success(store, mock_qdrant):
    chunk = Chunk(
        tenant_id="tenant-a",
        document_id=uuid4(),
        content="Test content",
        chunk_index=0,
        start_char=0,
        end_char=12,
        metadata={},
    )
    chunk.embedding = [0.1, 0.2, 0.3]
    await store.upsert_chunks([chunk])
    mock_qdrant.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_search_filters_and_shapes_results(store, mock_qdrant):
    results = await store.search(
        tenant_id="tenant-a", query_vector=[0.1, 0.2, 0.3], limit=5, score_threshold=0.5
    )
    assert len(results) == 2
    assert results[0]["score"] >= results[1]["score"]
    mock_qdrant.search.assert_called_once()


@pytest.mark.asyncio
async def test_delete_document(store, mock_qdrant):
    doc_id = uuid4()
    await store.delete_document("tenant-a", doc_id)
    mock_qdrant.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_collection_stats(store, mock_qdrant):
    stats = await store.get_collection_stats("tenant-a")
    assert stats["vectors_count"] == 10
    mock_qdrant.get_collection.assert_called_once()


@pytest.mark.asyncio
async def test_search_error_propagates(store, mock_qdrant):
    mock_qdrant.search.side_effect = Exception("Qdrant failure")
    with pytest.raises(Exception, match="Qdrant failure"):
        await store.search("tenant-a", [0.1], limit=1)