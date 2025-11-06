# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-06

### Added
- Initial release of PDF to Markdown converter
- PyMuPDF-based fast converter (0.12s per page)
- OCR support via Tesseract for scanned PDFs
- Complex table extraction with automatic header detection
- Image extraction with three modes: embed, link, separate
- Multi-column layout detection and proper reading order
- Text formatting preservation (bold, italic, headers, lists)
- Three user interfaces:
  - Typer-based CLI with rich output
  - Streamlit web UI for interactive conversion
  - FastAPI REST API for programmatic access
- Batch processing with parallel workers
- Docker support with multi-stage builds
- Comprehensive configuration system with Pydantic
- Conversion orchestrator with auto-strategy selection
- Quality validation and confidence scoring
- Detailed metadata extraction (document info, page-level stats)
- Multiple table formats (GitHub, pipe, grid, HTML)
- Progress indicators and verbose logging
- Health check and converter availability endpoints

### Documentation
- Comprehensive README with examples
- Detailed installation guide (INSTALL.md)
- Quick start guide (QUICKSTART.md)
- Advanced usage examples (examples/advanced_usage.py)
- API documentation via FastAPI automatic docs
- Docker deployment examples
- Troubleshooting section

### Features by Interface

#### CLI (`pdf2md`)
- `convert` - Convert single PDF with rich options
- `batch` - Batch convert directory of PDFs
- `info` - Display PDF information without converting
- `serve` - Launch web UI or API server
- `check` - Verify converter availability
- `version` - Display version information

#### Python API
- Simple one-line conversion function
- Full configuration access via Config class
- ConversionOrchestrator for strategy management
- Rich result objects with metadata
- Direct converter access for advanced use

#### Web UI (Streamlit)
- Drag-and-drop file upload
- Real-time conversion progress
- Tabbed result view (Markdown, Preview, Images, Metadata)
- Configuration sidebar with all options
- Download buttons for results
- Image gallery for extracted images

#### REST API (FastAPI)
- `POST /convert` - Synchronous conversion
- `POST /convert/async` - Asynchronous background processing
- `GET /convert/status/{job_id}` - Check async job status
- `POST /convert/batch` - Batch conversion
- `GET /converters` - List available converters
- `GET /health` - Health check endpoint
- Automatic OpenAPI documentation at `/docs`

### Performance
- Fast conversion: ~0.12s per page (PyMuPDF)
- OCR conversion: ~3s per page (Tesseract)
- Supports PDFs up to 50MB by default (configurable)
- Parallel batch processing
- Memory-efficient streaming for large documents

### Supported Features
- ✅ Text extraction with formatting
- ✅ Complex tables with merged cells
- ✅ Image extraction (PNG, JPG, all PyMuPDF formats)
- ✅ Multi-column layouts
- ✅ OCR for scanned PDFs
- ✅ Hyperlink preservation
- ✅ Page break markers
- ✅ Custom table formats
- ✅ Multiple image modes
- ✅ Metadata extraction

### Dependencies
- pymupdf >= 1.24.0
- pymupdf4llm >= 0.0.7
- pytesseract >= 0.3.10
- pdf2image >= 1.16.0
- typer >= 0.9.0
- rich >= 13.0.0
- pydantic >= 2.0.0

### Optional Dependencies
- streamlit >= 1.28.0 (Web UI)
- fastapi >= 0.104.0 (REST API)
- uvicorn >= 0.24.0 (API server)
- marker-pdf >= 0.2.0 (High-accuracy converter)

### Known Limitations
- Merged cells in tables require post-processing
- Very complex multi-column layouts may have reading order issues
- Password-protected PDFs not supported yet
- Form fields not extracted
- Annotations/comments not preserved
- AI-based accurate converter (Marker) not included in base install

### Breaking Changes
- None (initial release)

### Security
- No known security issues
- Runs in sandboxed Docker containers
- Non-root user in Docker images
- File size limits to prevent DoS
- Input validation on all API endpoints

## [Unreleased]

### Planned Features
- Marker AI converter integration for highest accuracy
- Password-protected PDF support
- Form field extraction
- Annotation preservation
- Multi-language OCR improvements
- Custom preprocessing pipelines
- Result caching
- Database integration for job storage
- Webhook support for async notifications
- S3 and cloud storage integration
- Kubernetes deployment examples
- Performance benchmarks
- More comprehensive test suite

### Future Improvements
- GPU acceleration for OCR
- Advanced table cell merging algorithms
- Better multi-column detection
- Improved scanned document preprocessing
- Custom model fine-tuning options
- Plugin system for custom converters
- Real-time conversion streaming
- Browser extension for web-based PDFs

---

For more information about each release, see the [GitHub Releases](https://github.com/yourusername/pdf2markdown/releases) page.
