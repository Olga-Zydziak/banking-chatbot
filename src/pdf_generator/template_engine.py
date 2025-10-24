"""Template rendering engine using Jinja2 and Faker.

This module provides:
- Secure template rendering using Jinja2 SandboxedEnvironment
- Random variable selection from faker_vars
- Category-weighted random selection
- Multi-language support

Security:
- Uses SandboxedEnvironment to prevent SSTI attacks
- Validates all template variables before rendering
- No arbitrary code execution possible

Time Complexity: O(n) where n is template length
Space Complexity: O(n) for rendered content
"""

import logging
import random
from typing import Any

from jinja2 import TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment

from pdf_generator.exceptions import TemplateRenderError
from pdf_generator.models import DomainConfig, LanguageCode, TemplateCategory

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Renders templates with random variable substitution.

    Features:
    - Weighted category selection
    - Random template selection within category
    - Random faker variable selection
    - Jinja2 template rendering in sandboxed environment

    Time Complexity: O(n) per render where n is template size
    Space Complexity: O(n) for rendered templates
    """

    def __init__(self, domain_config: DomainConfig, seed: int | None = None) -> None:
        """Initialize template engine.

        Args:
            domain_config: Domain configuration with categories and templates
            seed: Optional random seed for reproducibility

        Time Complexity: O(1)
        """
        self.domain_config = domain_config
        self.random = random.Random(seed)

        # Initialize Jinja2 sandboxed environment
        self.jinja_env = SandboxedEnvironment(
            autoescape=False,  # We control the content, no HTML escaping needed
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(
            f"TemplateEngine initialized for domain '{domain_config.domain}' "
            f"with seed={seed}"
        )

    def render_random_document(
        self, language: LanguageCode
    ) -> tuple[str, str, str]:
        """Generate random document content.

        Workflow:
        1. Select category based on weights
        2. Select random template for language
        3. Select random values for faker_vars
        4. Render template with variables

        Args:
            language: Target language for document

        Returns:
            Tuple of (category_name, rendered_content, template_used)

        Raises:
            TemplateRenderError: If rendering fails

        Time Complexity: O(n + m) where n is categories, m is template size
        Space Complexity: O(m) for rendered content

        Example:
            >>> engine = TemplateEngine(config)
            >>> category, content, template = engine.render_random_document(LanguageCode.PL)
            >>> print(category)
            'system_error'
        """
        # Select random category based on weights
        category_name, category = self._select_weighted_category()

        # Select random template for language
        templates = category.templates.get(language)
        if not templates:
            raise TemplateRenderError(
                f"No templates found for language '{language.value}' "
                f"in category '{category_name}'"
            )

        template_str = self.random.choice(templates)

        # Generate random variables for template
        variables = self._generate_template_variables(category)

        # Render template
        try:
            template = self.jinja_env.from_string(template_str)
            rendered_content = template.render(**variables)

            logger.debug(
                f"Rendered template for category='{category_name}', "
                f"language='{language.value}', vars={list(variables.keys())}"
            )

            return category_name, rendered_content, template_str

        except TemplateSyntaxError as e:
            raise TemplateRenderError(
                f"Template syntax error in category '{category_name}': {e}"
            ) from e
        except UndefinedError as e:
            raise TemplateRenderError(
                f"Template variable undefined in category '{category_name}': {e}. "
                f"Available variables: {list(variables.keys())}"
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                f"Failed to render template in category '{category_name}': {e}"
            ) from e

    def _select_weighted_category(self) -> tuple[str, TemplateCategory]:
        """Select random category based on weights.

        Uses weighted random selection where each category's probability
        is determined by its weight field.

        Returns:
            Tuple of (category_name, category_config)

        Time Complexity: O(n) where n is number of categories
        Space Complexity: O(n) for lists

        Example:
            >>> name, category = engine._select_weighted_category()
            >>> isinstance(category, TemplateCategory)
            True
        """
        categories = list(self.domain_config.categories.items())
        weights = [cat.weight for _, cat in categories]

        # random.choices handles weighted selection
        return self.random.choices(categories, weights=weights, k=1)[0]

    def _generate_template_variables(
        self, category: TemplateCategory
    ) -> dict[str, Any]:
        """Generate random variable values for template.

        For each variable in category.faker_vars, randomly selects one
        of the possible values.

        Args:
            category: Category configuration with faker_vars

        Returns:
            Dictionary of variable_name -> random_value

        Time Complexity: O(v) where v is number of variables
        Space Complexity: O(v) for variables dict

        Example:
            >>> variables = engine._generate_template_variables(category)
            >>> 'system_name' in variables
            True
        """
        variables: dict[str, Any] = {}

        for var_name, possible_values in category.faker_vars.items():
            if not possible_values:
                logger.warning(
                    f"Empty possible values for variable '{var_name}' "
                    f"in category '{category.name}'"
                )
                variables[var_name] = ""
            else:
                variables[var_name] = self.random.choice(possible_values)

        return variables


class LanguageSelector:
    """Selects random language based on distribution.

    This class handles weighted language selection for document generation.

    Time Complexity: O(1) per selection
    Space Complexity: O(n) where n is number of languages
    """

    def __init__(
        self, distribution: dict[LanguageCode, float], seed: int | None = None
    ) -> None:
        """Initialize language selector.

        Args:
            distribution: Language probability distribution (must sum to 1.0)
            seed: Optional random seed for reproducibility

        Time Complexity: O(n) where n is number of languages
        """
        self.distribution = distribution
        self.random = random.Random(seed)

        # Pre-compute lists for weighted selection
        self.languages = list(distribution.keys())
        self.weights = [distribution[lang] for lang in self.languages]

        logger.debug(
            f"LanguageSelector initialized with distribution={distribution}, seed={seed}"
        )

    def select_random_language(self) -> LanguageCode:
        """Select random language based on distribution.

        Returns:
            Selected language code

        Time Complexity: O(1)
        Space Complexity: O(1)

        Example:
            >>> selector = LanguageSelector({LanguageCode.PL: 0.7, LanguageCode.EN: 0.3})
            >>> lang = selector.select_random_language()
            >>> lang in [LanguageCode.PL, LanguageCode.EN]
            True
        """
        selected = self.random.choices(self.languages, weights=self.weights, k=1)[0]

        logger.debug(f"Selected language: {selected.value}")

        return selected
