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
    help="Convert 13+ document formats to Markdown powered by Microsoft MarkItDown (v2.0)",
    add_completion=True,
)
console = Console()

# Version display
def version_callback(value: bool):
    if value:
        console.print(f"pdf2md version {__version__}")
        console.print("Powered by Microsoft MarkItDown")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """Multi-format document to Markdown converter (v2.0)."""
    pass


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
    # XLSX-specific options
    xlsx_mode: str = typer.Option(
        "combined",
        "--xlsx-mode",
        help="Multi-sheet handling: combined, separate, or selected",
    ),
    xlsx_sheets: Optional[str] = typer.Option(
        None,
        "--xlsx-sheets",
        help="Comma-separated list of sheet names to convert (for 'selected' mode)",
    ),
    xlsx_extract_charts: bool = typer.Option(
        True,
        "--xlsx-extract-charts/--xlsx-no-extract-charts",
        help="Extract charts as images from XLSX",
    ),
    # MarkItDown v2.0 options
    use_markitdown: bool = typer.Option(
        True,
        "--markitdown/--legacy",
        help="Use MarkItDown converter (default) or legacy converters",
    ),
    rich_conversion: bool = typer.Option(
        False,
        "--rich-metadata/--simple",
        help="Extract detailed metadata using format-specific libraries (slower)",
    ),
    llm_descriptions: bool = typer.Option(
        False,
        "--llm-descriptions",
        help="Enable LLM-powered image descriptions (requires OPENAI_API_KEY)",
    ),
    llm_model: str = typer.Option(
        "gpt-4o",
        "--llm-model",
        help="OpenAI model for image descriptions (gpt-4o, gpt-4-turbo, etc.)",
    ),
    azure_docintel: bool = typer.Option(
        False,
        "--azure",
        help="Use Azure Document Intelligence for high-accuracy PDFs (requires Azure credentials)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
) -> None:
    """
    Convert documents to Markdown format.

    Supports 13+ formats:
    - Documents: PDF, DOCX, XLSX, PPTX
    - Web: HTML
    - Images: JPG, PNG, GIF, BMP, TIFF, WebP (with OCR)
    - Audio: WAV, MP3, M4A (with transcription)
    - E-books: EPub
    - Data: JSON, XML, CSV
    - Archives: ZIP
    - Email: MSG (Outlook)

    v2.0 Features:
    - LLM-powered image descriptions (--llm-descriptions)
    - Azure Document Intelligence for PDFs (--azure)
    - Rich metadata extraction (--rich-metadata)

    Examples:
        # PDF conversion
        pdf2md convert document.pdf -o output.md --images embed
        pdf2md convert scanned.pdf --llm-descriptions
        pdf2md convert complex.pdf --azure --rich-metadata

        # HTML conversion
        pdf2md convert page.html --html-base-url https://example.com

        # Office documents
        pdf2md convert report.docx --docx-include-comments
        pdf2md convert presentation.pptx -o slides.md
        pdf2md convert spreadsheet.xlsx --xlsx-mode combined

        # Images with OCR
        pdf2md convert scan.jpg -o text.md

        # Audio transcription
        pdf2md convert podcast.mp3 -o transcript.md

        # YouTube transcripts
        pdf2md convert https://youtube.com/watch?v=... -o transcript.md
    """
    try:
        # Determine output path
        if output_file is None:
            output_file = input_file.with_suffix('.md')

        # Parse XLSX sheets if provided
        xlsx_sheets_list = None
        if xlsx_sheets:
            xlsx_sheets_list = [s.strip() for s in xlsx_sheets.split(',')]

        # Create configuration
        config = Config(
            # MarkItDown v2.0 options
            use_markitdown=use_markitdown,
            rich_conversion=rich_conversion,
            llm_enabled=llm_descriptions,
            llm_model=llm_model,
            azure_enabled=azure_docintel,
            # Core conversion options
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
            # XLSX-specific options
            xlsx_mode=xlsx_mode,
            xlsx_sheets=xlsx_sheets_list,
            xlsx_extract_charts=xlsx_extract_charts,
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
    console.print(f"[bold]pdf2md version {__version__}[/bold]\n")

    # Check MarkItDown availability (v2.0 core)
    console.print("[bold]Core Converter (v2.0):[/bold]")
    try:
        import markitdown
        console.print(f"  [green]✓ MarkItDown[/green] - Primary converter for 13+ formats")
        console.print(f"    Version: {markitdown.__version__ if hasattr(markitdown, '__version__') else 'installed'}")
    except ImportError:
        console.print(f"  [red]✗ MarkItDown[/red] - Not installed (pip install markitdown[all])")

    # Check MarkItDown optional features
    console.print("\n[bold]MarkItDown Optional Features:[/bold]")

    # LLM integration
    try:
        import openai
        console.print(f"  [green]✓ openai[/green] - LLM-powered image descriptions")
    except ImportError:
        console.print(f"  [yellow]○ openai[/yellow] - LLM image descriptions (pip install openai)")

    # Azure Document Intelligence
    try:
        from azure.ai import formrecognizer
        console.print(f"  [green]✓ azure-ai-formrecognizer[/green] - High-accuracy PDF conversion")
    except ImportError:
        console.print(f"  [yellow]○ azure-ai-formrecognizer[/yellow] - Azure Document Intelligence (pip install azure-ai-formrecognizer)")

    # Audio transcription
    try:
        import speech_recognition
        console.print(f"  [green]✓ SpeechRecognition[/green] - Audio transcription")
    except ImportError:
        console.print(f"  [yellow]○ SpeechRecognition[/yellow] - Audio transcription (pip install SpeechRecognition)")

    # YouTube transcription
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        console.print(f"  [green]✓ youtube-transcript-api[/green] - YouTube transcript extraction")
    except ImportError:
        console.print(f"  [yellow]○ youtube-transcript-api[/yellow] - YouTube transcripts (pip install youtube-transcript-api)")

    # Create orchestrator to check converters
    orchestrator = ConversionOrchestrator()
    available = orchestrator.list_available_converters()

    # Create status table
    console.print("\n")
    table = Table(title="Available Converters")
    table.add_column("File Type", style="cyan")
    table.add_column("Strategy", style="yellow")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    for file_type, strategies in available.items():
        for strategy, is_available in strategies.items():
            status = "[green]✓ Available[/green]" if is_available else "[red]✗ Not Available[/red]"
            details = orchestrator.get_converter_info(file_type, strategy) if is_available else "Missing dependencies"
            table.add_row(file_type.upper(), strategy, status, details)

    console.print(table)

    # Check legacy dependencies
    console.print("\n[bold]Legacy Converters (deprecated):[/bold]")

    legacy_deps = {
        "pytesseract": "OCR support for scanned PDFs",
        "markdownify": "HTML to Markdown conversion",
        "beautifulsoup4": "HTML parsing",
        "pypandoc": "DOCX conversion (primary)",
        "mammoth": "DOCX conversion (fallback)",
        "python-docx": "DOCX metadata extraction",
        "pandas": "XLSX conversion",
        "openpyxl": "XLSX advanced features",
    }

    for dep, description in legacy_deps.items():
        try:
            __import__(dep.replace("-", "_"))
            console.print(f"  [green]✓[/green] {dep}: {description}")
        except ImportError:
            console.print(f"  [dim]○ {dep}: {description} (not needed with MarkItDown)[/dim]")

    # Check web interfaces
    console.print("\n[bold]Web Interfaces:[/bold]")
    web_deps = {
        "streamlit": "Web UI interface",
        "fastapi": "REST API server",
        "uvicorn": "ASGI server for FastAPI",
    }

    for dep, description in web_deps.items():
        try:
            __import__(dep.replace("-", "_"))
            console.print(f"  [green]✓[/green] {dep}: {description}")
        except ImportError:
            console.print(f"  [yellow]○[/yellow] {dep}: {description} (pip install -r requirements-web.txt)")


if __name__ == "__main__":
    app()
