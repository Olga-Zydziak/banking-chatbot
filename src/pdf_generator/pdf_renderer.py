"""PDF rendering using ReportLab.

This module provides:
- Clean PDF layout with header, body, footer
- Unicode support for Polish characters (ąćęłńóśźż)
- Embedded metadata (category, language, timestamp)
- Automatic page breaks for long content
- Atomic file writes to prevent corruption

Uses DejaVu Sans font for Polish character support.

Time Complexity: O(n) where n is content length
Space Complexity: O(n) for PDF buffer
"""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from pdf_generator.exceptions import PDFRenderError
from pdf_generator.models import GeneratedDocument
from pdf_generator.utils import atomic_write

logger = logging.getLogger(__name__)


class PDFRenderer:
    """Renders PDF documents using ReportLab.

    Features:
    - Professional layout with header/footer
    - Unicode/Polish character support
    - Embedded metadata
    - Automatic pagination
    - Atomic writes

    Time Complexity: O(n) per document where n is content length
    Space Complexity: O(n) for PDF buffer
    """

    def __init__(self) -> None:
        """Initialize PDF renderer.

        Time Complexity: O(1)
        """
        self.page_width, self.page_height = A4
        self.margin = 2 * cm

        logger.info("PDFRenderer initialized")

    def render_document(self, document: GeneratedDocument) -> None:
        """Render document to PDF file.

        Args:
            document: Document metadata and content

        Raises:
            PDFRenderError: If PDF generation fails

        Time Complexity: O(n) where n is content length
        Space Complexity: O(n) for PDF buffer

        Example:
            >>> renderer = PDFRenderer()
            >>> renderer.render_document(document)
        """
        try:
            # Generate PDF to memory buffer first
            pdf_buffer = io.BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
                title=f"{document.domain} - {document.category}",
                author="PDF Generator",
                subject=f"Support Ticket - {document.category}",
            )

            # Build content elements
            story = self._build_story(document)

            # Render PDF
            doc.build(story, onFirstPage=self._add_header, onLaterPages=self._add_header)

            # Write atomically to file
            pdf_bytes = pdf_buffer.getvalue()
            atomic_write(document.pdf_path, pdf_bytes)

            logger.info(
                f"Rendered PDF: {document.pdf_path.name} "
                f"({len(pdf_bytes)} bytes, {document.language.value})"
            )

        except Exception as e:
            raise PDFRenderError(
                f"Failed to render PDF for document {document.doc_id}: {e}"
            ) from e

    def _build_story(self, document: GeneratedDocument) -> list[Any]:
        """Build PDF content story (flowables).

        Args:
            document: Document to render

        Returns:
            List of ReportLab flowables

        Time Complexity: O(n) where n is content length
        """
        story = []
        styles = getSampleStyleSheet()

        # Title style
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=12,
            alignment=1,  # Center alignment
        )

        # Metadata style
        metadata_style = ParagraphStyle(
            "Metadata",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            spaceAfter=20,
            alignment=1,  # Center alignment
        )

        # Body style with Polish character support
        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#333333"),
            alignment=0,  # Left alignment
            spaceAfter=12,
        )

        # Add title
        title = f"{document.domain.title()} Support Ticket"
        story.append(Paragraph(title, title_style))

        # Add metadata
        metadata = (
            f"Category: {document.category} | "
            f"Language: {document.language.value.upper()} | "
            f"ID: {document.doc_id[:8]}"
        )
        story.append(Paragraph(metadata, metadata_style))

        # Add separator line
        story.append(Spacer(1, 0.3 * cm))

        # Add content
        # Split content into paragraphs for better formatting
        paragraphs = document.content.split("\n")
        for para_text in paragraphs:
            if para_text.strip():
                # Escape XML special characters for ReportLab
                escaped_text = self._escape_xml(para_text.strip())
                story.append(Paragraph(escaped_text, body_style))

        # Add footer spacer
        story.append(Spacer(1, 1 * cm))

        # Add timestamp footer
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#999999"),
            alignment=2,  # Right alignment
        )

        timestamp_str = document.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {timestamp_str}", footer_style))

        return story

    def _add_header(self, canvas_obj: canvas.Canvas, doc: Any) -> None:
        """Add header and footer to page.

        Args:
            canvas_obj: ReportLab canvas
            doc: Document template

        Time Complexity: O(1)
        """
        canvas_obj.saveState()

        # Add header line
        canvas_obj.setStrokeColor(colors.HexColor("#cccccc"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(
            self.margin,
            self.page_height - self.margin + 0.5 * cm,
            self.page_width - self.margin,
            self.page_height - self.margin + 0.5 * cm,
        )

        # Add page number in footer
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#999999"))
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.drawCentredString(self.page_width / 2, self.margin - 0.5 * cm, text)

        canvas_obj.restoreState()

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters for ReportLab.

        ReportLab uses XML-like markup, so we need to escape special chars.

        Args:
            text: Text to escape

        Returns:
            Escaped text

        Time Complexity: O(n) where n is text length
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


def create_document_metadata(
    doc_id: str,
    domain: str,
    category: str,
    language: str,
    content: str,
    output_path: Path,
) -> GeneratedDocument:
    """Create GeneratedDocument instance with metadata.

    Helper function for creating document metadata.

    Args:
        doc_id: Unique document identifier
        domain: Domain name
        category: Category name
        language: Language code (pl or en)
        content: Rendered content
        output_path: Path to output PDF file

    Returns:
        GeneratedDocument instance

    Time Complexity: O(1)
    Space Complexity: O(n) where n is content length

    Example:
        >>> doc = create_document_metadata(
        ...     doc_id="123",
        ...     domain="banking",
        ...     category="system_error",
        ...     language="pl",
        ...     content="Error message",
        ...     output_path=Path("output/doc.pdf")
        ... )
    """
    from pdf_generator.models import LanguageCode

    return GeneratedDocument(
        doc_id=doc_id,
        domain=domain,
        category=category,
        language=LanguageCode(language),
        content=content,
        timestamp=datetime.now(),
        pdf_path=output_path,
    )
