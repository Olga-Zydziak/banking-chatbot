"""Pytest fixtures for PDF Generator tests."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdf_generator.models import DomainConfig, LanguageCode, TemplateCategory


@pytest.fixture
def temp_dir() -> Path:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_banking_category() -> TemplateCategory:
    """Create sample banking category for testing."""
    return TemplateCategory(
        name="system_error",
        weight=0.5,
        templates={
            LanguageCode.PL: [
                "Nie mogę zalogować się do systemu {system_name}.",
                "Błąd {error_code} w systemie {system_name}.",
            ],
            LanguageCode.EN: [
                "Cannot log into {system_name}.",
                "Error {error_code} in {system_name}.",
            ],
        },
        faker_vars={
            "system_name": ["Internet Banking", "Mobile App"],
            "error_code": ["500", "503", "AUTH_FAILED"],
        },
    )


@pytest.fixture
def sample_domain_config(
    sample_banking_category: TemplateCategory,
) -> DomainConfig:
    """Create sample domain configuration for testing."""
    return DomainConfig(
        domain="banking",
        languages=[LanguageCode.PL, LanguageCode.EN],
        categories={
            "system_error": sample_banking_category,
            "account_access": TemplateCategory(
                name="account_access",
                weight=0.5,
                templates={
                    LanguageCode.PL: ["Brak dostępu do konta {account}."],
                    LanguageCode.EN: ["Cannot access account {account}."],
                },
                faker_vars={"account": ["123456", "789012"]},
            ),
        },
    )


@pytest.fixture
def sample_yaml_content() -> dict[str, Any]:
    """Create sample YAML content for domain config."""
    return {
        "domain": "test_domain",
        "languages": ["pl", "en"],
        "categories": {
            "test_category": {
                "weight": 1.0,
                "templates": {
                    "pl": ["Polski test {var1}"],
                    "en": ["English test {var1}"],
                },
                "faker_vars": {"var1": ["value1", "value2"]},
            }
        },
    }


@pytest.fixture
def create_yaml_file(temp_dir: Path) -> Any:
    """Factory fixture to create YAML files."""

    def _create_yaml(filename: str, content: dict[str, Any]) -> Path:
        path = temp_dir / filename
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(content, f)
        return path

    return _create_yaml


@pytest.fixture
def domains_dir_with_files(
    temp_dir: Path, sample_yaml_content: dict[str, Any]
) -> Path:
    """Create domains directory with sample YAML files."""
    domains_dir = temp_dir / "domains"
    domains_dir.mkdir()

    # Create sample banking domain
    banking_content = {
        "domain": "banking",
        "languages": ["pl", "en"],
        "categories": {
            "system_error": {
                "weight": 1.0,
                "templates": {
                    "pl": ["Test {var1}"],
                    "en": ["Test {var1}"],
                },
                "faker_vars": {"var1": ["value1"]},
            }
        },
    }

    with (domains_dir / "banking.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(banking_content, f)

    return domains_dir
