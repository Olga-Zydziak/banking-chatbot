"""Tests for utility functions."""

from pathlib import Path

import pytest

from pdf_generator.exceptions import InvalidLanguageMixError, PathValidationError
from pdf_generator.models import LanguageCode
from pdf_generator.utils import (
    atomic_write,
    ensure_directory,
    format_file_size,
    parse_language_mix,
    validate_output_path,
)


class TestParseLanguageMix:
    """Tests for parse_language_mix function."""

    @pytest.mark.parametrize(
        "mix_str,expected_pl,expected_en",
        [
            ("pl:100", 1.0, None),
            ("pl:70,en:30", 0.7, 0.3),
            ("pl:50,en:50", 0.5, 0.5),
            ("en:100", None, 1.0),
        ],
    )
    def test_valid_language_mix(
        self, mix_str: str, expected_pl: float | None, expected_en: float | None
    ) -> None:
        """Test parsing valid language mix specifications."""
        result = parse_language_mix(mix_str)

        if expected_pl is not None:
            assert result.distribution[LanguageCode.PL] == pytest.approx(expected_pl)
        if expected_en is not None:
            assert result.distribution[LanguageCode.EN] == pytest.approx(expected_en)

    def test_invalid_format_no_colon(self) -> None:
        """Test that format without colon raises error."""
        with pytest.raises(InvalidLanguageMixError, match="Expected 'lang:percentage'"):
            parse_language_mix("pl100")

    def test_invalid_language_code(self) -> None:
        """Test that unknown language code raises error."""
        with pytest.raises(InvalidLanguageMixError, match="Unknown language code"):
            parse_language_mix("fr:100")

    def test_invalid_percentage_format(self) -> None:
        """Test that non-numeric percentage raises error."""
        with pytest.raises(InvalidLanguageMixError, match="Invalid percentage"):
            parse_language_mix("pl:abc")

    def test_percentages_not_summing_to_100(self) -> None:
        """Test that percentages not summing to 100 raises error."""
        with pytest.raises(InvalidLanguageMixError):
            parse_language_mix("pl:60,en:30")

    def test_duplicate_language_code(self) -> None:
        """Test that duplicate language codes raise error."""
        with pytest.raises(InvalidLanguageMixError, match="Duplicate language code"):
            parse_language_mix("pl:50,pl:50")


class TestValidateOutputPath:
    """Tests for validate_output_path function."""

    def test_valid_relative_path(self, temp_dir: Path) -> None:
        """Test validating valid relative path."""
        test_path = temp_dir / "output"
        result = validate_output_path(test_path)
        assert result.is_absolute()

    def test_path_traversal_detected(self) -> None:
        """Test that path traversal attempts are detected."""
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validate_output_path(Path("../etc/passwd"))

    def test_invalid_characters_in_path(self) -> None:
        """Test that invalid characters are rejected."""
        with pytest.raises(PathValidationError, match="Invalid characters"):
            validate_output_path(Path("output/<script>"))


class TestAtomicWrite:
    """Tests for atomic_write function."""

    def test_atomic_write_creates_file(self, temp_dir: Path) -> None:
        """Test that atomic write creates file."""
        test_file = temp_dir / "test.pdf"
        content = b"PDF content here"

        atomic_write(test_file, content)

        assert test_file.exists()
        assert test_file.read_bytes() == content

    def test_atomic_write_overwrites_existing(self, temp_dir: Path) -> None:
        """Test that atomic write overwrites existing file."""
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"old content")

        new_content = b"new content"
        atomic_write(test_file, new_content)

        assert test_file.read_bytes() == new_content


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_new_directory(self, temp_dir: Path) -> None:
        """Test that ensure_directory creates new directory."""
        new_dir = temp_dir / "new" / "nested" / "dir"

        result = ensure_directory(new_dir)

        assert result.exists()
        assert result.is_dir()

    def test_existing_directory_no_error(self, temp_dir: Path) -> None:
        """Test that existing directory doesn't raise error."""
        result = ensure_directory(temp_dir)
        assert result.exists()


class TestFormatFileSize:
    """Tests for format_file_size function."""

    @pytest.mark.parametrize(
        "size_bytes,expected",
        [
            (100, "100.0 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1048576, "1.0 MB"),
            (1610612736, "1.5 GB"),
        ],
    )
    def test_format_file_size(self, size_bytes: int, expected: str) -> None:
        """Test file size formatting."""
        assert format_file_size(size_bytes) == expected
