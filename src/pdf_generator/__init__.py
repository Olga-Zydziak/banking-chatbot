"""PDF Generator - Synthetic Support Ticket Generator.

A production-grade system for generating domain-specific synthetic PDF documents
for knowledge base training and testing.

Features:
- Plugin-based domain system (YAML configuration)
- Multi-language support (Polish, English)
- Template-based content generation (Jinja2 + Faker)
- Clean PDF output with metadata
- Type-safe implementation (mypy --strict compliant)

Example:
    >>> from pdf_generator.domain_manager import DomainManager
    >>> manager = DomainManager()
    >>> config = manager.load_domain("banking")
    >>> print(config.domain)
    'banking'

Time Complexity: Varies per component
Space Complexity: Varies per component
"""

__version__ = "1.0.0"
__author__ = "PDF Generator Team"
__license__ = "MIT"

# Public API exports
from pdf_generator.domain_manager import DomainManager
from pdf_generator.exceptions import (
    ConfigurationError,
    DomainNotFoundError,
    InvalidDomainConfigError,
    InvalidLanguageMixError,
    PathValidationError,
    PDFGeneratorError,
    PDFRenderError,
    TemplateRenderError,
)
from pdf_generator.models import (
    DomainConfig,
    GeneratedDocument,
    GenerationConfig,
    LanguageCode,
    LanguageMix,
    TemplateCategory,
)
from pdf_generator.pdf_renderer import PDFRenderer, create_document_metadata
from pdf_generator.template_engine import LanguageSelector, TemplateEngine
from pdf_generator.utils import (
    ensure_directory,
    format_file_size,
    parse_language_mix,
    validate_output_path,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core managers
    "DomainManager",
    "TemplateEngine",
    "LanguageSelector",
    "PDFRenderer",
    # Models
    "DomainConfig",
    "TemplateCategory",
    "LanguageCode",
    "LanguageMix",
    "GeneratedDocument",
    "GenerationConfig",
    # Exceptions
    "PDFGeneratorError",
    "DomainNotFoundError",
    "InvalidDomainConfigError",
    "TemplateRenderError",
    "PDFRenderError",
    "InvalidLanguageMixError",
    "PathValidationError",
    "ConfigurationError",
    # Utilities
    "validate_output_path",
    "parse_language_mix",
    "ensure_directory",
    "format_file_size",
    "create_document_metadata",
]
