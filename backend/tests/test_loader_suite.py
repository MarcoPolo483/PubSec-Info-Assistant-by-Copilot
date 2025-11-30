"""Tests for document loaders covering HTML, PDF, DOCX, TXT success and failure paths."""
import pytest
from app.ingestion.loaders import (
    HTMLLoader,
    PDFLoader,
    DOCXLoader,
    TXTLoader,
    DocumentLoaderFactory,
)
from app.ingestion.models import DocumentType


@pytest.fixture
def tenant_id():
    return "tenant-test"


# HTML Loader Tests
@pytest.mark.parametrize("html_bytes,expected_title,expected_author,expected_language", [
    (b"<html lang='en'><head><title>Test Doc</title><meta name='author' content='Alice'></head><body><h1>Heading</h1><p>Paragraph.</p></body></html>", "Test Doc", "Alice", "en"),
])
def test_html_loader_success(html_bytes, expected_title, expected_author, expected_language, tenant_id):
    loader = HTMLLoader()
    doc = loader.load(html_bytes, "sample.html", tenant_id)
    assert doc.doc_type == DocumentType.HTML
    assert "Heading" in doc.content
    assert doc.metadata.title == expected_title
    assert doc.metadata.author == expected_author
    assert doc.metadata.language == expected_language
    assert doc.metadata.file_size_bytes == len(html_bytes)


def test_html_loader_invalid(tenant_id):
    loader = HTMLLoader()
    bad_bytes = bytes([0xff, 0xfe, 0xfd])  # invalid utf-8 sequence
    with pytest.raises(ValueError):
        loader.load(bad_bytes, "bad.html", tenant_id)


# TXT Loader Tests
def test_txt_loader_success(tenant_id):
    loader = TXTLoader()
    content = b"Simple text file contents."
    doc = loader.load(content, "readme.txt", tenant_id)
    assert doc.doc_type == DocumentType.TXT
    assert doc.content == content.decode("utf-8")
    assert doc.metadata.file_size_bytes == len(content)


def test_txt_loader_invalid_utf8(tenant_id):
    loader = TXTLoader()
    bad_bytes = bytes([0xff, 0xfe, 0xfd])
    with pytest.raises(ValueError):
        loader.load(bad_bytes, "bad.txt", tenant_id)


# PDF Loader Tests (monkeypatched)
class StubPdfPage:
    def __init__(self, text: str):
        self._text = text
    def extract_text(self):
        return self._text

class StubPdfReader:
    def __init__(self, file_obj):
        self.pages = [StubPdfPage("Page One"), StubPdfPage("Page Two")]
        class Meta:
            title = "PDF Title"
            author = "PDF Author"
            creation_date = None
        self.metadata = Meta()


def test_pdf_loader_success(monkeypatch, tenant_id):
    monkeypatch.setattr("app.ingestion.loaders.PdfReader", StubPdfReader)
    loader = PDFLoader()
    pdf_bytes = b"%PDF-1.4 minimal"
    doc = loader.load(pdf_bytes, "report.pdf", tenant_id)
    assert doc.doc_type == DocumentType.PDF
    assert "Page One" in doc.content and "Page Two" in doc.content
    assert doc.metadata.title == "PDF Title"
    assert doc.metadata.author == "PDF Author"
    assert doc.metadata.page_count == 2
    assert doc.metadata.file_size_bytes == len(pdf_bytes)


def test_pdf_loader_invalid(monkeypatch, tenant_id):
    def bad_reader(_):
        raise RuntimeError("Broken PDF")
    monkeypatch.setattr("app.ingestion.loaders.PdfReader", bad_reader)
    loader = PDFLoader()
    with pytest.raises(ValueError):
        loader.load(b"%PDF-1.4", "broken.pdf", tenant_id)


# DOCX Loader Tests (monkeypatched)
class StubParagraph:
    def __init__(self, text):
        self.text = text

class StubCoreProps:
    def __init__(self):
        self.title = "Docx Title"
        self.author = "Docx Author"
        self.created = None

class StubDocxDocument:
    def __init__(self, file_obj):
        self.paragraphs = [StubParagraph("First paragraph."), StubParagraph("Second paragraph.")]
        self.core_properties = StubCoreProps()


def test_docx_loader_success(monkeypatch, tenant_id):
    monkeypatch.setattr("app.ingestion.loaders.DocxDocument", StubDocxDocument)
    loader = DOCXLoader()
    docx_bytes = b"PK\x03\x04 minimal docx stub"  # zip header signature
    doc = loader.load(docx_bytes, "whitepaper.docx", tenant_id)
    assert doc.doc_type == DocumentType.DOCX
    assert "First paragraph." in doc.content
    assert doc.metadata.title == "Docx Title"
    assert doc.metadata.author == "Docx Author"
    assert doc.metadata.file_size_bytes == len(docx_bytes)


def test_docx_loader_invalid(monkeypatch, tenant_id):
    def bad_docx(_):
        raise RuntimeError("Broken DOCX")
    monkeypatch.setattr("app.ingestion.loaders.DocxDocument", bad_docx)
    loader = DOCXLoader()
    with pytest.raises(ValueError):
        loader.load(b"PK\x03\x04", "broken.docx", tenant_id)


# Factory Tests
@pytest.mark.parametrize("ext,expected_type", [
    ("html", DocumentType.HTML),
    ("htm", DocumentType.HTML),
    ("pdf", DocumentType.PDF),
    ("docx", DocumentType.DOCX),
    ("txt", DocumentType.TXT),
])
def test_factory_get_loader_by_extension(ext, expected_type):
    loader = DocumentLoaderFactory.get_loader_by_extension(ext)
    assert loader.doc_type == expected_type


def test_factory_get_loader_by_extension_unsupported():
    with pytest.raises(ValueError):
        DocumentLoaderFactory.get_loader_by_extension("exe")
