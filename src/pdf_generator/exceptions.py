"""Custom exception hierarchy for PDF Generator.

This module defines a comprehensive exception hierarchy following best practices:
- All exceptions inherit from a base exception
- Specific exceptions for different failure modes
- Clear, actionable error messages

Time Complexity: N/A (exception definitions)
Space Complexity: O(1) per exception instance
"""


class PDFGeneratorError(Exception):
    """Base exception for all PDF Generator errors.

    All custom exceptions in this application inherit from this base class,
    allowing for catch-all error handling when needed.
    """


class DomainNotFoundError(PDFGeneratorError):
    """Raised when a requested domain YAML file cannot be found.

    This typically occurs when:
    - User specifies a non-existent domain name
    - Domain file was deleted or moved
    - Domain directory is not accessible
    """


class InvalidDomainConfigError(PDFGeneratorError):
    """Raised when domain YAML validation fails.

    This occurs when:
    - YAML syntax is invalid
    - Required fields are missing
    - Field values don't match schema requirements
    - Category weights don't sum to 1.0
    """


class TemplateRenderError(PDFGeneratorError):
    """Raised when Jinja2 template rendering fails.

    Common causes:
    - Template references undefined variable
    - Invalid Jinja2 syntax in template
    - Faker variable not found in faker_vars
    """


class PDFRenderError(PDFGeneratorError):
    """Raised when ReportLab PDF generation fails.

    This can occur due to:
    - Invalid font configuration
    - Disk I/O errors during write
    - Content too large for page dimensions
    """


class InvalidLanguageMixError(PDFGeneratorError):
    """Raised when language mix specification is invalid.

    Examples of invalid specs:
    - Values don't sum to 100%
    - Unknown language codes
    - Malformed format (not 'lang:percentage')
    """


class PathValidationError(PDFGeneratorError):
    """Raised when file path validation fails.

    Security-related errors:
    - Path traversal attempts (../)
    - Invalid characters in path
    - Path outside allowed directories
    """


class ConfigurationError(PDFGeneratorError):
    """Raised when system configuration is invalid.

    Examples:
    - Missing required environment variables
    - Invalid tool configurations
    - Incompatible dependency versions
    """
