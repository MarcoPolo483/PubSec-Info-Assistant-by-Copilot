import pytest
from unittest.mock import AsyncMock

from app.ingestion.service import IngestionService
from app.ingestion.models import IngestionRequest, Document, DocumentType, DocumentMetadata, Chunk, ChunkingConfig, EmbeddingConfig
from app.ingestion import loaders as loaders_module
from app.ingestion import chunking as chunking_module
from app.ingestion import embeddings as embeddings_module
from app import config as config_module


class DummyLoader:
    def __init__(self):
        self.doc_type = DocumentType.TXT

    def load(self, content: bytes, filename: str, tenant_id: str) -> Document:
        return Document(
            tenant_id=tenant_id,
            filename=filename,
            doc_type=DocumentType.TXT,
            content=content.decode("utf-8"),
            metadata=DocumentMetadata(file_size_bytes=len(content)),
        )

    def extract_metadata(self, content: bytes):
        return DocumentMetadata(file_size_bytes=len(content))


class DummyChunkStrategy:
    def chunk(self, document: Document, config: ChunkingConfig):
        # Produce two small chunks
        return [
            Chunk(document_id=document.id, tenant_id=document.tenant_id, content="A", chunk_index=0, start_char=0, end_char=1),
            Chunk(document_id=document.id, tenant_id=document.tenant_id, content="B", chunk_index=1, start_char=1, end_char=2),
        ]


class DummyEmbeddingGen:
    async def generate_batch(self, chunks, embedding_cfg: EmbeddingConfig):
        # Attach fake embeddings
        for c in chunks:
            c.embedding = [0.0, 0.1]
        return chunks


@pytest.fixture()
def patched_env(monkeypatch):
    monkeypatch.setattr(loaders_module.DocumentLoaderFactory, "get_loader_by_extension", lambda ext: DummyLoader())
    monkeypatch.setattr(chunking_module.ChunkingStrategyFactory, "get_strategy", lambda name="sentence": DummyChunkStrategy())
    monkeypatch.setattr(embeddings_module.EmbeddingGeneratorFactory, "create", lambda use_openai=True: DummyEmbeddingGen())
    return monkeypatch

@pytest.mark.asyncio
async def test_ingest_success(patched_env):
    vector_store_mock = AsyncMock()
    vector_store_mock.upsert_chunks = AsyncMock()
    service = IngestionService(vector_store=vector_store_mock)

    req = IngestionRequest(tenant_id="t1", filename="file.txt", content=b"Hello World")
    resp = await service.ingest_document(req)

    assert resp.status.value == "completed"
    assert resp.chunks_created == 2
    vector_store_mock.upsert_chunks.assert_awaited()


@pytest.mark.asyncio
async def test_ingest_unsupported_extension(patched_env):
    service = IngestionService(vector_store=AsyncMock())
    req = IngestionRequest(tenant_id="t1", filename="file.xyz", content=b"data")
    resp = await service.ingest_document(req)
    assert resp.status.value == "failed"
    assert "Unsupported file extension" in resp.message


@pytest.mark.asyncio
async def test_ingest_too_large(patched_env):
    service = IngestionService(vector_store=AsyncMock())
    # Force max size small for test
    original = config_module.settings.max_file_size_mb
    config_module.settings.max_file_size_mb = 0  # zero MB limit triggers failure
    req = IngestionRequest(tenant_id="t1", filename="file.txt", content=b"abc")
    resp = await service.ingest_document(req)
    assert resp.status.value == "failed"
    assert "File size exceeds" in resp.message
    config_module.settings.max_file_size_mb = original


@pytest.mark.asyncio
async def test_ingest_empty_content(patched_env):
    service = IngestionService(vector_store=AsyncMock())
    req = IngestionRequest(tenant_id="t1", filename="file.txt", content=b"")
    resp = await service.ingest_document(req)
    assert resp.status.value == "failed"
    assert "Document content is required" in resp.message


@pytest.mark.asyncio
async def test_delete_document_error(patched_env):
    vs = AsyncMock()
    vs.delete_document.side_effect = Exception("boom")
    service = IngestionService(vector_store=vs)
    resp = await service.delete_document("tenantA", "not-a-uuid")
    # Invalid UUID triggers exception path
    assert resp["status"] == "error"
    assert "Failed to delete document" in resp["message"]


@pytest.mark.asyncio
async def test_collection_stats_error(patched_env):
    vs = AsyncMock()
    vs.get_collection_stats.side_effect = Exception("stats fail")
    service = IngestionService(vector_store=vs)
    stats = await service.get_collection_stats("tenantA")
    assert stats["error"] == "stats fail"
