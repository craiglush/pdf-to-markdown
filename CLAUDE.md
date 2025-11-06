# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a high-fidelity **multi-format document to Markdown converter** supporting PDF, HTML, DOCX, and XLSX files. It provides three interfaces (CLI, Web UI, REST API) with intelligent format detection and conversion strategy selection. The architecture uses a plugin-based design where format-specific converters implement a common `DocumentConverter` interface, and an orchestrator selects the appropriate converter based on file type and characteristics.

## Development Setup

```bash
# Install core dependencies
pip install -r requirements.txt
pip install -e .

# Install format-specific dependencies (optional)
pip install -r requirements-html.txt   # HTML support
pip install -r requirements-docx.txt   # DOCX support
pip install -r requirements-xlsx.txt   # XLSX support
pip install -r requirements-web.txt    # Web UI + API

# Install development tools
pip install -r requirements-dev.txt

# Verify installation and check available converters
pdf2md check
```

### System Dependencies

**Tesseract OCR** (for scanned PDF support):
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr poppler-utils`
- macOS: `brew install tesseract poppler`
- Windows: Install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

**Pandoc** (recommended for DOCX, falls back to mammoth if unavailable):
- Ubuntu/Debian: `sudo apt-get install pandoc`
- macOS: `brew install pandoc`
- Windows: `choco install pandoc`

## Running the Application

```bash
# CLI conversion (auto-detects format)
pdf2md convert document.pdf -o output.md
pdf2md convert page.html -o output.md
pdf2md convert report.docx -o output.md
pdf2md convert spreadsheet.xlsx -o output.md

# Format-specific options
pdf2md convert page.html --html-base-url https://example.com
pdf2md convert report.docx --docx-include-comments
pdf2md convert workbook.xlsx --xlsx-mode separate

# Batch conversion (supports all formats)
pdf2md batch ./docs/ --pattern "*.html" --output ./markdown/

# Web UI (Streamlit)
pdf2md serve --port 8501
# Or directly: streamlit run src/web/streamlit_app.py

# REST API (FastAPI)
pdf2md serve --interface fastapi --port 8000
# Or directly: uvicorn pdf2markdown.api.app:app --host 0.0.0.0 --port 8000

# Docker (all format converters included)
docker-compose build
docker-compose --profile web up streamlit
docker-compose --profile api up api
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_converters.py

# Run specific test
pytest tests/test_converters.py::test_pymupdf_conversion
```

## Code Quality

```bash
# Format code (line length: 100)
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/
```

## Architecture

### Core Components

**Multi-Format Converter Pattern**: All converters implement `DocumentConverter` abstract base class (src/converters/document_converter.py):
- `convert(file_path) -> ConversionResult` - Main conversion logic
- `supports_ocr() -> bool` - OCR capability flag
- `get_name() -> str` - Human-readable name
- `is_available() -> bool` - Check if dependencies are installed
- `get_supported_extensions() -> List[str]` - Supported file extensions

**File Type Detection**: `FileTypeDetector` (src/core/file_detector.py) uses multi-layered detection:
1. Extension-based detection (fast)
2. Magic bytes signature verification
3. MIME type detection (if python-magic available)
4. Office format differentiation (DOCX vs XLSX - both are ZIP-based)
5. Content analysis fallback

**Orchestration**: `ConversionOrchestrator` (src/core/orchestrator.py) manages format detection and converter selection:
1. Detects file type using `FileTypeDetector`
2. For PDFs: analyzes document to determine strategy (auto/fast/ocr/accurate)
3. For other formats: uses format-specific default converter
4. Selects appropriate converter from registry: `{(file_type, strategy): converter}`
5. Executes conversion and validates results
6. Can fallback to alternative converters on failure

**Data Flow**:
```
User Request → File Type Detection → Converter Selection → Document Analysis (PDFs)
                                                          ↓
Result Validation ← Conversion Result ← Format-Specific Conversion
```

**Available Converters**:
- **PDF**: `PyMuPDFConverter` (fast), `OCRConverter` (scanned PDFs)
- **HTML**: `HTMLConverter` (requires markdownify, beautifulsoup4)
- **DOCX**: `DOCXConverter` (dual: pypandoc primary, mammoth fallback)
- **XLSX**: `XLSXConverter` (requires pandas, openpyxl)

### Adding New Converters

To add a new converter (e.g., Marker AI for PDFs, or PPTX support):

1. Create new file in `src/converters/` (e.g., `marker_converter.py`, `pptx_converter.py`)
2. Inherit from `DocumentConverter` base class (src/converters/document_converter.py)
3. Implement required abstract methods
4. Register in orchestrator's `_initialize_converters()` method
5. For PDFs: Add to `ConversionStrategy` enum in `src/core/config.py`
6. For new formats: Add extension mappings to `FileTypeDetector` (src/core/file_detector.py)

Example (new PDF converter):
```python
from pdf2markdown.converters.document_converter import DocumentConverter

class MarkerConverter(DocumentConverter):
    def convert(self, file_path: Path) -> ConversionResult:
        # Implementation
        pass

    def supports_ocr(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Marker AI Converter"

    def is_available(self) -> bool:
        try:
            import marker
            return True
        except ImportError:
            return False

    def get_supported_extensions(self) -> List[str]:
        return ['.pdf']
```

Example (new format converter):
```python
from pdf2markdown.converters.document_converter import DocumentConverter

class PPTXConverter(DocumentConverter):
    def get_supported_extensions(self) -> List[str]:
        return ['.pptx', '.ppt']

    # Implement other required methods...
```

### Configuration System

Configuration uses Pydantic models (src/core/config.py):
- `Config` - Conversion options (strategy, image mode, table format, OCR settings)
- `AppSettings` - Application settings (loaded from environment with `PDF2MD_` prefix)
- Format-specific options: `html_*`, `docx_*`, `xlsx_*` fields in Config

Environment variables in `.env` override defaults. See `.env.example` for available settings.

**Format-Specific Configuration**:
- **HTML**: `html_download_images`, `html_base_url`
- **DOCX**: `docx_include_comments`, `docx_include_headers_footers`
- **XLSX**: `xlsx_mode` (combined/separate/selected), `xlsx_sheets`, `xlsx_extract_charts`

### Result Models

`ConversionResult` (src/core/models.py) contains:
- `markdown: str` - Generated markdown
- `images: List[ExtractedImage]` - Extracted images with metadata
- `tables: List[ExtractedTable]` - Extracted tables with markdown
- `metadata: ConversionMetadata` - Document and conversion metadata

All models use Pydantic for validation and serialization.

## Module Organization

```
src/
├── converters/               # Converter implementations
│   ├── document_converter.py  # Abstract base class for ALL converters
│   ├── pdf_converter.py       # Legacy PDF-specific base (deprecated)
│   ├── base.py               # Old base class (deprecated, use document_converter.py)
│   ├── pymupdf_converter.py  # Fast PDF converter using PyMuPDF4LLM
│   ├── ocr_converter.py      # Tesseract-based OCR PDF converter
│   ├── html_converter.py     # HTML to Markdown (markdownify + beautifulsoup4)
│   ├── docx_converter.py     # DOCX to Markdown (pypandoc + mammoth fallback)
│   └── xlsx_converter.py     # XLSX to Markdown (pandas + openpyxl)
├── core/
│   ├── config.py          # Pydantic config models and enums
│   ├── models.py          # Result data models (ConversionResult, etc.)
│   ├── orchestrator.py    # Format detection & converter selection
│   └── file_detector.py   # Multi-layered file type detection
├── cli/
│   └── main.py            # Typer CLI: convert, batch, info, serve, check
├── api/
│   └── app.py             # FastAPI endpoints: /convert, /convert/async, /convert/batch
└── web/
    └── streamlit_app.py   # Streamlit UI with multi-format upload support
```

## Key Design Patterns

**Strategy Pattern**: Different converters implement the same `DocumentConverter` interface, selected at runtime based on file type and strategy.

**Factory Pattern**: Orchestrator creates and manages converter instances based on availability, file type, and conversion strategy.

**Registry Pattern**: Converter registry maps `(file_type, strategy)` tuples to converter instances. E.g., `('pdf', 'fast')` → `PyMuPDFConverter`, `('html', 'default')` → `HTMLConverter`.

**Graceful Degradation**: Converters check `is_available()` before registration. Missing optional dependencies (HTML/DOCX/XLSX) don't break the core PDF functionality.

**Dual-Converter Fallback** (DOCX): Primary converter (pypandoc) with automatic fallback to secondary (mammoth) if pandoc system package is unavailable.

**Result Object Pattern**: `ConversionResult` encapsulates all conversion outputs and provides utility methods (`save()`, `to_dict()`, `get_summary()`).

**Configuration Management**: Pydantic settings with environment variable support, type validation, format-specific options, and defaults.

## Common Tasks

### Adding CLI Command

Add new command to `src/cli/main.py`:
```python
@app.command()
def mycommand(
    arg: str = typer.Argument(..., help="Description"),
    option: bool = typer.Option(False, "--flag", help="Description"),
) -> None:
    """Command description."""
    # Implementation
```

### Adding API Endpoint

Add new endpoint to `src/api/app.py`:
```python
@app.post("/endpoint", tags=["Category"])
async def my_endpoint(
    file: UploadFile = File(...),
) -> ResponseModel:
    """Endpoint description."""
    # Implementation
```

### Adding New Format Support

To add a new file format (e.g., PPTX):

1. Create converter in `src/converters/new_format_converter.py`
2. Add extension mapping to `EXTENSION_MAP` in `src/core/file_detector.py`
3. Add MIME type mapping to `MIME_MAP` in `src/core/file_detector.py` (optional)
4. Add magic bytes signature to `MAGIC_SIGNATURES` in `src/core/file_detector.py` (optional)
5. Register converter in `ConversionOrchestrator._initialize_converters()`
6. Add format-specific CLI options to `src/cli/main.py`
7. Update API to accept new format in `src/api/app.py`
8. Update Streamlit file uploader accepted types in `src/web/streamlit_app.py`

### Modifying Configuration

1. Add field to `Config` class in `src/core/config.py`
2. Update CLI options in `src/cli/main.py`
3. Update API parameters in `src/api/app.py`
4. Update Streamlit widgets in `src/web/streamlit_app.py`

## Important Implementation Notes

**Import Path**: The package name is `pdf2markdown` but source lives in `src/`. The `pyproject.toml` maps `pdf2markdown` to `src/` via `tool.setuptools.package-dir`.

**Converter Registry**: Orchestrator discovers converters at initialization by checking `is_available()`. Missing optional dependencies (HTML/DOCX/XLSX) don't cause failures - converters are simply not registered. Core PDF functionality always works.

**Optional Dependencies**: Format-specific converters are wrapped in try/except blocks in orchestrator. The orchestrator sets flags like `HTML_AVAILABLE`, `DOCX_AVAILABLE`, `XLSX_AVAILABLE` to gracefully handle missing dependencies.

**File Type Detection**: Uses multi-layered approach (extension → magic bytes → MIME → content analysis). Special handling for ZIP-based formats (DOCX/XLSX) - checks internal directory structure (`word/` vs `xl/`) to differentiate.

**DOCX Dual Converter**: DOCXConverter tries pypandoc first (requires pandoc system package), automatically falls back to mammoth if unavailable. Both converters are wrapped in the same class, transparent to the user.

**Error Handling**: Converters should raise:
- `FileNotFoundError` for missing files
- `ValueError` for invalid/unsupported files
- Generic `Exception` for conversion errors

The orchestrator catches these and provides user-friendly messages via Rich console.

**Docker**: Multi-stage Dockerfile with all format converters included:
- `base` - CLI with ALL format dependencies (PDF, HTML, DOCX, XLSX)
- `api` - FastAPI server with all formats
- `streamlit` - Web UI with all formats
- `development` - Full dev environment with tools

Use Docker Compose profiles: `--profile web`, `--profile api`, `--profile dev`

## Performance Considerations

**PDF Converters**:
- **PyMuPDF**: Fast (0.12s/page) but lower accuracy on complex layouts. Use for standard documents.
- **OCR**: Slower (3s/page) but handles scanned PDFs. Requires preprocessing and Tesseract.

**Other Format Converters**:
- **HTML**: Fast, depends on image download time if enabled
- **DOCX**: pypandoc is faster and more accurate than mammoth fallback
- **XLSX**: Performance depends on sheet size; wide tables auto-truncate for readability

**Batch Processing**: Use `--parallel N` flag for concurrent conversions. Default workers: 4. Works for all supported formats.

**Image Modes** (all formats):
- `embed` - Base64 in markdown (increases file size, portable)
- `link` - Separate image files (better for large images, faster)
- `separate` - Extract but don't reference (for analysis)

## Troubleshooting

**"Command not found: pdf2md"**: Run `pip install -e .` to install CLI entry point.

**"No module named 'pymupdf'"**: PyMuPDF conflicts with old `fitz` package. Uninstall both, reinstall: `pip install pymupdf`.

**"Tesseract not found"**: System package required, not Python package. Install via OS package manager.

**"No module named 'markdownify'"** (HTML): Install HTML dependencies: `pip install -r requirements-html.txt`

**"No module named 'pypandoc'"** (DOCX): Install DOCX dependencies: `pip install -r requirements-docx.txt`. Note: pypandoc will fallback to mammoth if pandoc system package is unavailable.

**"No module named 'pandas'"** (XLSX): Install XLSX dependencies: `pip install -r requirements-xlsx.txt`

**"Converter not available"**: Run `pdf2md check` to see which converters are available and which dependencies are missing.

**"Unsupported file type"**: Ensure file extension is correct. Supported: `.pdf`, `.html`, `.htm`, `.docx`, `.doc`, `.xlsx`, `.xls`

**Poor table extraction (PDFs)**: PyMuPDF's `find_tables()` struggles with borderless tables. Consider adding Camelot or pdfplumber as alternative table extractors.

**Scanned PDFs produce empty output**: Orchestrator should auto-detect and use OCR, but can be forced with `--strategy ocr`.

**DOCX conversion quality low**: Ensure pandoc system package is installed for best results. The mammoth fallback is less accurate.
