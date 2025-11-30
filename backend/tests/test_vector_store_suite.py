"""Tests for QdrantVectorStore covering create/upsert/search/delete/stats with monkeypatched client."""
import pytest
from uuid import uuid4
from types import SimpleNamespace

from app.ingestion.vector_store import QdrantVectorStore
from app.ingestion.models import Chunk


class StubQdrantClient:
    def __init__(self):
        self.collections = set()
        self.points = {}
        self.closed = False

    async def get_collections(self):
        return SimpleNamespace(collections=[SimpleNamespace(name=name) for name in self.collections])

    async def create_collection(self, collection_name, vectors_config):
        self.collections.add(collection_name)

    async def delete_collection(self, collection_name):
        if collection_name in self.collections:
            self.collections.remove(collection_name)
        else:
            raise RuntimeError("collection missing")

    async def upsert(self, collection_name, points):
        self.points.setdefault(collection_name, {})
        for p in points:
            self.points[collection_name][p.id] = p

    async def search(self, collection_name, query_vector, limit, score_threshold, query_filter=None):
        # Return stub results that respect limit; scores decreasing
        results = []
        for i in range(limit + 2):
            score = 1.0 - (i * 0.1)
            if score < score_threshold:
                continue
            payload = {
                "content": f"Chunk {i} content",
                "document_id": str(uuid4()),
                "chunk_index": i,
                "metadata": {"page_number": i+1},
            }
            results.append(SimpleNamespace(id=str(uuid4()), score=score, payload=payload))
        return results[:limit]

    async def delete(self, collection_name, points_selector):
        # Simplified: remove all points in collection
        self.points[collection_name] = {}

    async def get_collection(self, collection_name):
        # Return stats based on points
        points_count = len(self.points.get(collection_name, {}))
        return SimpleNamespace(
            vectors_count=points_count,
            indexed_vectors_count=points_count,
            points_count=points_count,
            status="green",
        )

    async def close(self):
        self.closed = True


@pytest.fixture
def store(monkeypatch):
    # Patch AsyncQdrantClient to our stub
    monkeypatch.setattr("app.ingestion.vector_store.AsyncQdrantClient", lambda **kwargs: StubQdrantClient())
    return QdrantVectorStore(host="localhost", port=6333, api_key=None, https=False)


@pytest.mark.asyncio
async def test_create_and_upsert_search_delete(store):
    tenant = "t1"
    await store.create_collection(tenant)

    # Prepare chunks (one without embedding to be skipped)
    doc_id = uuid4()
    chunks = [
        Chunk(document_id=doc_id, tenant_id=tenant, content="A", chunk_index=0, start_char=0, end_char=1, embedding=[0.1,0.2,0.3], metadata={}),
        Chunk(document_id=doc_id, tenant_id=tenant, content="B", chunk_index=1, start_char=2, end_char=3, embedding=None, metadata={}),
    ]

    # Upsert should skip chunk without embedding
    await store.upsert_chunks(chunks)

    # Search
    results = await store.search(tenant_id=tenant, query_vector=[0.1,0.2,0.3], limit=3, score_threshold=0.5)
    assert len(results) == 3
    assert all(r["score"] >= 0.5 for r in results)
    assert "content" in results[0]

    # Delete document
    await store.delete_document(tenant_id=tenant, document_id=doc_id)

    # Stats
    stats = await store.get_collection_stats(tenant)
    assert stats["collection_name"].endswith(tenant)
    assert stats["status"] == "green"

    # Close
    await store.close()


@pytest.mark.asyncio
async def test_delete_collection_errors(store):
    # Attempt to delete non-existent collection should raise
    with pytest.raises(Exception):
        await store.delete_collection("missing-tenant")


@pytest.mark.asyncio
async def test_search_with_filter_conditions(store):
    tenant = "t2"
    await store.create_collection(tenant)
    # Verify search supports filter arg pass-through
    results = await store.search(tenant_id=tenant, query_vector=[0.0,0.0], limit=2, score_threshold=0.3, filter_conditions={"must": []})
    assert len(results) == 2
