# Document to Markdown Converter

A high-fidelity document to Markdown converter with support for **PDF**, **HTML**, **DOCX**, and **XLSX** files. Features include complex table extraction, image handling, multi-column layouts, and OCR for scanned PDFs.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### Multi-Format Support
- 📄 **PDF**: Fast conversion (0.12s/page), OCR for scanned documents, multi-column layouts
- 🌐 **HTML**: External image download, relative link resolution, semantic tag preservation
- 📝 **DOCX**: Dual converter (pypandoc + mammoth fallback), formatting preservation, table extraction
- 📊 **XLSX**: Spreadsheet conversion with pandas, multi-sheet handling, chart extraction

### Core Capabilities
- ✅ **Fast Conversion**: 0.12s per page with PyMuPDF4LLM
- 📊 **Complex Tables**: Automatic header detection and table extraction
- 🖼️ **Image Handling**: Base64 embedding, external download, or separate file export
- 📝 **Text Formatting**: Preserves bold, italic, headers, and lists
- 🔍 **OCR Support**: Tesseract integration for scanned PDFs
- 🎯 **Multiple Interfaces**: CLI, Web UI (Streamlit), REST API (FastAPI)
- 🐳 **Docker Ready**: Containerized deployment options

## Quick Start

### Installation

#### Option 1: pip install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf2markdown.git
cd pdf2markdown

# Install with pip
pip install -r requirements.txt
pip install -e .
```

#### Option 2: Docker

```bash
# Build Docker image
docker-compose build

# Run CLI
docker-compose run --rm cli pdf2md convert /input/document.pdf -o /output/document.md

# Start web UI
docker-compose --profile web up streamlit

# Start REST API
docker-compose --profile api up api
```

### Basic Usage

#### Command Line

```bash
# Convert a PDF to Markdown
pdf2md convert document.pdf -o output.md

# Convert an HTML file to Markdown
pdf2md convert page.html -o output.md

# Convert a DOCX file to Markdown
pdf2md convert report.docx -o output.md

# Convert DOCX with comments and tracked changes
pdf2md convert report.docx --docx-include-comments

# Convert with base URL for relative links (HTML)
pdf2md convert page.html --html-base-url https://example.com

# Auto-detect scanned PDFs and use OCR
pdf2md convert scanned.pdf -o output.md --strategy auto

# Embed images as base64
pdf2md convert document.pdf --images embed

# Extract images to separate files
pdf2md convert document.pdf --images link

# Batch convert multiple files (supports PDF, HTML, DOCX, XLSX)
pdf2md batch ./docs/ --pattern "*.html" --output ./markdown/
pdf2md batch ./pdfs/ --output ./markdown/ --parallel 4

# Get PDF information
pdf2md info document.pdf

# Check converter availability
pdf2md check
```

#### Python API

```python
from pdf2markdown import convert_pdf

# Simple conversion
markdown = convert_pdf("document.pdf", output_path="output.md")

# With custom options
markdown = convert_pdf(
    "document.pdf",
    strategy="auto",
    extract_images=True,
    extract_tables=True,
    ocr_enabled=False,
)
print(markdown)
```

#### Web UI

```bash
# Start Streamlit interface
pdf2md serve --port 8501

# Or directly
streamlit run src/web/streamlit_app.py
```

Visit http://localhost:8501 in your browser.

#### REST API

```bash
# Start FastAPI server
pdf2md serve --interface fastapi --port 8000

# Or directly
uvicorn pdf2markdown.api.app:app --host 0.0.0.0 --port 8000
```

API documentation at http://localhost:8000/docs

Example API usage:

```bash
# Convert a PDF
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "strategy=auto" \
  -F "image_mode=embed"

# Check health
curl http://localhost:8000/health

# List available converters
curl http://localhost:8000/converters
```

## Configuration

### Conversion Strategies

- **auto**: Automatically detect best strategy (default)
- **fast**: PyMuPDF4LLM - fastest (0.12s/page)
- **accurate**: Marker AI - highest accuracy (11.3s/page, requires additional installation)
- **ocr**: Tesseract OCR - for scanned PDFs (3s/page)

### Image Modes

- **embed**: Base64 encode images in markdown (default)
- **link**: Save images separately and link in markdown
- **separate**: Extract images but don't include in markdown

### Table Formats

- **github**: GitHub-flavored markdown tables (default)
- **pipe**: Simple pipe-delimited tables
- **grid**: Grid-style tables
- **html**: HTML tables for complex structures

### CLI Options

```
pdf2md convert [OPTIONS] INPUT_FILE

Supported formats: PDF, HTML, DOCX, XLSX

Options:
  -o, --output PATH           Output file path
  -s, --strategy [auto|fast|accurate|ocr]
                              Conversion strategy (default: auto, mainly for PDFs)
  -i, --images [embed|link|separate]
                              Image handling mode (default: embed)
  --extract-images / --no-extract-images
                              Extract images (default: True)
  --extract-tables / --no-extract-tables
                              Extract tables (default: True)
  -t, --table-format [github|pipe|grid|html]
                              Table format (default: github)
  --ocr                       Force OCR for scanned PDFs
  --ocr-lang TEXT             Tesseract language code (default: eng)
  --page-breaks               Include page break markers (PDFs only)

  # HTML-specific options
  --html-download-images / --html-no-download-images
                              Download external images from HTML (default: True)
  --html-base-url TEXT        Base URL for resolving relative links in HTML

  # DOCX-specific options
  --docx-include-comments / --docx-no-include-comments
                              Include comments and tracked changes (default: False)
  --docx-include-headers-footers / --docx-no-include-headers-footers
                              Include headers and footers (default: False)

  # XLSX-specific options
  --xlsx-mode TEXT            Multi-sheet handling: combined, separate, or selected (default: combined)
  --xlsx-sheets TEXT          Comma-separated list of sheet names for 'selected' mode
  --xlsx-extract-charts / --xlsx-no-extract-charts
                              Extract charts as images (default: True)

  -v, --verbose               Verbose output
  --help                      Show this message and exit
```

## Advanced Features

### OCR for Scanned PDFs

Install Tesseract OCR:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract tesseract-lang

# Windows (via Chocolatey)
choco install tesseract
```

Use OCR:

```bash
# Auto-detect and apply OCR if needed
pdf2md convert scanned.pdf --strategy auto

# Force OCR
pdf2md convert document.pdf --ocr --ocr-lang eng

# Multiple languages
pdf2md convert document.pdf --ocr --ocr-lang eng+fra
```

### High-Accuracy AI Conversion (Optional)

Install Marker for highest accuracy:

```bash
pip install marker-pdf torch
```

Use accurate strategy:

```bash
pdf2md convert document.pdf --strategy accurate
```

**Note**: First run downloads ~1GB model, requires more resources but provides 95-99% accuracy.

### HTML to Markdown Conversion

Convert HTML files with advanced features:

```bash
# Basic HTML conversion
pdf2md convert page.html -o output.md

# Download external images (default: True)
pdf2md convert page.html --html-download-images

# Keep external images as links (faster)
pdf2md convert page.html --html-no-download-images

# Resolve relative links with base URL
pdf2md convert page.html --html-base-url https://example.com/docs/

# Combine with image embedding
pdf2md convert page.html --images embed --html-download-images
```

**HTML Conversion Features:**
- ✅ Semantic HTML preservation (headings, lists, code blocks, tables)
- ✅ External image download and embedding
- ✅ Relative link resolution with configurable base URL
- ✅ Data URI image handling
- ✅ Malformed HTML handling (via BeautifulSoup)
- ✅ Table extraction with automatic header detection

**Installation:**
```bash
# Install HTML conversion dependencies
pip install -r requirements-html.txt

# Or install with optional HTML support
pip install -e ".[html]"
```

### DOCX to Markdown Conversion

Convert DOCX files with dual-converter support:

```bash
# Basic DOCX conversion (uses pypandoc if available, falls back to mammoth)
pdf2md convert document.docx -o output.md

# Include comments and tracked changes
pdf2md convert document.docx --docx-include-comments

# Include headers and footers
pdf2md convert document.docx --docx-include-headers-footers

# Combine options
pdf2md convert document.docx --docx-include-comments --docx-include-headers-footers
```

**DOCX Conversion Features:**
- ✅ Dual converter support: pypandoc (primary) + mammoth (fallback)
- ✅ Formatting preservation (bold, italic, headings, lists)
- ✅ Table extraction with automatic header detection
- ✅ Image extraction with metadata
- ✅ Optional comments and tracked changes
- ✅ Optional headers and footers
- ✅ Document metadata extraction (title, author, etc.)

**Installation:**
```bash
# Install DOCX conversion dependencies
pip install -r requirements-docx.txt

# Or install with optional DOCX support
pip install -e ".[docx]"

# For pypandoc support (recommended), install pandoc:
# Ubuntu/Debian: sudo apt-get install pandoc
# macOS: brew install pandoc
# Windows: choco install pandoc
```

**Note**: pypandoc requires the pandoc system package. If pandoc is not installed, the converter automatically falls back to mammoth.

### XLSX to Markdown Conversion

Convert Excel spreadsheets with powerful multi-sheet handling:

```bash
# Basic XLSX conversion (combines all sheets)
pdf2md convert spreadsheet.xlsx -o output.md

# Separate mode: Each sheet as its own section
pdf2md convert workbook.xlsx -o output.md --xlsx-mode separate

# Selected mode: Convert specific sheets only
pdf2md convert workbook.xlsx --xlsx-mode selected --xlsx-sheets "Sheet1,Sheet3"

# Extract charts as images
pdf2md convert report.xlsx --xlsx-extract-charts

# Combine options
pdf2md convert financial.xlsx --xlsx-mode combined --images embed
```

**XLSX Conversion Features:**
- ✅ Multi-sheet handling (combined, separate, selected)
- ✅ Table conversion with pandas (supports all table formats)
- ✅ Chart extraction as images using openpyxl
- ✅ Embedded image extraction
- ✅ Wide table handling (auto-truncation for readability)
- ✅ Formula display support
- ✅ Metadata extraction (author, title, creation date)
- ✅ Support for .xlsx, .xls, and .xlsm formats

**Multi-Sheet Modes:**
- **combined**: All sheets in one document with headers
- **separate**: Each sheet as a separate section
- **selected**: Only specific sheets (use --xlsx-sheets)

**Installation:**
```bash
# Install XLSX conversion dependencies
pip install -r requirements-xlsx.txt

# Or install with optional XLSX support
pip install -e ".[xlsx]"

# Dependencies: pandas, openpyxl, Pillow
```

**Note**: pandas and openpyxl are required for XLSX conversion. Install them to enable this feature.

### Batch Processing

```bash
# Convert all PDFs in a directory
pdf2md batch ./pdfs/ --output ./markdown/

# Recursive search
pdf2md batch ./documents/ --recursive --pattern "*.pdf"

# Parallel processing
pdf2md batch ./pdfs/ --parallel 8

# Stop on first error
pdf2md batch ./pdfs/ --fail-fast
```

### Python API Advanced Usage

```python
from pdf2markdown.core.config import Config, ConversionStrategy, ImageMode
from pdf2markdown.core.orchestrator import ConversionOrchestrator

# Custom configuration
config = Config(
    strategy=ConversionStrategy.FAST,
    image_mode=ImageMode.LINK,
    extract_images=True,
    extract_tables=True,
    table_format="github",
    ocr_enabled=True,
    ocr_language="eng+fra",
    include_page_breaks=True,
)

# Convert with custom config
orchestrator = ConversionOrchestrator(config)
result = orchestrator.convert("document.pdf")

# Access results
print(result.markdown)
print(f"Extracted {len(result.images)} images")
print(f"Extracted {len(result.tables)} tables")

# Save to files
result.save("output.md", save_images=True)

# Get summary
print(result.get_summary())
```

## Docker Deployment

**Full Format Support**: The Docker images now include all format converters (PDF, HTML, DOCX, XLSX) with their required dependencies pre-installed.

### Quick Start with Docker

```bash
# Build all images
docker-compose build

# Run CLI converter
docker-compose run --rm cli pdf2md convert /input/document.pdf -o /output/document.md

# Start web UI (Streamlit)
docker-compose --profile web up streamlit
# Access at http://localhost:8501

# Start REST API
docker-compose --profile api up api
# API docs at http://localhost:8000/docs

# Verify all converters are available
docker-compose run --rm cli pdf2md check
```

### Development

```bash
# Start development environment
docker-compose --profile dev up -d dev
docker-compose exec dev bash
```

### Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: pdf2markdown:api
    ports:
      - "8000:8000"
    environment:
      - PDF2MD_API_WORKERS=8
      - PDF2MD_DEBUG=false
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

Run:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

```
pdf-to-markdown/
├── src/
│   ├── converters/          # PDF converter implementations
│   │   ├── base.py          # Base converter interface
│   │   ├── pymupdf_converter.py  # Fast converter
│   │   └── ocr_converter.py      # OCR converter
│   ├── processors/          # Document processors
│   ├── core/                # Core logic
│   │   ├── config.py        # Configuration
│   │   ├── models.py        # Data models
│   │   └── orchestrator.py # Conversion orchestration
│   ├── cli/                 # CLI interface
│   │   └── main.py          # Typer CLI
│   ├── api/                 # REST API
│   │   └── app.py           # FastAPI application
│   └── web/                 # Web interfaces
│       └── streamlit_app.py # Streamlit UI
├── tests/                   # Test suite
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Core dependencies
└── pyproject.toml          # Project metadata
```

## Performance

| Converter | Speed (per page) | Accuracy | Resource Use | OCR Support |
|-----------|-----------------|----------|--------------|-------------|
| PyMuPDF   | 0.12s          | 85-90%   | Low (CPU)    | External    |
| Marker    | 11.3s          | 95-99%   | High (GPU)   | Built-in    |
| Tesseract | 3s             | 70-85%   | Medium (CPU) | Primary     |

## Troubleshooting

### Common Issues

**1. Import Error: No module named 'pymupdf'**

```bash
pip install pymupdf pymupdf4llm
```

**2. Tesseract not found**

Install Tesseract OCR system package (see OCR section).

**3. Poor OCR results**

- Increase DPI: Add `--ocr-dpi 600` flag
- Try image preprocessing
- Ensure correct language pack installed

**4. Tables not detected**

- Some PDFs use images for tables
- Try OCR strategy: `--strategy ocr`
- Use accurate strategy for complex tables

**5. Images too large**

- Use link mode: `--images link`
- Reduce image size in config

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built with:
- [PyMuPDF](https://pymupdf.readthedocs.io/) - Fast PDF processing
- [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) - LLM-ready markdown conversion
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR support
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [FastAPI](https://fastapi.tiangolo.com/) - REST API
- [Streamlit](https://streamlit.io/) - Web UI

## Acknowledgments

Special thanks to the PyMuPDF team for their excellent PDF library and pymupdf4llm conversion tool.

## Support

- 📧 Issues: [GitHub Issues](https://github.com/yourusername/pdf2markdown/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/pdf2markdown/discussions)
- 📖 Documentation: [Wiki](https://github.com/yourusername/pdf2markdown/wiki)

---

**Made with ❤️ for the open-source community**
