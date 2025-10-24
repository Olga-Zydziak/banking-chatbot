"""Tests for Pydantic models."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from pdf_generator.models import (
    DomainConfig,
    GeneratedDocument,
    GenerationConfig,
    LanguageCode,
    LanguageMix,
    TemplateCategory,
)


class TestTemplateCategory:
    """Tests for TemplateCategory model."""

    def test_valid_category(self, sample_banking_category: TemplateCategory) -> None:
        """Test creating valid template category."""
        assert sample_banking_category.name == "system_error"
        assert sample_banking_category.weight == 0.5
        assert LanguageCode.PL in sample_banking_category.templates
        assert len(sample_banking_category.faker_vars) == 2

    def test_empty_templates_raises_error(self) -> None:
        """Test that empty template list raises validation error."""
        with pytest.raises(ValidationError, match="must have at least one template"):
            TemplateCategory(
                name="test",
                weight=1.0,
                templates={LanguageCode.PL: []},
                faker_vars={},
            )

    def test_empty_faker_vars_raises_error(self) -> None:
        """Test that empty faker_vars list raises validation error."""
        with pytest.raises(ValidationError, match="must have at least one value"):
            TemplateCategory(
                name="test",
                weight=1.0,
                templates={LanguageCode.PL: ["test"]},
                faker_vars={"var1": []},
            )


class TestDomainConfig:
    """Tests for DomainConfig model."""

    def test_valid_domain_config(self, sample_domain_config: DomainConfig) -> None:
        """Test creating valid domain configuration."""
        assert sample_domain_config.domain == "banking"
        assert len(sample_domain_config.languages) == 2
        assert len(sample_domain_config.categories) == 2

    def test_weights_must_sum_to_one(self) -> None:
        """Test that category weights must sum to 1.0."""
        with pytest.raises(ValidationError, match="must sum to 1.0"):
            DomainConfig(
                domain="test",
                languages=[LanguageCode.PL],
                categories={
                    "cat1": TemplateCategory(
                        name="cat1",
                        weight=0.3,
                        templates={LanguageCode.PL: ["test"]},
                        faker_vars={},
                    ),
                    "cat2": TemplateCategory(
                        name="cat2",
                        weight=0.5,
                        templates={LanguageCode.PL: ["test"]},
                        faker_vars={},
                    ),
                },
            )

    def test_invalid_domain_name_pattern(self) -> None:
        """Test that domain name must match pattern."""
        with pytest.raises(ValidationError):
            DomainConfig(
                domain="Invalid-Domain!",
                languages=[LanguageCode.PL],
                categories={},
            )

    def test_missing_language_templates(self) -> None:
        """Test that all categories must have templates for all languages."""
        with pytest.raises(
            ValidationError, match="missing templates for languages"
        ):
            DomainConfig(
                domain="test",
                languages=[LanguageCode.PL, LanguageCode.EN],
                categories={
                    "cat1": TemplateCategory(
                        name="cat1",
                        weight=1.0,
                        templates={LanguageCode.PL: ["test"]},
                        faker_vars={},
                    )
                },
            )


class TestLanguageMix:
    """Tests for LanguageMix model."""

    def test_valid_language_mix(self) -> None:
        """Test creating valid language mix."""
        mix = LanguageMix(
            distribution={LanguageCode.PL: 0.7, LanguageCode.EN: 0.3}
        )
        assert mix.distribution[LanguageCode.PL] == 0.7
        assert mix.distribution[LanguageCode.EN] == 0.3

    def test_distribution_must_sum_to_one(self) -> None:
        """Test that distribution must sum to 1.0."""
        with pytest.raises(ValidationError, match="must sum to 1.0"):
            LanguageMix(distribution={LanguageCode.PL: 0.5, LanguageCode.EN: 0.3})

    def test_probability_out_of_range(self) -> None:
        """Test that probabilities must be in [0.0, 1.0] range."""
        with pytest.raises(ValidationError, match="must be in"):
            LanguageMix(distribution={LanguageCode.PL: 1.5})


class TestGeneratedDocument:
    """Tests for GeneratedDocument model."""

    def test_valid_document(self, temp_dir: Path) -> None:
        """Test creating valid generated document."""
        pdf_path = temp_dir / "test.pdf"
        doc = GeneratedDocument(
            doc_id="test-123",
            domain="banking",
            category="system_error",
            language=LanguageCode.PL,
            content="Test content",
            timestamp=datetime.now(),
            pdf_path=pdf_path,
        )
        assert doc.doc_id == "test-123"
        assert doc.domain == "banking"
        assert doc.pdf_path.suffix == ".pdf"

    def test_invalid_pdf_extension(self, temp_dir: Path) -> None:
        """Test that PDF path must have .pdf extension."""
        with pytest.raises(ValidationError, match="must end with .pdf"):
            GeneratedDocument(
                doc_id="test-123",
                domain="banking",
                category="system_error",
                language=LanguageCode.PL,
                content="Test content",
                timestamp=datetime.now(),
                pdf_path=temp_dir / "test.txt",
            )


class TestGenerationConfig:
    """Tests for GenerationConfig model."""

    def test_valid_config(self, temp_dir: Path) -> None:
        """Test creating valid generation config."""
        config = GenerationConfig(
            domain="banking",
            count=100,
            language_mix=LanguageMix(distribution={LanguageCode.PL: 1.0}),
            output_dir=temp_dir,
            seed=42,
        )
        assert config.domain == "banking"
        assert config.count == 100
        assert config.seed == 42

    def test_count_exceeds_maximum(self, temp_dir: Path) -> None:
        """Test that count cannot exceed maximum."""
        with pytest.raises(ValidationError):
            GenerationConfig(
                domain="banking",
                count=20000,
                language_mix=LanguageMix(distribution={LanguageCode.PL: 1.0}),
                output_dir=temp_dir,
            )
