# PDF Generator

Production-grade synthetic PDF generator for knowledge base training and testing.

## Overview

PDF Generator is an extensible, domain-agnostic system for creating synthetic support ticket PDFs. The architecture allows non-programmers to add new domains (banking, medical, legal, etc.) via YAML configuration files **without touching any Python code**.

### Key Features

- **Plugin-based Domain System**: Domains defined in YAML, not hardcoded
- **Multi-language Support**: Polish (pl) and English (en) with configurable distribution
- **Template-based Generation**: Jinja2 templates with Faker variable injection
- **Production-ready**: Type-safe (mypy --strict), tested (80%+ coverage), documented
- **Clean Architecture**: SOLID principles, separation of concerns, dependency inversion

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd banking-chatbot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package with dependencies
pip install -e ".[dev]"
```

### Generate Your First PDFs

```bash
# Generate 100 banking PDFs (70% Polish, 30% English)
python -m pdf_generator generate \
  --domain banking \
  --count 100 \
  --lang-mix pl:70,en:30 \
  --output ./output

# Generate 50 medical PDFs (100% Polish)
python -m pdf_generator generate \
  --domain medical \
  --count 50 \
  --lang-mix pl:100 \
  --output ./output/medical

# Use seed for reproducible generation
python -m pdf_generator generate \
  --domain banking \
  --count 10 \
  --seed 42
```

### Validate Domain Configuration

```bash
# Validate specific domain
python -m pdf_generator validate banking

# List all available domains
python -m pdf_generator list-domains
```

## Architecture

### Project Structure

```
pdf_generator/
├── src/pdf_generator/          # Main package
│   ├── cli.py                  # Typer CLI interface
│   ├── models.py               # Pydantic V2 data models
│   ├── domain_manager.py       # YAML loading + validation
│   ├── template_engine.py      # Jinja2 + Faker integration
│   ├── pdf_renderer.py         # ReportLab PDF generation
│   ├── exceptions.py           # Custom exception hierarchy
│   └── utils.py                # Helper functions
├── domains/                    # Domain configurations
│   ├── banking.yaml            # Banking support tickets
│   ├── medical.yaml            # Medical queries
│   └── template.yaml           # Boilerplate for new domains
├── tests/                      # Comprehensive test suite
│   ├── test_models.py
│   ├── test_domain_manager.py
│   ├── test_template_engine.py
│   └── integration/
└── pyproject.toml              # Modern Python packaging
```

### Core Components

#### 1. Domain Manager (`domain_manager.py`)
- Loads domain configurations from YAML files
- Validates schemas using Pydantic
- Caches configs for performance
- **Security**: Uses `yaml.safe_load()` to prevent code execution

#### 2. Template Engine (`template_engine.py`)
- Renders Jinja2 templates with random variable substitution
- Weighted category selection
- **Security**: Uses `SandboxedEnvironment` to prevent SSTI attacks

#### 3. PDF Renderer (`pdf_renderer.py`)
- Generates clean, professional PDFs using ReportLab
- Unicode support for Polish characters (ąćęłńóśźż)
- Embedded metadata (category, language, timestamp)
- **Reliability**: Atomic file writes (temp → rename)

#### 4. CLI (`cli.py`)
- User-friendly Typer-based command-line interface
- Rich progress bars and formatted output
- Clear error messages with actionable guidance

## Adding New Domains

### Step 1: Copy Template

```bash
cp domains/template.yaml domains/your_domain.yaml
```

### Step 2: Edit Configuration

```yaml
domain: your_domain  # Must match filename (without .yaml)
languages: [pl, en]

categories:
  category_name_1:
    weight: 0.4  # Probability (all weights must sum to 1.0)
    templates:
      pl:
        - "Polski szablon z {variable1} i {variable2}."
      en:
        - "English template with {variable1} and {variable2}."
    faker_vars:
      variable1: ["value1", "value2", "value3"]
      variable2: [100, 200, 300]

  category_name_2:
    weight: 0.6
    templates:
      pl:
        - "Inny szablon używający {another_var}."
      en:
        - "Another template using {another_var}."
    faker_vars:
      another_var: ["option_a", "option_b"]
```

### Step 3: Validate

```bash
python -m pdf_generator validate your_domain
```

### Step 4: Generate PDFs

```bash
python -m pdf_generator generate --domain your_domain --count 10
```

That's it! **No Python code changes required.**

## Configuration Reference

### Domain YAML Schema

```yaml
domain: string                    # Domain identifier (^[a-z_]+$)
languages: [pl, en]              # Supported languages

categories:                       # Category definitions
  category_name:
    weight: float                 # Selection probability (0.0-1.0)
    templates:
      pl: [string, ...]          # Polish templates
      en: [string, ...]          # English templates
    faker_vars:                   # Variable definitions
      var_name: [value, ...]     # Possible values (any type)
```

### Validation Rules

1. Domain name must match `^[a-z_]+$` pattern
2. All category weights must sum to 1.0 (±0.01 tolerance)
3. Each category must have templates for all domain languages
4. Each template variable `{var}` must be defined in `faker_vars`
5. Each `faker_vars` list must have at least one value

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy --strict src/pdf_generator/

# Run linting
ruff check src/ tests/

# Run formatting
ruff format src/ tests/
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=pdf_generator --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py

# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -v
```

### Code Quality Standards

This project maintains **strict quality standards**:

- ✅ `mypy --strict` compliance (zero errors)
- ✅ `ruff check` compliance (zero warnings)
- ✅ 100% type hint coverage
- ✅ 80%+ test coverage
- ✅ Google-style docstrings with complexity analysis
- ✅ PEP 8 compliant

## Security

### YAML Injection Prevention
- Uses `yaml.safe_load()` exclusively
- All YAML validated through Pydantic before use

### Path Traversal Prevention
- All paths validated (no `..` segments)
- Domain names restricted to `^[a-z_]+$` pattern

### Template Injection Prevention (SSTI)
- Uses `jinja2.SandboxedEnvironment`
- No arbitrary code execution possible

### Resource Exhaustion Protection
- Document count limited to 10,000
- File writes are atomic and safe

## Performance

### Benchmarks

- **Generation Speed**: ~10-20 PDFs/second (typical)
- **Memory Usage**: O(1) per document (streaming generation)
- **Disk I/O**: Atomic writes prevent corruption

### Optimization Tips

```bash
# Use seed for deterministic generation (faster)
python -m pdf_generator generate --domain banking --count 1000 --seed 42

# Generate in batches for large datasets
for i in {1..10}; do
  python -m pdf_generator generate --domain banking --count 1000 --output batch_$i
done
```

## Troubleshooting

### Common Issues

#### Domain not found
```bash
$ python -m pdf_generator generate --domain mydom
Error: Domain 'mydom' not found. Available domains: banking, medical
```
**Solution**: Check spelling or add new domain YAML file.

#### Weights don't sum to 1.0
```yaml
# ❌ Wrong
categories:
  cat1: {weight: 0.3}
  cat2: {weight: 0.5}  # Sum = 0.8

# ✅ Correct
categories:
  cat1: {weight: 0.4}
  cat2: {weight: 0.6}  # Sum = 1.0
```

#### Missing language templates
```yaml
# ❌ Wrong (domain has 'en', category doesn't)
domain: test
languages: [pl, en]
categories:
  cat1:
    templates:
      pl: ["test"]  # Missing 'en'

# ✅ Correct
categories:
  cat1:
    templates:
      pl: ["test"]
      en: ["test"]
```

## License

MIT License - see LICENSE file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Support

- Issues: https://github.com/your-org/pdf-generator/issues
- Documentation: This README and inline docstrings
- Examples: See `domains/` directory for working examples
