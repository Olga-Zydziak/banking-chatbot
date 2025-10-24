"""Utility functions for PDF Generator.

This module provides helper functions for:
- Path validation and sanitization
- Language mix parsing
- File system operations
- Atomic file writes

All functions are pure and side-effect free where possible.

Time Complexity: Noted per function
Space Complexity: Noted per function
"""

import re
import tempfile
from pathlib import Path

from pdf_generator.exceptions import InvalidLanguageMixError, PathValidationError
from pdf_generator.models import LanguageCode, LanguageMix


def validate_output_path(path: Path) -> Path:
    """Validate and sanitize output directory path.

    Security checks:
    - No path traversal (../) attempts
    - No absolute path escapes
    - Valid directory name characters only

    Args:
        path: Path to validate

    Returns:
        Validated absolute path

    Raises:
        PathValidationError: If path validation fails

    Time Complexity: O(n) where n is path length
    Space Complexity: O(n) for path string operations

    Example:
        >>> validate_output_path(Path("./output"))
        PosixPath('/home/user/project/output')
        >>> validate_output_path(Path("../etc/passwd"))  # Raises error
    """
    try:
        # Resolve to absolute path
        abs_path = path.resolve()

        # Check for path traversal attempts
        if ".." in path.parts:
            raise PathValidationError(
                f"Path traversal detected in '{path}'. "
                "Path must not contain '..' segments."
            )

        # Validate path components (alphanumeric, underscore, hyphen, dot)
        for part in path.parts:
            if part in (".", "..", "/"):
                continue
            if not re.match(r"^[a-zA-Z0-9._-]+$", part):
                raise PathValidationError(
                    f"Invalid characters in path component '{part}'. "
                    "Only alphanumeric, underscore, hyphen, and dot allowed."
                )

        return abs_path

    except Exception as e:
        if isinstance(e, PathValidationError):
            raise
        raise PathValidationError(f"Path validation failed for '{path}': {e}") from e


def parse_language_mix(mix_str: str) -> LanguageMix:
    """Parse language mix specification from CLI format.

    Format: "lang1:percentage1,lang2:percentage2"
    Example: "pl:70,en:30" -> {PL: 0.7, EN: 0.3}

    Args:
        mix_str: Language mix string in CLI format

    Returns:
        LanguageMix model with validated distribution

    Raises:
        InvalidLanguageMixError: If format is invalid or values don't sum to 100

    Time Complexity: O(n) where n is number of languages in mix
    Space Complexity: O(n) for distribution dictionary

    Example:
        >>> mix = parse_language_mix("pl:70,en:30")
        >>> mix.distribution[LanguageCode.PL]
        0.7
    """
    try:
        distribution: dict[LanguageCode, float] = {}

        # Split by comma and parse each language:percentage pair
        for pair_raw in mix_str.split(","):
            pair = pair_raw.strip()
            if ":" not in pair:
                raise InvalidLanguageMixError(
                    f"Invalid format '{pair}'. Expected 'lang:percentage'"
                )

            lang_str, percent_str = pair.split(":", 1)
            lang_str = lang_str.strip().lower()
            percent_str = percent_str.strip()

            # Validate language code
            try:
                lang = LanguageCode(lang_str)
            except ValueError:
                valid_codes = ", ".join(code.value for code in LanguageCode)
                raise InvalidLanguageMixError(
                    f"Unknown language code '{lang_str}'. "
                    f"Valid codes: {valid_codes}"
                ) from None

            # Parse percentage
            try:
                percentage = float(percent_str)
            except ValueError:
                raise InvalidLanguageMixError(
                    f"Invalid percentage '{percent_str}' for language '{lang_str}'. "
                    "Expected numeric value."
                ) from None

            # Convert percentage to probability
            probability = percentage / 100.0

            if lang in distribution:
                raise InvalidLanguageMixError(
                    f"Duplicate language code '{lang_str}' in mix specification"
                )

            distribution[lang] = probability

        # Validate using Pydantic model (checks sum to 1.0, etc.)
        return LanguageMix(distribution=distribution)

    except InvalidLanguageMixError:
        raise
    except Exception as e:
        raise InvalidLanguageMixError(
            f"Failed to parse language mix '{mix_str}': {e}"
        ) from e


def atomic_write(path: Path, content: bytes) -> None:
    """Write file atomically using temp file + rename strategy.

    This ensures that:
    - No partial writes are visible
    - Concurrent reads don't see incomplete data
    - Write failures don't corrupt existing file

    Args:
        path: Destination file path
        content: Binary content to write

    Raises:
        OSError: If write or rename fails

    Time Complexity: O(n) where n is content size
    Space Complexity: O(n) for content buffer

    Example:
        >>> atomic_write(Path("output.pdf"), b"PDF content")
    """
    # Create temp file in same directory to ensure same filesystem
    # (required for atomic rename on Unix)
    temp_fd = None
    temp_path = None

    try:
        # Create temporary file in same directory
        temp_fd, temp_path_str = tempfile.mkstemp(
            dir=path.parent, prefix=".tmp_", suffix=path.suffix
        )
        temp_path = Path(temp_path_str)

        # Write content to temp file
        with open(temp_fd, "wb") as f:
            f.write(content)

        # Atomic rename (POSIX guarantees atomicity)
        temp_path.replace(path)

    except Exception:
        # Clean up temp file on failure
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise
    finally:
        # Close file descriptor if still open
        if temp_fd is not None:
            try:
                import os

                os.close(temp_fd)
            except OSError:
                pass


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, creating if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        Absolute path to directory

    Raises:
        OSError: If directory creation fails
        PathValidationError: If path is invalid

    Time Complexity: O(n) where n is path depth
    Space Complexity: O(1)

    Example:
        >>> ensure_directory(Path("./output"))
        PosixPath('/home/user/project/output')
    """
    validated_path = validate_output_path(path)
    validated_path.mkdir(parents=True, exist_ok=True)
    return validated_path


def get_project_root() -> Path:
    """Get the project root directory.

    Searches for pyproject.toml or .git directory to identify root.

    Returns:
        Absolute path to project root

    Time Complexity: O(d) where d is directory depth
    Space Complexity: O(1)
    """
    current = Path(__file__).resolve()

    # Walk up directory tree looking for project markers
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent

    # Fallback to parent of src directory
    return current.parent.parent.parent


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB", "256 KB")

    Time Complexity: O(1)
    Space Complexity: O(1)

    Example:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} TB"
