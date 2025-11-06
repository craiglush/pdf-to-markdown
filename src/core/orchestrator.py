"""Conversion orchestrator for intelligent converter selection and management."""

from pathlib import Path
from typing import Dict, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from pdf2markdown.converters.document_converter import DocumentConverter
from pdf2markdown.converters.ocr_converter import OCRConverter
from pdf2markdown.converters.pymupdf_converter import PyMuPDFConverter
from pdf2markdown.core.config import Config, ConversionStrategy
from pdf2markdown.core.file_detector import FileTypeDetector
from pdf2markdown.core.models import ConversionResult

# Import format-specific converters if available
try:
    from pdf2markdown.converters.html_converter import HTMLConverter
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

try:
    from pdf2markdown.converters.docx_converter import DOCXConverter
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pdf2markdown.converters.xlsx_converter import XLSXConverter
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

console = Console()


class ConversionOrchestrator:
    """
    Orchestrates document to Markdown conversion with intelligent converter selection.

    The orchestrator:
    - Detects file type (PDF, HTML, DOCX, XLSX)
    - Analyzes the document to determine the best conversion strategy
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
        self.file_detector = FileTypeDetector()

        # Converter registry: {(file_type, strategy): converter}
        self._converters: Dict[Tuple[str, str], DocumentConverter] = {}
        self._initialize_converters()

    def _initialize_converters(self) -> None:
        """Initialize all available converters."""
        # PDF converters
        pymupdf_converter = PyMuPDFConverter(self.config)
        if pymupdf_converter.is_available():
            self._converters[('pdf', ConversionStrategy.FAST.value)] = pymupdf_converter

        ocr_converter = OCRConverter(self.config)
        if ocr_converter.is_available():
            self._converters[('pdf', ConversionStrategy.OCR.value)] = ocr_converter

        # TODO: Add Marker converter when implementing accurate strategy
        # marker_converter = MarkerConverter(self.config)
        # if marker_converter.is_available():
        #     self._converters[('pdf', ConversionStrategy.ACCURATE.value)] = marker_converter

        # HTML converter
        if HTML_AVAILABLE:
            html_converter = HTMLConverter(self.config)
            if html_converter.is_available():
                self._converters[('html', 'default')] = html_converter

        # DOCX converter
        if DOCX_AVAILABLE:
            docx_converter = DOCXConverter(self.config)
            if docx_converter.is_available():
                self._converters[('docx', 'default')] = docx_converter

        # XLSX converter
        if XLSX_AVAILABLE:
            xlsx_converter = XLSXConverter(self.config)
            if xlsx_converter.is_available():
                self._converters[('xlsx', 'default')] = xlsx_converter

    def convert(
        self,
        file_path: Path | str,
        strategy: str | ConversionStrategy | None = None,
        **options
    ) -> ConversionResult:
        """
        Convert a document to Markdown.

        Supports multiple file formats: PDF, HTML, DOCX, XLSX (future).

        Args:
            file_path: Path to the document file
            strategy: Conversion strategy (auto, fast, accurate, ocr)
            **options: Additional configuration options

        Returns:
            ConversionResult with markdown and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported or no suitable converter available
        """
        # Normalize path
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Detect file type
        try:
            file_type = self.file_detector.detect(file_path)
        except ValueError as e:
            raise ValueError(f"Could not determine file type: {e}")

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
            strategy = self._detect_best_strategy(file_path, file_type)

        # Get converter for file type and strategy
        converter = self._get_converter_for_type(file_type, strategy)

        if not converter:
            available = self._get_available_strategies_for_type(file_type)
            raise ValueError(
                f"No converter available for {file_type.upper()} with strategy '{strategy.value}'. "
                f"Available strategies for {file_type.upper()}: {available}"
            )

        # Log conversion start
        console.print(f"[cyan]File Type:[/cyan] {file_type.upper()}")
        console.print(f"[cyan]Converting:[/cyan] {file_path.name}")
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
                f"Converting {file_path.name}...",
                total=None,
            )

            result = converter.convert(file_path)

            progress.update(task, completed=True)

        # Validate result
        if self.config.validate_output:
            self._validate_result(result)

        # Print summary
        console.print("\n[green]✓ Conversion completed successfully![/green]")
        console.print(result.get_summary())

        return result

    def _detect_best_strategy(self, file_path: Path, file_type: str) -> ConversionStrategy:
        """
        Automatically detect the best conversion strategy for a file.

        Args:
            file_path: Path to the file
            file_type: Detected file type ('pdf', 'html', 'docx', 'xlsx')

        Returns:
            Recommended ConversionStrategy
        """
        # PDF-specific strategy detection
        if file_type == 'pdf':
            return self._detect_pdf_strategy(file_path)

        # For other file types, check if we have a default converter
        if (file_type, 'default') in self._converters:
            return ConversionStrategy.FAST  # Use FAST as placeholder

        # Fall back to FAST strategy
        return ConversionStrategy.FAST

    def _detect_pdf_strategy(self, pdf_path: Path) -> ConversionStrategy:
        """
        Detect best strategy specifically for PDF files.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Recommended ConversionStrategy
        """
        # Check if PDF is scanned (no text layer)
        is_scanned = self._is_scanned_pdf(pdf_path)

        if is_scanned:
            console.print("[yellow]Detected scanned PDF (no text layer)[/yellow]")
            if ('pdf', ConversionStrategy.OCR.value) in self._converters:
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

    def _get_converter_for_type(
        self,
        file_type: str,
        strategy: ConversionStrategy
    ) -> Optional[DocumentConverter]:
        """
        Get converter for the given file type and strategy.

        Args:
            file_type: File type ('pdf', 'html', 'docx', 'xlsx')
            strategy: Conversion strategy

        Returns:
            DocumentConverter instance or None
        """
        # Try exact match first
        key = (file_type, strategy.value)
        if key in self._converters:
            return self._converters[key]

        # Try 'default' strategy for non-PDF formats
        if file_type != 'pdf':
            default_key = (file_type, 'default')
            if default_key in self._converters:
                return self._converters[default_key]

        return None

    def _get_available_strategies_for_type(self, file_type: str) -> list[str]:
        """
        Get list of available strategies for a file type.

        Args:
            file_type: File type

        Returns:
            List of available strategy names
        """
        strategies = []
        for (ft, strategy) in self._converters.keys():
            if ft == file_type:
                strategies.append(strategy)
        return strategies

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
            warnings.append("Very little text extracted - document may be scanned or contain mostly images")

        # Check for errors
        if result.metadata.errors:
            warnings.append(f"Conversion completed with {len(result.metadata.errors)} errors")

        # Add warnings to metadata
        if warnings:
            result.metadata.warnings.extend(warnings)

    def list_available_converters(self) -> Dict[str, Dict[str, bool]]:
        """
        List all converters and their availability by file type.

        Returns:
            Dictionary mapping file type to {strategy: availability}
        """
        result: Dict[str, Dict[str, bool]] = {}

        # PDF converters
        result['pdf'] = {
            ConversionStrategy.FAST.value: ('pdf', ConversionStrategy.FAST.value) in self._converters,
            ConversionStrategy.ACCURATE.value: ('pdf', ConversionStrategy.ACCURATE.value) in self._converters,
            ConversionStrategy.OCR.value: ('pdf', ConversionStrategy.OCR.value) in self._converters,
        }

        # Other file types (future)
        for file_type in ['html', 'docx', 'xlsx']:
            if any(ft == file_type for ft, _ in self._converters.keys()):
                result[file_type] = {
                    'default': (file_type, 'default') in self._converters
                }

        return result

    def get_converter_info(self, file_type: str, strategy: str = 'default') -> Optional[str]:
        """
        Get information about a specific converter.

        Args:
            file_type: File type ('pdf', 'html', 'docx', 'xlsx')
            strategy: Conversion strategy

        Returns:
            Converter information string or None
        """
        key = (file_type, strategy)
        converter = self._converters.get(key)
        if converter:
            return f"{converter.get_name()} - OCR: {converter.supports_ocr()}"
        return None

    def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported file types.

        Returns:
            List of supported file type strings
        """
        file_types = set()
        for file_type, _ in self._converters.keys():
            file_types.add(file_type)
        return sorted(file_types)
