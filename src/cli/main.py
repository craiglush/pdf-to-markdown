"""Main CLI application using Typer."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pdf2markdown import __version__
from pdf2markdown.core.config import Config, ConversionStrategy, ImageMode, TableFormat
from pdf2markdown.core.orchestrator import ConversionOrchestrator

app = typer.Typer(
    name="pdf2md",
    help="Convert documents (PDF, HTML, DOCX, XLSX) to Markdown with high fidelity",
    add_completion=True,
)
console = Console()


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Input file to convert (PDF, HTML, DOCX, XLSX)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output Markdown file (default: same name as input with .md extension)",
    ),
    strategy: ConversionStrategy = typer.Option(
        ConversionStrategy.AUTO,
        "--strategy",
        "-s",
        help="Conversion strategy (mainly for PDFs)",
        case_sensitive=False,
    ),
    image_mode: ImageMode = typer.Option(
        ImageMode.EMBED,
        "--images",
        "-i",
        help="Image handling mode",
        case_sensitive=False,
    ),
    extract_images: bool = typer.Option(
        True,
        "--extract-images/--no-extract-images",
        help="Extract images from document",
    ),
    extract_tables: bool = typer.Option(
        True,
        "--extract-tables/--no-extract-tables",
        help="Extract and convert tables",
    ),
    table_format: TableFormat = typer.Option(
        TableFormat.GITHUB,
        "--table-format",
        "-t",
        help="Markdown table format",
        case_sensitive=False,
    ),
    ocr: bool = typer.Option(
        False,
        "--ocr",
        help="Force OCR for scanned PDFs",
    ),
    ocr_language: str = typer.Option(
        "eng",
        "--ocr-lang",
        help="Tesseract language code (e.g., 'eng', 'fra', 'eng+fra')",
    ),
    page_breaks: bool = typer.Option(
        False,
        "--page-breaks",
        help="Include page break markers (PDFs only)",
    ),
    # HTML-specific options
    html_download_images: bool = typer.Option(
        True,
        "--html-download-images/--html-no-download-images",
        help="Download external images from HTML (otherwise keep as links)",
    ),
    html_base_url: Optional[str] = typer.Option(
        None,
        "--html-base-url",
        help="Base URL for resolving relative links in HTML",
    ),
    # DOCX-specific options
    docx_include_comments: bool = typer.Option(
        False,
        "--docx-include-comments/--docx-no-include-comments",
        help="Include comments and tracked changes in DOCX conversion",
    ),
    docx_include_headers_footers: bool = typer.Option(
        False,
        "--docx-include-headers-footers/--docx-no-include-headers-footers",
        help="Include headers and footers from DOCX",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
) -> None:
    """
    Convert a document file to Markdown format.

    Supports: PDF, HTML, DOCX, XLSX

    Examples:
        pdf2md convert document.pdf -o output.md --images embed
        pdf2md convert page.html -o output.md --html-base-url https://example.com
        pdf2md convert report.docx -o output.md
        pdf2md convert document.docx --docx-include-comments
    """
    try:
        # Determine output path
        if output_file is None:
            output_file = input_file.with_suffix('.md')

        # Create configuration
        config = Config(
            strategy=strategy,
            image_mode=image_mode,
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=table_format,
            ocr_enabled=ocr,
            ocr_language=ocr_language,
            include_page_breaks=page_breaks,
            # HTML-specific options
            html_download_images=html_download_images,
            html_base_url=html_base_url,
            # DOCX-specific options
            docx_include_comments=docx_include_comments,
            docx_include_headers_footers=docx_include_headers_footers,
        )

        # Create orchestrator and convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(input_file)

        # Save result
        result.save(output_file, save_images=(image_mode != ImageMode.EMBED))

        # Success message
        console.print(f"\n[green]✓ Saved to:[/green] {output_file}")

        if result.images and image_mode != ImageMode.EMBED:
            console.print(f"[green]✓ Images saved to:[/green] {result.image_dir}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ...,
        help="Input directory containing documents to convert",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for Markdown files (default: same as input)",
    ),
    pattern: str = typer.Option(
        "*.pdf",
        "--pattern",
        "-p",
        help="File pattern to match (e.g., '*.pdf', '*.html', '*.{pdf,html}')",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Search for files recursively in subdirectories",
    ),
    parallel: int = typer.Option(
        1,
        "--parallel",
        help="Number of parallel conversion workers (1 = sequential)",
        min=1,
        max=16,
    ),
    strategy: ConversionStrategy = typer.Option(
        ConversionStrategy.AUTO,
        "--strategy",
        "-s",
        help="Conversion strategy (mainly for PDFs)",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop on first error",
    ),
) -> None:
    """
    Batch convert multiple document files in a directory.

    Supports: PDF, HTML, DOCX, XLSX

    Examples:
        pdf2md batch ./pdfs/ --output ./markdown/ --parallel 4
        pdf2md batch ./docs/ --pattern "*.html" --recursive
    """
    try:
        # Determine output directory
        if output_dir is None:
            output_dir = input_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find files
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))

        if not files:
            console.print(f"[yellow]No files found matching '{pattern}' in {input_dir}[/yellow]")
            return

        console.print(f"[cyan]Found {len(files)} file(s) to convert[/cyan]\n")

        # Create configuration
        config = Config(strategy=strategy)
        orchestrator = ConversionOrchestrator(config)

        # Process files
        success_count = 0
        error_count = 0

        for file in files:
            try:
                console.print(f"[cyan]Converting:[/cyan] {file.name}")

                # Calculate relative path for subdirectories
                if recursive:
                    rel_path = file.relative_to(input_dir)
                    out_path = output_dir / rel_path.with_suffix('.md')
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    out_path = output_dir / file.with_suffix('.md').name

                # Convert
                result = orchestrator.convert(file)
                result.save(out_path)

                console.print(f"[green]✓ Saved:[/green] {out_path}\n")
                success_count += 1

            except Exception as e:
                console.print(f"[red]✗ Error:[/red] {e}\n")
                error_count += 1

                if fail_fast:
                    raise typer.Exit(1)

        # Summary
        console.print(f"\n[bold]Conversion Summary:[/bold]")
        console.print(f"  ✓ Successful: {success_count}")
        console.print(f"  ✗ Failed: {error_count}")

        if error_count > 0:
            raise typer.Exit(1)

    except Exception as e:
        if not fail_fast:
            console.print(f"[red]✗ Batch conversion failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    pdf_file: Path = typer.Argument(
        ...,
        help="PDF file to analyze",
        exists=True,
        file_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Display information about a PDF file without converting it.

    Example:
        pdf2md info document.pdf
    """
    try:
        import pymupdf as fitz

        doc = fitz.open(pdf_file)

        # Create info table
        table = Table(title=f"PDF Information: {pdf_file.name}")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Basic info
        table.add_row("File Size", f"{pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
        table.add_row("Pages", str(len(doc)))

        # Metadata
        meta = doc.metadata
        if meta.get("title"):
            table.add_row("Title", meta["title"])
        if meta.get("author"):
            table.add_row("Author", meta["author"])
        if meta.get("subject"):
            table.add_row("Subject", meta["subject"])
        if meta.get("creator"):
            table.add_row("Creator", meta["creator"])

        # Count images and tables
        total_images = 0
        total_tables = 0
        has_text = False

        for page in doc:
            total_images += len(page.get_images())
            tables = page.find_tables()
            total_tables += len(tables.tables) if tables else 0
            if page.get_text().strip():
                has_text = True

        table.add_row("Images", str(total_images))
        table.add_row("Tables", str(total_tables))
        table.add_row("Has Text Layer", "Yes" if has_text else "No (Scanned)")

        doc.close()

        console.print(table)

        # Recommendation
        if not has_text:
            console.print("\n[yellow]⚠ This PDF appears to be scanned. Use --ocr flag for conversion.[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host address to bind",
    ),
    port: int = typer.Option(
        8501,
        "--port",
        "-p",
        help="Port number",
    ),
    interface: str = typer.Option(
        "streamlit",
        "--interface",
        "-i",
        help="Web interface to launch (streamlit or fastapi)",
    ),
) -> None:
    """
    Start the web interface for PDF conversion.

    Example:
        pdf2md serve --port 8501
    """
    try:
        if interface.lower() == "streamlit":
            console.print(f"[cyan]Starting Streamlit UI on http://{host}:{port}[/cyan]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

            import subprocess
            subprocess.run([
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(Path(__file__).parent.parent / "web" / "streamlit_app.py"),
                "--server.address",
                host,
                "--server.port",
                str(port),
            ])

        elif interface.lower() == "fastapi":
            console.print(f"[cyan]Starting FastAPI server on http://{host}:{port}[/cyan]")
            console.print("[yellow]API docs available at http://{host}:{port}/docs[/yellow]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

            import uvicorn
            from pdf2markdown.api.app import app as fastapi_app

            uvicorn.run(
                fastapi_app,
                host=host,
                port=port,
                log_level="info",
            )

        else:
            console.print(f"[red]Unknown interface: {interface}[/red]")
            console.print("Available interfaces: streamlit, fastapi")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error starting server:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Display version information."""
    console.print(f"pdf2md version {__version__}")


@app.command()
def check() -> None:
    """
    Check availability of dependencies and converters.
    """
    console.print("[bold]Checking dependencies...[/bold]\n")

    # Create orchestrator to check converters
    orchestrator = ConversionOrchestrator()
    available = orchestrator.list_available_converters()

    # Create status table
    table = Table(title="Converter Availability")
    table.add_column("Strategy", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    for strategy, is_available in available.items():
        status = "[green]✓ Available[/green]" if is_available else "[red]✗ Not Available[/red]"
        details = orchestrator.get_converter_info(strategy) if is_available else "Missing dependencies"
        table.add_row(strategy.value, status, details)

    console.print(table)

    # Check optional dependencies
    console.print("\n[bold]Optional Dependencies:[/bold]")

    optional_deps = {
        "pytesseract": "OCR support for scanned PDFs",
        "markdownify": "HTML to Markdown conversion",
        "beautifulsoup4": "HTML parsing and preprocessing",
        "pypandoc": "DOCX to Markdown conversion (primary)",
        "mammoth": "DOCX to Markdown conversion (fallback)",
        "python-docx": "DOCX metadata and image extraction",
        "pandas": "XLSX to Markdown conversion",
        "streamlit": "Web UI interface",
        "fastapi": "REST API server",
        "marker-pdf": "High-accuracy AI converter (PDFs)",
    }

    for dep, description in optional_deps.items():
        try:
            __import__(dep.replace("-", "_"))
            console.print(f"  [green]✓[/green] {dep}: {description}")
        except ImportError:
            console.print(f"  [yellow]○[/yellow] {dep}: {description} (not installed)")


if __name__ == "__main__":
    app()
