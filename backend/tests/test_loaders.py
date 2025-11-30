"""Tests for document loaders."""
import pytest

from app.ingestion.loaders import (
    DOCXLoader,
    DocumentLoaderFactory,
    HTMLLoader,
    PDFLoader,
    TXTLoader,
)
from app.ingestion.models import DocumentType


class TestHTMLLoader:
    """Tests for HTML document loader."""

    def test_load_html(self, sample_html_content: bytes, test_tenant_id: str) -> None:
        """Test loading HTML document."""
        loader = HTMLLoader()
        document = loader.load(sample_html_content, "test.html", test_tenant_id)

        assert document.tenant_id == test_tenant_id
        assert document.filename == "test.html"
        assert document.doc_type == DocumentType.HTML
        assert "Test Heading" in document.content
        assert "test paragraph" in document.content
        assert document.metadata.title == "Test Document"
        assert document.metadata.author == "Test Author"
        assert document.metadata.language == "en"
        assert document.metadata.file_size_bytes == len(sample_html_content)

    def test_extract_metadata(self, sample_html_content: bytes) -> None:
        """Test metadata extraction from HTML."""
        loader = HTMLLoader()
        metadata = loader.extract_metadata(sample_html_content)

        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert metadata.language == "en"

    def test_load_invalid_html(self, test_tenant_id: str) -> None:
        """Test loading invalid HTML."""
        loader = HTMLLoader()
        invalid_content = b"\x80\x81\x82"  # Invalid UTF-8

        with pytest.raises(ValueError, match="Invalid HTML document"):
            loader.load(invalid_content, "invalid.html", test_tenant_id)


class TestTXTLoader:
    """Tests for TXT document loader."""

    def test_load_txt(self, sample_text_content: bytes, test_tenant_id: str) -> None:
        """Test loading text document."""
        loader = TXTLoader()
        document = loader.load(sample_text_content, "test.txt", test_tenant_id)

        assert document.tenant_id == test_tenant_id
        assert document.filename == "test.txt"
        assert document.doc_type == DocumentType.TXT
        assert "Test Document" in document.content
        assert "multiple paragraphs" in document.content
        assert document.metadata.file_size_bytes == len(sample_text_content)

    def test_extract_metadata(self, sample_text_content: bytes) -> None:
        """Test metadata extraction from TXT."""
        loader = TXTLoader()
        metadata = loader.extract_metadata(sample_text_content)

        assert metadata.file_size_bytes == len(sample_text_content)
        assert metadata.title is None
        assert metadata.author is None


class TestDocumentLoaderFactory:
    """Tests for document loader factory."""

    def test_get_loader_by_type(self) -> None:
        """Test getting loader by document type."""
        html_loader = DocumentLoaderFactory.get_loader(DocumentType.HTML)
        assert isinstance(html_loader, HTMLLoader)

        pdf_loader = DocumentLoaderFactory.get_loader(DocumentType.PDF)
        assert isinstance(pdf_loader, PDFLoader)

        docx_loader = DocumentLoaderFactory.get_loader(DocumentType.DOCX)
        assert isinstance(docx_loader, DOCXLoader)

        txt_loader = DocumentLoaderFactory.get_loader(DocumentType.TXT)
        assert isinstance(txt_loader, TXTLoader)

    def test_get_loader_by_extension(self) -> None:
        """Test getting loader by file extension."""
        html_loader = DocumentLoaderFactory.get_loader_by_extension(".html")
        assert isinstance(html_loader, HTMLLoader)

        html_loader = DocumentLoaderFactory.get_loader_by_extension("htm")
        assert isinstance(html_loader, HTMLLoader)

        txt_loader = DocumentLoaderFactory.get_loader_by_extension(".txt")
        assert isinstance(txt_loader, TXTLoader)

    def test_get_loader_unsupported_extension(self) -> None:
        """Test getting loader for unsupported extension."""
        with pytest.raises(ValueError, match="Unsupported file extension"):
            DocumentLoaderFactory.get_loader_by_extension(".xyz")
