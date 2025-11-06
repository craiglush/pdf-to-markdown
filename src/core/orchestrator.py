"""Conversion orchestrator for intelligent converter selection and management."""

from pathlib import Path
from typing import Dict, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from pdf2markdown.converters.document_converter import DocumentConverter
from pdf2markdown.core.cache import ConversionCache
from pdf2markdown.core.config import Config, ConversionStrategy
from pdf2markdown.core.file_detector import FileTypeDetector
from pdf2markdown.core.models import ConversionResult
from pdf2markdown.core.profiling import PerformanceTimer

# Import MarkItDown converter (v2.0 primary converter)
try:
    from pdf2markdown.converters.markitdown_converter import MarkItDownConverter
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

# Import legacy format-specific converters (optional fallback)
try:
    from pdf2markdown.converters.ocr_converter import OCRConverter
    from pdf2markdown.converters.pymupdf_converter import PyMuPDFConverter
    LEGACY_PDF_AVAILABLE = True
except ImportError:
    LEGACY_PDF_AVAILABLE = False

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
    Orchestrates multi-format document to Markdown conversion (v2.0).

    The orchestrator:
    - Detects file type (PDF, HTML, DOCX, XLSX, PPTX, audio, YouTube, EPub, etc.)
    - Analyzes the document to determine the best conversion strategy
    - Selects the appropriate converter (MarkItDown primary, legacy fallback)
    - Handles LLM and Azure Document Intelligence integration
    - Validates output quality

    v2.0 Changes:
    - Uses Microsoft MarkItDown as primary converter for all formats
    - Supports 13+ file formats (PDF, DOCX, XLSX, PPTX, HTML, audio, YouTube, EPub, etc.)
    - Optional LLM-powered image descriptions
    - Optional Azure Document Intelligence for high-accuracy PDFs
    - Legacy converters available as fallback when use_markitdown=False
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration for conversion
        """
        self.config = config or Config()
        self.file_detector = FileTypeDetector()

        # Initialize cache (v2.0 performance optimization)
        self.cache = ConversionCache(
            cache_dir=Path(self.config.cache_dir) if self.config.cache_dir else None,
            max_age_hours=self.config.cache_max_age_hours,
            enabled=self.config.enable_cache,
        )

        # Converter registry: {(file_type, strategy): converter}
        self._converters: Dict[Tuple[str, str], DocumentConverter] = {}
        self._markitdown_converter: Optional[DocumentConverter] = None
        self._initialize_converters()

    def _initialize_converters(self) -> None:
        """Initialize all available converters (MarkItDown primary, legacy fallback)."""

        # MarkItDown converter (v2.0 primary converter for ALL formats)
        if MARKITDOWN_AVAILABLE and self.config.use_markitdown:
            markitdown_converter = MarkItDownConverter(self.config)
            if markitdown_converter.is_available():
                self._markitdown_converter = markitdown_converter

                # Register MarkItDown for all supported formats
                for ext in markitdown_converter.get_supported_extensions():
                    # Map extension to file type
                    file_type = self._ext_to_filetype(ext)
                    if file_type:
                        # Register for all strategies
                        self._converters[(file_type, ConversionStrategy.MARKITDOWN.value)] = markitdown_converter
                        self._converters[(file_type, ConversionStrategy.FAST.value)] = markitdown_converter
                        self._converters[(file_type, ConversionStrategy.AUTO.value)] = markitdown_converter

                        # For PDFs with Azure, register as accurate
                        if file_type == 'pdf' and self.config.azure_enabled:
                            self._converters[(file_type, ConversionStrategy.ACCURATE.value)] = markitdown_converter

                console.print("[green]✓ MarkItDown converter initialized[/green]")
            else:
                console.print("[yellow]⚠ MarkItDown not available, using legacy converters[/yellow]")

        # Legacy converters (optional fallback when use_markitdown=False)
        if not self.config.use_markitdown or not self._markitdown_converter:
            self._initialize_legacy_converters()

    def _initialize_legacy_converters(self) -> None:
        """Initialize legacy format-specific converters (fallback)."""
        console.print("[cyan]Initializing legacy converters...[/cyan]")

        # Legacy PDF converters
        if LEGACY_PDF_AVAILABLE:
            pymupdf_converter = PyMuPDFConverter(self.config)
            if pymupdf_converter.is_available():
                self._converters[('pdf', ConversionStrategy.FAST.value)] = pymupdf_converter
                console.print("[green]✓ PyMuPDF converter available[/green]")

            ocr_converter = OCRConverter(self.config)
            if ocr_converter.is_available():
                self._converters[('pdf', ConversionStrategy.OCR.value)] = ocr_converter
                console.print("[green]✓ OCR converter available[/green]")

        # Legacy HTML converter
        if HTML_AVAILABLE:
            html_converter = HTMLConverter(self.config)
            if html_converter.is_available():
                self._converters[('html', 'default')] = html_converter
                self._converters[('html', ConversionStrategy.FAST.value)] = html_converter
                console.print("[green]✓ HTML converter available[/green]")

        # Legacy DOCX converter
        if DOCX_AVAILABLE:
            docx_converter = DOCXConverter(self.config)
            if docx_converter.is_available():
                self._converters[('docx', 'default')] = docx_converter
                self._converters[('docx', ConversionStrategy.FAST.value)] = docx_converter
                console.print("[green]✓ DOCX converter available[/green]")

        # Legacy XLSX converter
        if XLSX_AVAILABLE:
            xlsx_converter = XLSXConverter(self.config)
            if xlsx_converter.is_available():
                self._converters[('xlsx', 'default')] = xlsx_converter
                self._converters[('xlsx', ConversionStrategy.FAST.value)] = xlsx_converter
                console.print("[green]✓ XLSX converter available[/green]")

    def _ext_to_filetype(self, ext: str) -> Optional[str]:
        """
        Map file extension to file type.

        Args:
            ext: File extension (e.g., '.pdf', '.docx')

        Returns:
            File type string or None
        """
        mapping = {
            '.pdf': 'pdf',
            '.html': 'html',
            '.htm': 'html',
            '.docx': 'docx',
            '.doc': 'docx',
            '.xlsx': 'xlsx',
            '.xls': 'xlsx',
            '.pptx': 'pptx',
            '.ppt': 'pptx',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.tiff': 'image',
            '.wav': 'audio',
            '.mp3': 'audio',
            '.m4a': 'audio',
            '.epub': 'epub',
            '.json': 'json',
            '.xml': 'xml',
            '.csv': 'csv',
            '.zip': 'zip',
            '.msg': 'msg',
        }
        return mapping.get(ext)

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
            strategy_str = strategy.value if isinstance(strategy, ConversionStrategy) else strategy
            raise ValueError(
                f"No converter available for {file_type.upper()} with strategy '{strategy_str}'. "
                f"Available strategies for {file_type.upper()}: {available}"
            )

        # Log conversion start
        strategy_str = strategy.value if isinstance(strategy, ConversionStrategy) else strategy
        console.print(f"[cyan]File Type:[/cyan] {file_type.upper()}")
        console.print(f"[cyan]Converting:[/cyan] {file_path.name}")
        console.print(f"[cyan]Strategy:[/cyan] {strategy_str}")
        console.print(f"[cyan]Converter:[/cyan] {converter.get_name()}")

        # Check cache first (v2.0 performance optimization)
        config_dict = self.config.model_dump(exclude={"enable_cache", "cache_max_age_hours", "cache_dir"})
        cached_result = self.cache.get(file_path, config_dict)

        if cached_result:
            console.print("[green]✓[/green] Using cached result")
            return cached_result

        # Perform conversion with progress and optional profiling
        timer = PerformanceTimer("conversion") if self.config.enable_profiling else None

        if timer:
            timer.__enter__()

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

        if timer:
            timer.__exit__(None, None, None)

        # Validate result
        if self.config.validate_output:
            self._validate_result(result)

        # Store in cache
        self.cache.set(file_path, config_dict, result)

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
        strategy: ConversionStrategy | str
    ) -> Optional[DocumentConverter]:
        """
        Get converter for the given file type and strategy.

        Args:
            file_type: File type ('pdf', 'html', 'docx', 'xlsx')
            strategy: Conversion strategy (enum or string)

        Returns:
            DocumentConverter instance or None
        """
        # Get strategy value (handle both enum and string)
        strategy_str = strategy.value if isinstance(strategy, ConversionStrategy) else strategy

        # Try exact match first
        key = (file_type, strategy_str)
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
