# Contributing to PDF Generator

Thank you for your interest in contributing! This document provides guidelines and instructions for development.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of Python type hints and Pydantic

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd banking-chatbot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -m pdf_generator list-domains
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the code quality standards below. All changes must:
- Pass `mypy --strict` with zero errors
- Pass `ruff check` with zero warnings
- Include comprehensive tests
- Have 100% type hint coverage
- Include Google-style docstrings

### 3. Run Quality Checks

```bash
# Format code
ruff format src/ tests/

# Run linter
ruff check src/ tests/

# Run type checker
mypy --strict src/pdf_generator/

# Run tests with coverage
pytest --cov=pdf_generator --cov-report=term-missing
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Quality Standards

### Type Hints (100% Coverage Required)

```python
# ✅ Good - Full type hints
def process_document(
    doc_id: str,
    content: str,
    language: LanguageCode
) -> GeneratedDocument:
    """Process document with full type safety."""
    pass

# ❌ Bad - Missing type hints
def process_document(doc_id, content, language):
    pass
```

### Docstrings (Google Style Required)

```python
def calculate_weight_distribution(
    categories: dict[str, TemplateCategory]
) -> dict[str, float]:
    """Calculate normalized weight distribution for categories.

    This function ensures weights sum to exactly 1.0 by normalizing
    the raw weights. Handles edge cases like zero-weight categories.

    Args:
        categories: Dictionary mapping category names to configurations

    Returns:
        Dictionary mapping category names to normalized weights (sum = 1.0)

    Raises:
        ValueError: If all category weights are zero

    Time Complexity: O(n) where n is number of categories
    Space Complexity: O(n) for result dictionary

    Example:
        >>> cats = {"cat1": TemplateCategory(weight=0.3), "cat2": TemplateCategory(weight=0.7)}
        >>> calculate_weight_distribution(cats)
        {'cat1': 0.3, 'cat2': 0.7}
    """
    pass
```

### Error Handling

```python
# ✅ Good - Specific exceptions
try:
    config = load_domain_config(domain_name)
except DomainNotFoundError as e:
    logger.error(f"Domain not found: {e}")
    raise
except InvalidDomainConfigError as e:
    logger.error(f"Invalid config: {e}")
    raise

# ❌ Bad - Bare except
try:
    config = load_domain_config(domain_name)
except:
    pass
```

### Testing Requirements

All new code must have comprehensive tests:

```python
import pytest
from pdf_generator.models import LanguageCode

class TestNewFeature:
    """Tests for new feature."""

    def test_happy_path(self) -> None:
        """Test normal operation."""
        result = new_feature("input")
        assert result == "expected"

    def test_error_handling(self) -> None:
        """Test error conditions."""
        with pytest.raises(ValueError, match="specific error"):
            new_feature("invalid")

    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ])
    def test_edge_cases(self, input: str, expected: int) -> None:
        """Test edge cases with parametrization."""
        assert new_feature(input) == expected
```

## Project Structure Conventions

### Module Responsibilities

- `models.py`: Pydantic models only, no business logic
- `exceptions.py`: Custom exception hierarchy
- `domain_manager.py`: YAML loading and domain management
- `template_engine.py`: Template rendering logic
- `pdf_renderer.py`: PDF generation (ReportLab wrapper)
- `cli.py`: CLI interface (Typer commands)
- `utils.py`: Helper functions (pure, side-effect free)

### Naming Conventions

```python
# Classes: PascalCase
class DomainManager:
    pass

# Functions/Methods: snake_case
def load_domain_config(domain_name: str) -> DomainConfig:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_DOCUMENT_COUNT = 10000

# Private functions: leading underscore
def _internal_helper() -> None:
    pass
```

## Testing Guidelines

### Test Organization

```
tests/
├── conftest.py              # Pytest fixtures
├── test_models.py           # Model validation tests
├── test_domain_manager.py   # Domain loading tests
├── test_template_engine.py  # Template rendering tests
├── test_pdf_renderer.py     # PDF generation tests
├── test_cli.py             # CLI interface tests
└── integration/
    └── test_end_to_end.py  # E2E integration tests
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_models.py

# Specific test
pytest tests/test_models.py::TestDomainConfig::test_weights_must_sum_to_one

# With coverage
pytest --cov=pdf_generator --cov-report=html
open htmlcov/index.html

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Coverage Requirements

- Minimum 80% overall coverage
- 100% coverage for critical paths (domain validation, template rendering)
- All edge cases must be tested

## Adding New Features

### Adding a New Domain Validator

1. Add validation method to `DomainConfig` in `models.py`:

```python
@model_validator(mode="after")
def validate_new_requirement(self) -> "DomainConfig":
    """Validate new requirement."""
    # Validation logic
    return self
```

2. Add test in `tests/test_models.py`:

```python
def test_new_validation_rule(self) -> None:
    """Test new validation rule."""
    with pytest.raises(ValidationError, match="expected error"):
        DomainConfig(...)
```

3. Update `domains/template.yaml` with documentation.

### Adding a New CLI Command

1. Add command to `cli.py`:

```python
@app.command()
def new_command(
    arg: str = typer.Argument(..., help="Description")
) -> None:
    """Command description."""
    try:
        # Implementation
        pass
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
```

2. Add test in `tests/test_cli.py`.

3. Update README.md with usage example.

## Common Tasks

### Updating Dependencies

```bash
# Update specific package
pip install --upgrade pydantic

# Regenerate lock file (if using)
pip freeze > requirements-dev.txt

# Test with new dependencies
pytest
mypy --strict src/pdf_generator/
```

### Adding a New Language

1. Add language to `LanguageCode` enum in `models.py`:

```python
class LanguageCode(str, Enum):
    PL = "pl"
    EN = "en"
    FR = "fr"  # New language
```

2. Update domain YAML files to include new language.

3. Add tests for new language code.

### Debugging Tips

```bash
# Run with verbose output
pytest -vv

# Run single test with print statements
pytest -s tests/test_models.py::test_specific

# Use debugger
pytest --pdb tests/test_models.py

# Check type hints
mypy --strict --show-error-codes src/pdf_generator/
```

## Git Workflow

### Branch Naming

- Features: `feature/description`
- Bugs: `fix/description`
- Docs: `docs/description`

### Commit Messages

```bash
# Good
feat: add medical domain support
fix: handle empty faker_vars in template engine
docs: update installation instructions

# Bad
Update code
Fixed stuff
WIP
```

### Pull Request Checklist

Before submitting PR, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy --strict`)
- [ ] Linting passes (`ruff check`)
- [ ] Code is formatted (`ruff format`)
- [ ] Coverage is ≥80% (`pytest --cov`)
- [ ] Documentation is updated (README, docstrings)
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with main branch

## Code Review Process

### For Reviewers

Check for:
1. **Type Safety**: All functions have type hints
2. **Documentation**: All public APIs have docstrings
3. **Tests**: New code has comprehensive tests
4. **Error Handling**: Specific exceptions, no bare `except`
5. **SOLID Principles**: Code follows clean architecture
6. **Performance**: No obvious performance issues

### For Contributors

Address review comments by:
1. Making requested changes
2. Adding tests for edge cases
3. Updating documentation
4. Re-running quality checks

## Getting Help

- **Questions**: Open GitHub Discussion
- **Bugs**: Create GitHub Issue with reproduction steps
- **Security**: Email security@example.com (do not create public issue)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
