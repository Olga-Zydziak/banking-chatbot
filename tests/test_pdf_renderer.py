"""Tests for PDF renderer."""

from datetime import datetime
from pathlib import Path

from pdf_generator.models import GeneratedDocument, LanguageCode
from pdf_generator.pdf_renderer import PDFRenderer, create_document_metadata


class TestPDFRenderer:
    """Tests for PDFRenderer class."""

    def test_render_document_creates_file(self, temp_dir: Path) -> None:
        """Test that rendering creates PDF file."""
        renderer = PDFRenderer()

        doc = GeneratedDocument(
            doc_id="test-123",
            domain="banking",
            category="system_error",
            language=LanguageCode.PL,
            content="Test content with Polish characters: ąćęłńóśźż",
            timestamp=datetime.now(),
            pdf_path=temp_dir / "test.pdf",
        )

        renderer.render_document(doc)

        assert doc.pdf_path.exists()
        assert doc.pdf_path.stat().st_size > 0

    def test_render_long_content(self, temp_dir: Path) -> None:
        """Test rendering document with long content (multiple pages)."""
        renderer = PDFRenderer()

        # Create very long content
        long_content = "Test paragraph. " * 500

        doc = GeneratedDocument(
            doc_id="test-long",
            domain="banking",
            category="system_error",
            language=LanguageCode.PL,
            content=long_content,
            timestamp=datetime.now(),
            pdf_path=temp_dir / "long.pdf",
        )

        renderer.render_document(doc)

        assert doc.pdf_path.exists()
        # Long content should create larger PDF
        assert doc.pdf_path.stat().st_size > 5000

    def test_polish_characters_rendering(self, temp_dir: Path) -> None:
        """Test that Polish characters are rendered correctly."""
        renderer = PDFRenderer()

        polish_content = "Ąąćęłńóśźż ĄĆĘŁŃÓŚŹŻ"

        doc = GeneratedDocument(
            doc_id="test-polish",
            domain="banking",
            category="system_error",
            language=LanguageCode.PL,
            content=polish_content,
            timestamp=datetime.now(),
            pdf_path=temp_dir / "polish.pdf",
        )

        # Should not raise exception
        renderer.render_document(doc)
        assert doc.pdf_path.exists()


class TestCreateDocumentMetadata:
    """Tests for create_document_metadata helper."""

    def test_create_metadata(self, temp_dir: Path) -> None:
        """Test creating document metadata."""
        pdf_path = temp_dir / "test.pdf"

        doc = create_document_metadata(
            doc_id="test-123",
            domain="banking",
            category="system_error",
            language="pl",
            content="Test content",
            output_path=pdf_path,
        )

        assert doc.doc_id == "test-123"
        assert doc.domain == "banking"
        assert doc.category == "system_error"
        assert doc.language == LanguageCode.PL
        assert doc.content == "Test content"
        assert doc.pdf_path == pdf_path
        assert isinstance(doc.timestamp, datetime)
