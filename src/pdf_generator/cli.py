"""Command-line interface for PDF Generator using Typer.

This module provides CLI commands:
- generate: Generate N synthetic PDF documents
- validate: Validate domain YAML configuration
- list-domains: List available domains

Time Complexity: Varies per command
Space Complexity: Varies per command
"""

import logging
import uuid
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pdf_generator.domain_manager import DomainManager
from pdf_generator.exceptions import (
    DomainNotFoundError,
    InvalidDomainConfigError,
    InvalidLanguageMixError,
)
from pdf_generator.models import GenerationConfig
from pdf_generator.pdf_renderer import PDFRenderer, create_document_metadata
from pdf_generator.template_engine import LanguageSelector, TemplateEngine
from pdf_generator.utils import ensure_directory, format_file_size, parse_language_mix

# Initialize Typer app
app = typer.Typer(
    name="pdf-generator",
    help="Generate synthetic PDF documents for knowledge base training",
    add_completion=False,
)

# Rich console for pretty output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.command()
def generate(
    domain: str = typer.Option(
        ...,
        "--domain",
        "-d",
        help="Domain to use (e.g., banking, medical)",
    ),
    count: int = typer.Option(
        100,
        "--count",
        "-c",
        help="Number of PDFs to generate (1-10000)",
        min=1,
        max=10000,
    ),
    lang_mix: str = typer.Option(
        "pl:70,en:30",
        "--lang-mix",
        "-l",
        help="Language distribution (e.g., 'pl:70,en:30')",
    ),
    output: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory for PDFs",
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        "-s",
        help="Random seed for reproducibility",
    ),
) -> None:
    """Generate synthetic PDF documents.

    Example:
        python -m pdf_generator generate --domain banking --count 100 --lang-mix pl:70,en:30

    Time Complexity: O(n * m) where n is count, m is avg content length
    Space Complexity: O(m) for single document buffer
    """
    try:
        console.print("\n[bold cyan]PDF Generator[/bold cyan]")
        console.print(f"Domain: [green]{domain}[/green]")
        console.print(f"Count: [green]{count}[/green]")
        console.print(f"Language Mix: [green]{lang_mix}[/green]")
        console.print(f"Output: [green]{output}[/green]")
        if seed is not None:
            console.print(f"Seed: [green]{seed}[/green]")
        console.print()

        # Parse language mix
        try:
            language_mix = parse_language_mix(lang_mix)
        except InvalidLanguageMixError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

        # Validate generation config (not used, just for validation)
        _ = GenerationConfig(
            domain=domain,
            count=count,
            language_mix=language_mix,
            output_dir=output,
            seed=seed,
        )

        # Initialize components
        domain_manager = DomainManager()

        # Load domain config
        try:
            domain_config = domain_manager.load_domain(domain)
        except DomainNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
        except InvalidDomainConfigError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

        # Ensure output directory exists
        output_dir = ensure_directory(output)

        # Initialize engines
        template_engine = TemplateEngine(domain_config, seed=seed)
        language_selector = LanguageSelector(language_mix.distribution, seed=seed)
        pdf_renderer = PDFRenderer()

        # Generate PDFs with progress bar
        console.print("[bold]Generating PDFs...[/bold]\n")

        success_count = 0
        error_count = 0
        total_size = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Generating {count} documents...", total=count
            )

            for i in range(count):
                try:
                    # Select random language
                    language = language_selector.select_random_language()

                    # Render random document
                    category_name, content, _template = (
                        template_engine.render_random_document(language)
                    )

                    # Generate unique document ID
                    doc_id = str(uuid.uuid4())

                    # Create output path
                    filename = f"{domain}_{category_name}_{language.value}_{doc_id[:8]}.pdf"
                    pdf_path = output_dir / filename

                    # Create document metadata
                    document = create_document_metadata(
                        doc_id=doc_id,
                        domain=domain,
                        category=category_name,
                        language=language.value,
                        content=content,
                        output_path=pdf_path,
                    )

                    # Render PDF
                    pdf_renderer.render_document(document)

                    # Update statistics
                    success_count += 1
                    total_size += pdf_path.stat().st_size

                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to generate document {i+1}: {e}")

                # Update progress
                progress.update(task, advance=1)

        # Print summary
        console.print()
        console.print("[bold green]Generation Complete![/bold green]\n")
        console.print(f"✓ Successfully generated: [green]{success_count}[/green] PDFs")
        if error_count > 0:
            console.print(f"✗ Errors: [red]{error_count}[/red]")
        console.print(f"📁 Output directory: [cyan]{output_dir}[/cyan]")
        console.print(f"📊 Total size: [cyan]{format_file_size(total_size)}[/cyan]")
        console.print()

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        logger.exception("Unexpected error during generation")
        raise typer.Exit(code=1)


@app.command()
def validate(
    domain: str = typer.Argument(
        ...,
        help="Domain name to validate (e.g., banking)",
    )
) -> None:
    """Validate domain YAML configuration.

    Example:
        python -m pdf_generator validate banking

    Time Complexity: O(n) where n is YAML file size
    Space Complexity: O(n)
    """
    try:
        console.print(f"\n[bold cyan]Validating domain:[/bold cyan] {domain}\n")

        domain_manager = DomainManager()
        is_valid, message = domain_manager.validate_domain(domain)

        if is_valid:
            console.print(f"[green]✓ {message}[/green]\n")
        else:
            console.print(f"[red]✗ {message}[/red]\n")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"\n[red]Validation error:[/red] {e}\n")
        raise typer.Exit(code=1)


@app.command("list-domains")
def list_domains() -> None:
    """List all available domains.

    Example:
        python -m pdf_generator list-domains

    Time Complexity: O(n log n) where n is number of domain files
    Space Complexity: O(n)
    """
    try:
        console.print("\n[bold cyan]Available Domains[/bold cyan]\n")

        domain_manager = DomainManager()
        domains = domain_manager.list_available_domains()

        if not domains:
            console.print("[yellow]No domains found.[/yellow]")
            console.print(
                f"Domain directory: [cyan]{domain_manager.domains_dir}[/cyan]\n"
            )
            return

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Domain", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details")

        for domain_name in domains:
            try:
                # Try to load domain to check validity
                config = domain_manager.load_domain(domain_name)

                languages = ", ".join(lang.value for lang in config.languages)
                categories = len(config.categories)
                details = f"{categories} categories, languages: {languages}"

                table.add_row(domain_name, "✓ Valid", details)

            except Exception as e:
                table.add_row(domain_name, "✗ Invalid", str(e))

        console.print(table)
        console.print(
            f"\nDomain directory: [cyan]{domain_manager.domains_dir}[/cyan]\n"
        )

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        raise typer.Exit(code=1)


@app.callback()
def main() -> None:
    """PDF Generator - Create synthetic support ticket PDFs.

    A production-grade tool for generating domain-specific synthetic documents
    for knowledge base training and testing.
    """


if __name__ == "__main__":
    app()
