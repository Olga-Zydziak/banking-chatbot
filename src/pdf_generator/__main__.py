"""Entry point for running PDF Generator as a module.

Usage:
    python -m pdf_generator generate --domain banking --count 100
    python -m pdf_generator validate banking
    python -m pdf_generator list-domains

Time Complexity: Delegated to CLI commands
Space Complexity: Delegated to CLI commands
"""

from pdf_generator.cli import app

if __name__ == "__main__":
    app()
