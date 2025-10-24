"""Tests for domain manager."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from pdf_generator.domain_manager import DomainManager
from pdf_generator.exceptions import DomainNotFoundError, InvalidDomainConfigError


class TestDomainManager:
    """Tests for DomainManager class."""

    def test_load_valid_domain(self, domains_dir_with_files: Path) -> None:
        """Test loading valid domain configuration."""
        manager = DomainManager(domains_dir=domains_dir_with_files)
        config = manager.load_domain("banking")

        assert config.domain == "banking"
        assert len(config.languages) == 2
        assert "system_error" in config.categories

    def test_load_nonexistent_domain_raises_error(
        self, domains_dir_with_files: Path
    ) -> None:
        """Test that loading nonexistent domain raises DomainNotFoundError."""
        manager = DomainManager(domains_dir=domains_dir_with_files)

        with pytest.raises(DomainNotFoundError, match="not found"):
            manager.load_domain("nonexistent")

    def test_domain_caching(self, domains_dir_with_files: Path) -> None:
        """Test that domains are cached after first load."""
        manager = DomainManager(domains_dir=domains_dir_with_files)

        # Load domain twice
        config1 = manager.load_domain("banking")
        config2 = manager.load_domain("banking")

        # Should return same instance (cached)
        assert config1 is config2

    def test_list_available_domains(self, domains_dir_with_files: Path) -> None:
        """Test listing available domains."""
        manager = DomainManager(domains_dir=domains_dir_with_files)
        domains = manager.list_available_domains()

        assert "banking" in domains
        assert isinstance(domains, list)

    def test_invalid_yaml_syntax(
        self, temp_dir: Path, create_yaml_file: Any
    ) -> None:
        """Test that invalid YAML syntax raises error."""
        domains_dir = temp_dir / "domains"
        domains_dir.mkdir()

        # Create file with invalid YAML
        invalid_yaml = domains_dir / "invalid.yaml"
        invalid_yaml.write_text("domain: test\n  invalid: indentation")

        manager = DomainManager(domains_dir=domains_dir)

        with pytest.raises(InvalidDomainConfigError, match="YAML syntax error"):
            manager.load_domain("invalid")

    def test_weights_not_summing_to_one(self, temp_dir: Path) -> None:
        """Test that weights not summing to 1.0 raises error."""
        domains_dir = temp_dir / "domains"
        domains_dir.mkdir()

        invalid_content = {
            "domain": "test",
            "languages": ["pl"],
            "categories": {
                "cat1": {
                    "weight": 0.3,
                    "templates": {"pl": ["test"]},
                    "faker_vars": {},
                },
                "cat2": {
                    "weight": 0.5,
                    "templates": {"pl": ["test"]},
                    "faker_vars": {},
                },
            },
        }

        with (domains_dir / "test.yaml").open("w") as f:
            yaml.dump(invalid_content, f)

        manager = DomainManager(domains_dir=domains_dir)

        with pytest.raises(InvalidDomainConfigError, match="must sum to 1.0"):
            manager.load_domain("test")

    def test_validate_domain_success(self, domains_dir_with_files: Path) -> None:
        """Test successful domain validation."""
        manager = DomainManager(domains_dir=domains_dir_with_files)
        is_valid, message = manager.validate_domain("banking")

        assert is_valid is True
        assert "valid" in message.lower()

    def test_validate_domain_failure(self, domains_dir_with_files: Path) -> None:
        """Test failed domain validation."""
        manager = DomainManager(domains_dir=domains_dir_with_files)
        is_valid, message = manager.validate_domain("nonexistent")

        assert is_valid is False
        assert "not found" in message.lower()

    def test_empty_yaml_file(self, temp_dir: Path) -> None:
        """Test that empty YAML file raises error."""
        domains_dir = temp_dir / "domains"
        domains_dir.mkdir()

        empty_file = domains_dir / "empty.yaml"
        empty_file.write_text("")

        manager = DomainManager(domains_dir=domains_dir)

        with pytest.raises(InvalidDomainConfigError, match="empty or invalid"):
            manager.load_domain("empty")
