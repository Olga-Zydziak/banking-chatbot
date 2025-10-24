"""Domain configuration management for PDF Generator.

This module handles:
- Loading domain configurations from YAML files
- Validating domain schemas using Pydantic
- Discovering available domains
- Caching domain configs for performance

Security:
- Uses yaml.safe_load() to prevent arbitrary code execution
- Validates all paths to prevent traversal attacks
- All YAML content validated through Pydantic before use

Time Complexity: O(n) where n is YAML file size
Space Complexity: O(n) for cached domain configs
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from pdf_generator.exceptions import DomainNotFoundError, InvalidDomainConfigError
from pdf_generator.models import DomainConfig, LanguageCode
from pdf_generator.utils import get_project_root

logger = logging.getLogger(__name__)


class DomainManager:
    """Manages domain configurations and YAML loading.

    This class provides:
    - Domain discovery from domains/ directory
    - YAML loading with validation
    - Config caching for performance
    - Clear error messages for validation failures

    Time Complexity: O(1) for cached lookups, O(n) for first load
    Space Complexity: O(d * n) where d is domain count, n is avg config size
    """

    def __init__(self, domains_dir: Path | None = None) -> None:
        """Initialize domain manager.

        Args:
            domains_dir: Optional custom domains directory path.
                        Defaults to project_root/domains/

        Time Complexity: O(1)
        """
        if domains_dir is None:
            domains_dir = get_project_root() / "domains"

        self.domains_dir = domains_dir
        self._cache: dict[str, DomainConfig] = {}

        logger.info(f"DomainManager initialized with domains_dir={self.domains_dir}")

    def load_domain(self, domain_name: str) -> DomainConfig:
        """Load and validate domain configuration.

        Args:
            domain_name: Domain identifier (e.g., "banking", "medical")

        Returns:
            Validated domain configuration

        Raises:
            DomainNotFoundError: If domain YAML file not found
            InvalidDomainConfigError: If YAML validation fails

        Time Complexity: O(1) if cached, O(n) for first load where n is file size
        Space Complexity: O(n) where n is config size

        Example:
            >>> manager = DomainManager()
            >>> config = manager.load_domain("banking")
            >>> config.domain
            'banking'
        """
        # Check cache first
        if domain_name in self._cache:
            logger.debug(f"Loading domain '{domain_name}' from cache")
            return self._cache[domain_name]

        # Construct path to domain YAML file
        domain_path = self.domains_dir / f"{domain_name}.yaml"

        if not domain_path.exists():
            available = self.list_available_domains()
            available_str = ", ".join(available) if available else "none"
            raise DomainNotFoundError(
                f"Domain '{domain_name}' not found at {domain_path}. "
                f"Available domains: {available_str}"
            )

        try:
            # Load YAML using safe_load (prevents code execution)
            with domain_path.open("r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)

            if raw_data is None:
                raise InvalidDomainConfigError(
                    f"Domain file '{domain_path}' is empty or invalid"
                )

            # Convert raw data to structured format for Pydantic
            structured_data = self._structure_yaml_data(raw_data, domain_name)

            # Validate through Pydantic model
            config = DomainConfig(**structured_data)

            # Cache validated config
            self._cache[domain_name] = config

            logger.info(
                f"Successfully loaded domain '{domain_name}' "
                f"with {len(config.categories)} categories"
            )

            return config

        except yaml.YAMLError as e:
            raise InvalidDomainConfigError(
                f"YAML syntax error in '{domain_path}': {e}"
            ) from e
        except ValidationError as e:
            # Format Pydantic validation errors for user-friendly output
            error_details = self._format_validation_errors(e)
            raise InvalidDomainConfigError(
                f"Validation failed for domain '{domain_name}':\n{error_details}"
            ) from e
        except Exception as e:
            raise InvalidDomainConfigError(
                f"Failed to load domain '{domain_name}': {e}"
            ) from e

    def list_available_domains(self) -> list[str]:
        """List all available domain names.

        Returns:
            Sorted list of domain names (without .yaml extension)

        Time Complexity: O(n log n) where n is number of YAML files
        Space Complexity: O(n) for domain name list

        Example:
            >>> manager = DomainManager()
            >>> manager.list_available_domains()
            ['banking', 'medical']
        """
        if not self.domains_dir.exists():
            logger.warning(f"Domains directory does not exist: {self.domains_dir}")
            return []

        domains = [
            path.stem
            for path in self.domains_dir.glob("*.yaml")
            if not path.name.startswith(".")  # Ignore hidden files
            and path.stem != "template"  # Ignore template file
        ]

        return sorted(domains)

    def validate_domain(self, domain_name: str) -> tuple[bool, str]:
        """Validate domain configuration without caching.

        Useful for CLI validation command.

        Args:
            domain_name: Domain to validate

        Returns:
            Tuple of (is_valid, message)

        Time Complexity: O(n) where n is config size
        Space Complexity: O(n)

        Example:
            >>> manager = DomainManager()
            >>> valid, msg = manager.validate_domain("banking")
            >>> print(msg)
            'Domain "banking" is valid with 4 categories'
        """
        try:
            # Temporarily clear cache to force fresh load
            self._cache.pop(domain_name, None)
            config = self.load_domain(domain_name)

            message = (
                f"Domain '{domain_name}' is valid:\n"
                f"  - Languages: {', '.join(lang.value for lang in config.languages)}\n"
                f"  - Categories: {len(config.categories)}\n"
                f"  - Total templates: {self._count_templates(config)}"
            )

            return True, message

        except (DomainNotFoundError, InvalidDomainConfigError) as e:
            return False, str(e)

    def _structure_yaml_data(self, raw_data: Any, domain_name: str) -> dict[str, Any]:
        """Convert raw YAML data to Pydantic-compatible structure.

        Args:
            raw_data: Raw data from YAML file
            domain_name: Domain name for validation

        Returns:
            Structured dictionary for Pydantic validation

        Raises:
            InvalidDomainConfigError: If data structure is invalid

        Time Complexity: O(n) where n is data size
        """
        if not isinstance(raw_data, dict):
            raise InvalidDomainConfigError(
                f"Domain YAML must be a dictionary, got {type(raw_data).__name__}"
            )

        # Convert categories to TemplateCategory format
        categories = raw_data.get("categories", {})
        structured_categories: dict[str, Any] = {}

        for cat_name, cat_data in categories.items():
            if not isinstance(cat_data, dict):
                raise InvalidDomainConfigError(
                    f"Category '{cat_name}' must be a dictionary"
                )

            # Convert language codes from strings to enums
            templates = cat_data.get("templates", {})
            structured_templates: dict[LanguageCode, list[str]] = {}

            for lang_str, template_list in templates.items():
                try:
                    lang = LanguageCode(lang_str)
                    structured_templates[lang] = template_list
                except ValueError:
                    valid_codes = ", ".join(code.value for code in LanguageCode)
                    raise InvalidDomainConfigError(
                        f"Invalid language code '{lang_str}' in category '{cat_name}'. "
                        f"Valid codes: {valid_codes}"
                    ) from None

            structured_categories[cat_name] = {
                "name": cat_name,
                "weight": cat_data.get("weight", 0.0),
                "templates": structured_templates,
                "faker_vars": cat_data.get("faker_vars", {}),
            }

        # Convert language list
        languages = raw_data.get("languages", [])
        structured_languages = []
        for lang_str in languages:
            try:
                structured_languages.append(LanguageCode(lang_str))
            except ValueError:
                valid_codes = ", ".join(code.value for code in LanguageCode)
                raise InvalidDomainConfigError(
                    f"Invalid language code '{lang_str}'. Valid codes: {valid_codes}"
                ) from None

        return {
            "domain": raw_data.get("domain", domain_name),
            "languages": structured_languages,
            "categories": structured_categories,
        }

    def _format_validation_errors(self, error: ValidationError) -> str:
        """Format Pydantic validation errors for human readability.

        Args:
            error: Pydantic validation error

        Returns:
            Formatted error message

        Time Complexity: O(n) where n is number of errors
        """
        lines = []
        for err in error.errors():
            location = " -> ".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            lines.append(f"  • {location}: {message}")

        return "\n".join(lines)

    def _count_templates(self, config: DomainConfig) -> int:
        """Count total templates across all categories and languages.

        Args:
            config: Domain configuration

        Returns:
            Total template count

        Time Complexity: O(n * m) where n is categories, m is languages
        """
        total = 0
        for category in config.categories.values():
            for templates in category.templates.values():
                total += len(templates)
        return total
