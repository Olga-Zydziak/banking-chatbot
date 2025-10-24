"""Pydantic V2 data models for PDF Generator.

This module defines the core data structures with comprehensive validation:
- LanguageCode: Supported languages (Polish, English)
- TemplateCategory: Category configuration with templates and variables
- DomainConfig: Complete domain specification
- GeneratedDocument: Metadata for generated PDFs
- LanguageMix: Language distribution specification

All models use Pydantic V2 for runtime validation and type safety.

Time Complexity: O(n) for validation where n is input size
Space Complexity: O(n) for model instances
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class LanguageCode(str, Enum):
    """Supported language codes following ISO 639-1.

    PL: Polish (pl_PL locale)
    EN: English (en_US locale)
    """

    PL = "pl"
    EN = "en"


class TemplateCategory(BaseModel):
    """Configuration for a single template category.

    Attributes:
        name: Category identifier (e.g., "system_error", "test_results")
        weight: Probability of selection (0.0 to 1.0, must sum to 1.0 across categories)
        templates: Jinja2 templates per language
        faker_vars: Variables for template substitution (variable name -> possible values)

    Time Complexity: O(1) for validation
    Space Complexity: O(t + v) where t is template count, v is faker_vars size
    """

    name: str = Field(min_length=1, max_length=100)
    weight: float = Field(ge=0.0, le=1.0)
    templates: dict[LanguageCode, list[str]]
    faker_vars: dict[str, list[str | int | float]] = Field(default_factory=dict)

    @field_validator("templates")
    @classmethod
    def validate_templates_not_empty(
        cls, v: dict[LanguageCode, list[str]]
    ) -> dict[LanguageCode, list[str]]:
        """Ensure each language has at least one template.

        Args:
            v: Templates dictionary to validate

        Returns:
            Validated templates dictionary

        Raises:
            ValueError: If any language has empty template list

        Time Complexity: O(n) where n is number of languages
        """
        for lang, templates in v.items():
            if not templates:
                raise ValueError(
                    f"Language '{lang}' must have at least one template"
                )
        return v

    @field_validator("faker_vars")
    @classmethod
    def validate_faker_vars_not_empty(
        cls, v: dict[str, list[str | int | float]]
    ) -> dict[str, list[str | int | float]]:
        """Ensure each faker variable has at least one possible value.

        Args:
            v: Faker variables dictionary to validate

        Returns:
            Validated faker_vars dictionary

        Raises:
            ValueError: If any variable has empty value list

        Time Complexity: O(n) where n is number of variables
        """
        for var_name, values in v.items():
            if not values:
                raise ValueError(
                    f"Faker variable '{var_name}' must have at least one value"
                )
        return v


class DomainConfig(BaseModel):
    """Complete domain specification loaded from YAML.

    Attributes:
        domain: Domain identifier (lowercase, underscores only)
        languages: Supported languages for this domain
        categories: Category configurations with templates and weights

    Time Complexity: O(n + m) for validation where n is categories, m is templates
    Space Complexity: O(n * m) where n is categories, m is average templates per category
    """

    domain: str = Field(pattern=r"^[a-z_]+$", min_length=1, max_length=50)
    languages: list[LanguageCode] = Field(min_length=1)
    categories: dict[str, TemplateCategory]

    @field_validator("categories")
    @classmethod
    def validate_categories_not_empty(
        cls, v: dict[str, TemplateCategory]
    ) -> dict[str, TemplateCategory]:
        """Ensure at least one category is defined.

        Args:
            v: Categories dictionary to validate

        Returns:
            Validated categories dictionary

        Raises:
            ValueError: If categories dictionary is empty

        Time Complexity: O(1)
        """
        if not v:
            raise ValueError("Domain must have at least one category")
        return v

    @model_validator(mode="after")
    def validate_weights_sum_to_one(self) -> "DomainConfig":
        """Ensure category weights sum to approximately 1.0.

        Allows for floating-point precision tolerance of 0.01.

        Returns:
            Self after validation

        Raises:
            ValueError: If weights don't sum to 1.0 (within tolerance)

        Time Complexity: O(n) where n is number of categories
        """
        total_weight = sum(cat.weight for cat in self.categories.values())
        if not abs(total_weight - 1.0) < 0.01:
            raise ValueError(
                f"Category weights must sum to 1.0, got {total_weight:.3f}"
            )
        return self

    @model_validator(mode="after")
    def validate_category_languages(self) -> "DomainConfig":
        """Ensure all categories support all domain languages.

        Returns:
            Self after validation

        Raises:
            ValueError: If category doesn't have templates for all languages

        Time Complexity: O(n * m) where n is categories, m is languages
        """
        domain_langs = set(self.languages)
        for cat_name, category in self.categories.items():
            cat_langs = set(category.templates.keys())
            missing_langs = domain_langs - cat_langs
            if missing_langs:
                raise ValueError(
                    f"Category '{cat_name}' missing templates for languages: "
                    f"{', '.join(lang.value for lang in missing_langs)}"
                )
        return self


class LanguageMix(BaseModel):
    """Language distribution specification for document generation.

    Attributes:
        distribution: Mapping of language code to probability (0.0 to 1.0)

    Time Complexity: O(n) for validation where n is number of languages
    Space Complexity: O(n) where n is number of languages
    """

    distribution: dict[LanguageCode, float]

    @field_validator("distribution")
    @classmethod
    def validate_distribution_sums_to_one(
        cls, v: dict[LanguageCode, float]
    ) -> dict[LanguageCode, float]:
        """Ensure language probabilities sum to approximately 1.0.

        Args:
            v: Distribution dictionary to validate

        Returns:
            Validated distribution

        Raises:
            ValueError: If probabilities don't sum to 1.0 (within tolerance)

        Time Complexity: O(n) where n is number of languages
        """
        total = sum(v.values())
        if not abs(total - 1.0) < 0.01:
            raise ValueError(
                f"Language mix probabilities must sum to 1.0, got {total:.3f}"
            )
        return v

    @field_validator("distribution")
    @classmethod
    def validate_probabilities_in_range(
        cls, v: dict[LanguageCode, float]
    ) -> dict[LanguageCode, float]:
        """Ensure all probabilities are between 0.0 and 1.0.

        Args:
            v: Distribution dictionary to validate

        Returns:
            Validated distribution

        Raises:
            ValueError: If any probability is outside [0.0, 1.0] range

        Time Complexity: O(n) where n is number of languages
        """
        for lang, prob in v.items():
            if not 0.0 <= prob <= 1.0:
                raise ValueError(
                    f"Language '{lang}' probability must be in [0.0, 1.0], got {prob}"
                )
        return v


class GeneratedDocument(BaseModel):
    """Metadata for a generated PDF document.

    Attributes:
        doc_id: Unique document identifier (UUID)
        domain: Domain name (e.g., "banking", "medical")
        category: Category name (e.g., "system_error", "test_results")
        language: Document language
        content: Rendered template content
        timestamp: Generation timestamp
        pdf_path: Absolute path to generated PDF file

    Time Complexity: O(1) for creation
    Space Complexity: O(n) where n is content length
    """

    doc_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    category: str = Field(min_length=1)
    language: LanguageCode
    content: str = Field(min_length=1)
    timestamp: datetime
    pdf_path: Path

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_path_extension(cls, v: Path) -> Path:
        """Ensure PDF path has .pdf extension.

        Args:
            v: Path to validate

        Returns:
            Validated path

        Raises:
            ValueError: If path doesn't end with .pdf

        Time Complexity: O(1)
        """
        if v.suffix.lower() != ".pdf":
            raise ValueError(f"PDF path must end with .pdf, got {v.suffix}")
        return v


class GenerationConfig(BaseModel):
    """Configuration for PDF generation run.

    Attributes:
        domain: Domain to use for generation
        count: Number of PDFs to generate
        language_mix: Language distribution
        output_dir: Output directory path
        seed: Random seed for reproducibility (optional)

    Time Complexity: O(1) for validation
    Space Complexity: O(1)
    """

    domain: str = Field(pattern=r"^[a-z_]+$", min_length=1)
    count: int = Field(ge=1, le=10000)
    language_mix: LanguageMix
    output_dir: Path
    seed: int | None = Field(default=None, ge=0)

    @field_validator("count")
    @classmethod
    def validate_count_reasonable(cls, v: int) -> int:
        """Ensure document count is reasonable to prevent resource exhaustion.

        Args:
            v: Count to validate

        Returns:
            Validated count

        Raises:
            ValueError: If count exceeds maximum (10,000)

        Time Complexity: O(1)
        """
        if v > 10000:
            raise ValueError(
                f"Document count must not exceed 10,000 for safety, got {v}"
            )
        return v
