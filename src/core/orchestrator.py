"""Conversion orchestrator for intelligent converter selection and management."""

from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from pdf2markdown.converters.base import PDFConverter
from pdf2markdown.converters.ocr_converter import OCRConverter
from pdf2markdown.converters.pymupdf_converter import PyMuPDFConverter
from pdf2markdown.core.config import Config, ConversionStrategy
from pdf2markdown.core.models import ConversionResult

console = Console()


class ConversionOrchestrator:
    """
    Orchestrates PDF to Markdown conversion with intelligent converter selection.

    The orchestrator:
    - Analyzes the PDF to determine the best conversion strategy
    - Selects the appropriate converter
    - Handles fallback scenarios
    - Validates output quality
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration for conversion
        """
        self.config = config or Config()
        self._converters: Dict[str, PDFConverter] = {}
        self._initialize_converters()

    def _initialize_converters(self) -> None:
        """Initialize all available converters."""
        # Fast converter (PyMuPDF)
        pymupdf_converter = PyMuPDFConverter(self.config)
        if pymupdf_converter.is_available():
            self._converters[ConversionStrategy.FAST] = pymupdf_converter

        # OCR converter
        ocr_converter = OCRConverter(self.config)
        if ocr_converter.is_available():
            self._converters[ConversionStrategy.OCR] = ocr_converter

        # TODO: Add Marker converter when implementing accurate strategy
        # marker_converter = MarkerConverter(self.config)
        # if marker_converter.is_available():
        #     self._converters[ConversionStrategy.ACCURATE] = marker_converter

    def convert(
        self,
        pdf_path: Path | str,
        strategy: str | ConversionStrategy | None = None,
        **options
    ) -> ConversionResult:
        """
        Convert a PDF to Markdown.

        Args:
            pdf_path: Path to the PDF file
            strategy: Conversion strategy (auto, fast, accurate, ocr)
            **options: Additional configuration options

        Returns:
            ConversionResult with markdown and metadata

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If no suitable converter is available
        """
        # Normalize path
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        # Update config with options
        if options:
            config_dict = self.config.model_dump()
            config_dict.update(options)
            self.config = Config(**config_dict)

        # Determine strategy
        if strategy:
            if isinstance(strategy, str):
                strategy = ConversionStrategy(strategy)
        else:
            strategy = self.config.strategy

        # Auto-detect strategy if needed
        if strategy == ConversionStrategy.AUTO:
            strategy = self._detect_best_strategy(pdf_path)

        # Get converter
        converter = self._get_converter(strategy)

        if not converter:
            available = list(self._converters.keys())
            raise ValueError(
                f"No converter available for strategy '{strategy}'. "
                f"Available strategies: {available}"
            )

        # Log conversion start
        console.print(f"[cyan]Converting:[/cyan] {pdf_path.name}")
        console.print(f"[cyan]Strategy:[/cyan] {strategy.value}")
        console.print(f"[cyan]Converter:[/cyan] {converter.get_name()}")

        # Perform conversion with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Converting {pdf_path.name}...",
                total=None,
            )

            result = converter.convert(pdf_path)

            progress.update(task, completed=True)

        # Validate result
        if self.config.validate_output:
            self._validate_result(result)

        # Print summary
        console.print("\n[green]✓ Conversion completed successfully![/green]")
        console.print(result.get_summary())

        return result

    def _detect_best_strategy(self, pdf_path: Path) -> ConversionStrategy:
        """
        Automatically detect the best conversion strategy.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Recommended ConversionStrategy
        """
        # Check if PDF is scanned (no text layer)
        is_scanned = self._is_scanned_pdf(pdf_path)

        if is_scanned:
            console.print("[yellow]Detected scanned PDF (no text layer)[/yellow]")
            if ConversionStrategy.OCR in self._converters:
                return ConversionStrategy.OCR
            else:
                console.print(
                    "[red]Warning: OCR not available. "
                    "Install pytesseract and tesseract-ocr to process scanned PDFs[/red]"
                )
                return ConversionStrategy.FAST

        # For normal PDFs with text, use fast converter
        return ConversionStrategy.FAST

    def _is_scanned_pdf(self, pdf_path: Path) -> bool:
        """
        Check if PDF is scanned (image-based).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if scanned, False if has text layer
        """
        try:
            import pymupdf as fitz

            doc = fitz.open(pdf_path)

            # Check first few pages
            pages_to_check = min(3, len(doc))
            total_text_length = 0

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                total_text_length += len(text)

            doc.close()

            # If very little text found, likely scanned
            avg_text_per_page = total_text_length / pages_to_check
            return avg_text_per_page < 50  # Threshold for scanned detection

        except Exception:
            # If we can't determine, assume not scanned
            return False

    def _get_converter(self, strategy: ConversionStrategy) -> Optional[PDFConverter]:
        """
        Get converter for the given strategy.

        Args:
            strategy: Conversion strategy

        Returns:
            PDFConverter instance or None
        """
        return self._converters.get(strategy)

    def _validate_result(self, result: ConversionResult) -> None:
        """
        Validate conversion result quality.

        Args:
            result: ConversionResult to validate
        """
        if not result.metadata:
            return

        warnings = []

        # Check if output is suspiciously short
        if result.metadata.total_words < 10 and result.metadata.page_count > 1:
            warnings.append("Very little text extracted - PDF may be scanned or contain mostly images")

        # Check for errors
        if result.metadata.errors:
            warnings.append(f"Conversion completed with {len(result.metadata.errors)} errors")

        # Add warnings to metadata
        if warnings:
            result.metadata.warnings.extend(warnings)

    def list_available_converters(self) -> Dict[str, bool]:
        """
        List all converters and their availability.

        Returns:
            Dictionary mapping strategy to availability
        """
        return {
            ConversionStrategy.FAST: ConversionStrategy.FAST in self._converters,
            ConversionStrategy.ACCURATE: ConversionStrategy.ACCURATE in self._converters,
            ConversionStrategy.OCR: ConversionStrategy.OCR in self._converters,
        }

    def get_converter_info(self, strategy: ConversionStrategy) -> Optional[str]:
        """
        Get information about a specific converter.

        Args:
            strategy: Conversion strategy

        Returns:
            Converter information string or None
        """
        converter = self._get_converter(strategy)
        if converter:
            return f"{converter.get_name()} - OCR: {converter.supports_ocr()}"
        return None
