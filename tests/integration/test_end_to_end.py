"""End-to-end integration tests."""

import uuid
from pathlib import Path

import pytest

from pdf_generator.domain_manager import DomainManager
from pdf_generator.models import LanguageCode
from pdf_generator.pdf_renderer import PDFRenderer, create_document_metadata
from pdf_generator.template_engine import LanguageSelector, TemplateEngine
from pdf_generator.utils import ensure_directory


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.integration
    def test_full_generation_pipeline(
        self, domains_dir_with_files: Path, temp_dir: Path
    ) -> None:
        """Test complete PDF generation pipeline."""
        # Initialize components
        domain_manager = DomainManager(domains_dir=domains_dir_with_files)
        domain_config = domain_manager.load_domain("banking")

        template_engine = TemplateEngine(domain_config, seed=42)
        language_selector = LanguageSelector(
            {LanguageCode.PL: 0.7, LanguageCode.EN: 0.3}, seed=42
        )
        pdf_renderer = PDFRenderer()

        output_dir = ensure_directory(temp_dir / "output")

        # Generate multiple PDFs
        count = 10
        generated_files = []

        for i in range(count):
            # Select language
            language = language_selector.select_random_language()

            # Render template
            category, content, _ = template_engine.render_random_document(language)

            # Create document metadata
            doc_id = str(uuid.uuid4())
            filename = f"banking_{category}_{language.value}_{doc_id[:8]}.pdf"
            pdf_path = output_dir / filename

            doc = create_document_metadata(
                doc_id=doc_id,
                domain="banking",
                category=category,
                language=language.value,
                content=content,
                output_path=pdf_path,
            )

            # Render PDF
            pdf_renderer.render_document(doc)

            generated_files.append(pdf_path)

        # Verify all files created
        assert len(generated_files) == count
        for pdf_file in generated_files:
            assert pdf_file.exists()
            assert pdf_file.stat().st_size > 0

    @pytest.mark.integration
    def test_domain_validation_workflow(
        self, domains_dir_with_files: Path
    ) -> None:
        """Test domain validation workflow."""
        manager = DomainManager(domains_dir=domains_dir_with_files)

        # List domains
        domains = manager.list_available_domains()
        assert len(domains) > 0

        # Validate each domain
        for domain_name in domains:
            is_valid, message = manager.validate_domain(domain_name)
            assert is_valid is True
            assert domain_name in message
