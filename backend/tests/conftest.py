"""Test configuration and fixtures."""
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

# Set test environment (must match allowed literals in Settings)
os.environ["ENVIRONMENT"] = "dev"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
os.environ["SKIP_SENTENCE_TRANSFORMERS"] = "1"  # Skip heavy torch-dependent import during unit tests for speed/stability
os.environ["OPENAI_API_KEY"] = "test-openai-api-key"


@pytest.fixture(scope="session")
def test_tenant_id() -> str:
    """Fixture for test tenant ID."""
    return "test_tenant"


@pytest.fixture
def sample_html_content() -> bytes:
    """Fixture for sample HTML content."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Document</title>
        <meta name="author" content="Test Author">
    </head>
    <body>
        <h1>Test Heading</h1>
        <p>This is a test paragraph with some content.</p>
        <p>This is another paragraph for testing chunking.</p>
    </body>
    </html>
    """
    return html.encode("utf-8")


@pytest.fixture
def sample_text_content() -> bytes:
    """Fixture for sample text content."""
    text = """Test Document

This is a test document with multiple paragraphs.

First paragraph with some content that should be chunked properly.

Second paragraph with additional information for testing the ingestion pipeline.

Third paragraph to ensure proper handling of multiple text segments."""
    return text.encode("utf-8")


@pytest_asyncio.fixture
async def mock_qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    """Fixture for mock Qdrant client (in-memory)."""
    client = AsyncQdrantClient(":memory:")
    yield client
    await client.close()
