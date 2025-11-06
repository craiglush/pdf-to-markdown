# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a high-fidelity PDF to Markdown converter with three interfaces (CLI, Web UI, REST API) and multiple conversion strategies. The project uses a plugin-based architecture where converters implement a common interface, and an orchestrator intelligently selects the best converter based on PDF characteristics.

## Development Setup

```bash
# Install for development
pip install -r requirements-dev.txt
pip install -e .

# Verify installation
pdf2md check

# Install optional web dependencies
pip install -r requirements-web.txt
```

### System Dependencies

The project requires Tesseract OCR for scanned PDF support:
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr poppler-utils`
- macOS: `brew install tesseract poppler`
- Windows: Install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Running the Application

```bash
# CLI conversion
pdf2md convert document.pdf -o output.md

# Web UI (Streamlit)
pdf2md serve --port 8501
# Or directly: streamlit run src/web/streamlit_app.py

# REST API (FastAPI)
pdf2md serve --interface fastapi --port 8000
# Or directly: uvicorn pdf2markdown.api.app:app --host 0.0.0.0 --port 8000

# Docker
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

**Converter Pattern**: All converters implement `PDFConverter` abstract base class (src/converters/base.py) with required methods:
- `convert(pdf_path) -> ConversionResult` - Main conversion logic
- `supports_ocr() -> bool` - OCR capability flag
- `get_name() -> str` - Human-readable name
- `is_available() -> bool` - Check if dependencies are installed

**Strategy Selection**: `ConversionOrchestrator` (src/core/orchestrator.py) manages converter selection:
1. Receives conversion request with strategy (auto/fast/ocr/accurate)
2. If "auto", analyzes PDF to detect if scanned (no text layer)
3. Selects appropriate converter from registry
4. Executes conversion and validates results
5. Can fallback to alternative converters on failure

**Data Flow**:
```
User Request → Orchestrator → Converter Selection → PDF Analysis
                                                   ↓
Result Validation ← Conversion Result ← Convert PDF
```

### Adding New Converters

To add a new converter (e.g., Marker AI for high-accuracy):

1. Create new file in `src/converters/` (e.g., `marker_converter.py`)
2. Inherit from `PDFConverter` base class
3. Implement required abstract methods
4. Register in orchestrator's `_initialize_converters()` method
5. Add to `ConversionStrategy` enum in `src/core/config.py`

Example:
```python
from pdf2markdown.converters.base import PDFConverter

class MarkerConverter(PDFConverter):
    def convert(self, pdf_path: Path) -> ConversionResult:
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
```

### Configuration System

Configuration uses Pydantic models (src/core/config.py):
- `Config` - Conversion options (strategy, image mode, table format, OCR settings)
- `AppSettings` - Application settings (loaded from environment with `PDF2MD_` prefix)

Environment variables in `.env` override defaults. See `.env.example` for available settings.

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
├── converters/          # Converter implementations
│   ├── base.py         # Abstract base class (implement this for new converters)
│   ├── pymupdf_converter.py  # Fast converter using PyMuPDF4LLM
│   └── ocr_converter.py      # Tesseract-based OCR converter
├── core/
│   ├── config.py       # Pydantic config models and enums
│   ├── models.py       # Result data models (ConversionResult, etc.)
│   └── orchestrator.py # Converter selection and execution logic
├── cli/
│   └── main.py         # Typer CLI with commands: convert, batch, info, serve, check
├── api/
│   └── app.py          # FastAPI endpoints: /convert, /convert/async, /convert/batch
└── web/
    └── streamlit_app.py # Streamlit UI with file upload and result tabs
```

## Key Design Patterns

**Strategy Pattern**: Different converters (Fast/OCR/Accurate) implement same interface, selected at runtime.

**Factory Pattern**: Orchestrator creates and manages converter instances based on availability and strategy.

**Result Object Pattern**: `ConversionResult` encapsulates all conversion outputs and provides utility methods (`save()`, `to_dict()`, `get_summary()`).

**Configuration Management**: Pydantic settings with environment variable support, type validation, and defaults.

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

### Modifying Configuration

1. Add field to `Config` class in `src/core/config.py`
2. Update CLI options in `src/cli/main.py`
3. Update API parameters in `src/api/app.py`
4. Update Streamlit widgets in `src/web/streamlit_app.py`

## Important Implementation Notes

**Import Path**: The package name is `pdf2markdown` but source lives in `src/`. The `pyproject.toml` maps `pdf2markdown` to `src/` via `tool.setuptools.package-dir`.

**Converter Registry**: Orchestrator discovers converters at initialization by checking `is_available()`. Missing dependencies don't cause failures - converters are simply not registered.

**Error Handling**: Converters should raise:
- `FileNotFoundError` for missing PDFs
- `ValueError` for invalid PDFs
- Generic `Exception` for conversion errors

The orchestrator catches these and provides user-friendly messages via Rich console.

**Docker Stages**: Multi-stage Dockerfile builds different images:
- `base` - CLI with core dependencies
- `api` - FastAPI server
- `streamlit` - Web UI
- `development` - Full dev environment with tools

Use Docker Compose profiles: `--profile web`, `--profile api`, `--profile dev`

## Performance Considerations

**PyMuPDF Converter**: Fast (0.12s/page) but lower accuracy on complex layouts. Use for standard documents.

**OCR Converter**: Slower (3s/page) but handles scanned PDFs. Requires preprocessing and Tesseract.

**Batch Processing**: Use `--parallel N` flag for concurrent conversions. Default workers: 4.

**Image Modes**:
- `embed` - Base64 in markdown (increases file size)
- `link` - Separate image files (better for large images)
- `separate` - Extract but don't reference (for analysis)

## Troubleshooting

**"Command not found: pdf2md"**: Run `pip install -e .` to install CLI entry point.

**"No module named 'pymupdf'"**: PyMuPDF conflicts with old `fitz` package. Uninstall both, reinstall: `pip install pymupdf`.

**"Tesseract not found"**: System package required, not Python package. Install via OS package manager.

**Poor table extraction**: PyMuPDF's `find_tables()` struggles with borderless tables. Consider adding Camelot or pdfplumber as alternative table extractors.

**Scanned PDFs produce empty output**: Orchestrator should auto-detect and use OCR, but can be forced with `--strategy ocr`.
