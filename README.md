# Multi-Format Document to Markdown Converter v2.0

A high-fidelity document to Markdown converter powered by **Microsoft MarkItDown**. Supports **13+ file formats** including PDF, DOCX, XLSX, PPTX, HTML, images (with OCR), audio (with transcription), EPub books, and more.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://github.com/yourusername/pdf2markdown)

## ✨ What's New in v2.0

**Major Release** - Complete rewrite powered by Microsoft MarkItDown!

- 🚀 **13+ Format Support**: PDF, DOCX, XLSX, PPTX, HTML, images, audio, EPub, ZIP, MSG, and more
- 🤖 **AI-Powered Features**: Optional OpenAI GPT-4 for image descriptions
- ☁️ **Azure Integration**: High-accuracy PDF conversion with Azure Document Intelligence
- 🎵 **Audio Transcription**: Convert audio files (WAV, MP3, M4A) to text
- 🎥 **YouTube Support**: Extract video transcripts directly from URLs
- 📚 **E-book Support**: Convert EPub books to Markdown
- 🖼️ **Enhanced OCR**: Built-in image OCR with AI descriptions
- 🎨 **Modern UI**: Redesigned Streamlit interface with batch processing
- 🔄 **Backward Compatible**: Legacy converters still available (deprecated)

## Features

### Supported Formats

#### 📄 Documents
- **PDF** - Portable Document Format with OCR support
- **DOCX** - Microsoft Word documents with formatting
- **XLSX** - Excel spreadsheets with charts and images
- **PPTX** - PowerPoint presentations

#### 🌐 Web & Data
- **HTML** - Web pages with external images
- **XML** - Structured XML documents
- **JSON** - JSON data files
- **CSV** - Comma-separated values

#### 🖼️ Images (with OCR)
- **JPG/JPEG** - JPEG images with optional OCR
- **PNG** - PNG images with optional OCR
- **GIF** - GIF images with optional OCR
- **BMP** - Bitmap images with optional OCR

#### 🎵 Audio (with Transcription)
- **WAV** - WAV audio with speech-to-text
- **MP3** - MP3 audio with speech-to-text
- **M4A** - M4A audio with speech-to-text

#### 📦 Other Formats
- **EPub** - E-book format
- **ZIP** - Archive files
- **MSG** - Outlook email messages
- **YouTube** - Video transcript extraction

### Core Capabilities

- ✅ **Universal Format Support**: 13+ formats via Microsoft MarkItDown
- 🤖 **AI-Powered**: Optional GPT-4 image descriptions
- ☁️ **Cloud Integration**: Azure Document Intelligence for PDFs
- 📊 **Complex Tables**: Automatic header detection and extraction
- 🖼️ **Smart Images**: Base64 embedding, external download, or separate export
- 📝 **Text Formatting**: Preserves bold, italic, headers, and lists
- 🔍 **Advanced OCR**: Image OCR with optional AI descriptions
- 🎯 **Multiple Interfaces**: CLI, Web UI (Streamlit), REST API (FastAPI)
- 🐳 **Docker Ready**: Containerized deployment
- ⚡ **Batch Processing**: Convert multiple files in parallel

## Quick Start

### Installation

#### Core Installation (MarkItDown only)

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf2markdown.git
cd pdf2markdown

# Install core dependencies
pip install -r requirements.txt
pip install -e .
```

#### With AI Features (Optional)

```bash
# Install LLM support (OpenAI GPT-4 for image descriptions)
pip install -r requirements-markitdown.txt

# Or install specific feature sets
pip install openai>=1.0.0  # For AI image descriptions

# For Azure Document Intelligence (high-accuracy PDFs)
pip install azure-ai-formrecognizer>=3.3.0

# For YouTube transcript extraction
pip install youtube-transcript-api>=0.6.0

# For audio transcription
pip install SpeechRecognition>=3.10.0 pydub>=0.25.1
```

#### Legacy Converters (Deprecated, Optional)

```bash
# Install legacy format-specific converters (for backward compatibility)
pip install -r requirements-legacy.txt
```

### Environment Configuration

Create a `.env` file for advanced features:

```bash
# LLM Configuration (Optional - for AI image descriptions)
PDF2MD_LLM_ENABLED=true
OPENAI_API_KEY=your_openai_api_key_here
PDF2MD_LLM_MODEL=gpt-4o

# Azure Document Intelligence (Optional - for high-accuracy PDFs)
AZURE_DOCINTEL_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCINTEL_KEY=your_azure_key_here
PDF2MD_AZURE_ENABLED=true

# Conversion Settings
PDF2MD_RICH_CONVERSION=false  # Extract detailed metadata
PDF2MD_USE_MARKITDOWN=true    # Use MarkItDown (recommended)
```

### Basic Usage

#### Command Line (v2.0)

```bash
# Convert any supported file to Markdown
pdf2md convert document.pdf -o output.md
pdf2md convert presentation.pptx -o output.md
pdf2md convert spreadsheet.xlsx -o output.md
pdf2md convert image.jpg -o output.md
pdf2md convert audio.mp3 -o output.md

# With AI image descriptions (requires OpenAI API key)
pdf2md convert document.pdf --llm-descriptions --llm-model gpt-4o

# With Azure Document Intelligence (for high-accuracy PDFs)
pdf2md convert scanned.pdf --azure

# With rich metadata extraction
pdf2md convert document.pdf --rich-metadata

# Embed images as base64
pdf2md convert document.pdf --images embed

# Extract images to separate files
pdf2md convert document.pdf --images link

# Batch convert multiple files
pdf2md batch ./docs/ --pattern "*.pdf" --output ./markdown/
pdf2md batch ./documents/ --output ./markdown/ --parallel 4

# YouTube transcript extraction
# (MarkItDown will handle YouTube URLs automatically)

# Check available converters
pdf2md check
```

#### Python API (v2.0)

```python
from pdf2markdown import convert_pdf
from pdf2markdown.core.config import Config
from pdf2markdown.core.orchestrator import ConversionOrchestrator

# Simple conversion (uses MarkItDown by default)
markdown = convert_pdf("document.pdf", output_path="output.md")

# With AI features
config = Config(
    use_markitdown=True,
    llm_enabled=True,
    llm_model="gpt-4o",
    azure_enabled=False,
    rich_conversion=True,
)

orchestrator = ConversionOrchestrator(config)
result = orchestrator.convert("document.pdf")

print(result.markdown)
print(f"Extracted {len(result.images)} images")
print(f"Extracted {len(result.tables)} tables")

# Save with images
result.save("output.md", save_images=True)
```

#### Web UI (v2.0 - Redesigned!)

```bash
# Start Streamlit interface
pdf2md serve --port 8501

# Or directly
streamlit run src/web/streamlit_app.py
```

Visit http://localhost:8501 in your browser.

**New v2.0 Features:**
- 📤 Upload & Convert tab with 13+ format support
- 📚 Formats Gallery showcasing all supported formats
- ⚡ Batch Processing with progress tracking
- 🔑 API Settings for OpenAI and Azure credentials
- 🎨 Modern sidebar with all configuration options
- 🖼️ Enhanced image pagination and preview

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
# Convert any supported file
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "use_markitdown=true" \
  -F "llm_enabled=false"

# With AI features
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "llm_enabled=true" \
  -F "llm_model=gpt-4o"

# Check supported formats
curl http://localhost:8000/formats

# Check health
curl http://localhost:8000/health
```

## Configuration

### Conversion Strategies

- **markitdown**: Microsoft MarkItDown - supports all formats (default)
- **auto**: Automatically detect best converter (legacy mode)
- **fast**: PyMuPDF (PDF only, deprecated in v2.0)
- **ocr**: Tesseract OCR (PDF only, deprecated in v2.0)

### Image Modes

- **embed**: Base64 encode images in markdown (default)
- **link**: Save images separately and link in markdown
- **separate**: Extract images but don't include in markdown

### Table Formats

- **github**: GitHub-flavored markdown tables (default)
- **pipe**: Simple pipe-delimited tables
- **grid**: Grid-style tables
- **html**: HTML tables for complex structures

### CLI Options (v2.0)

```
pdf2md convert [OPTIONS] INPUT_FILE

Supported formats: PDF, DOCX, XLSX, PPTX, HTML, JPG, PNG, GIF, BMP,
                   WAV, MP3, M4A, EPub, ZIP, MSG, CSV, XML, JSON

Options:
  -o, --output PATH           Output file path
  -s, --strategy [markitdown|auto|fast|ocr]
                              Conversion strategy (default: markitdown)

  # MarkItDown v2.0 Options
  --markitdown / --legacy     Use MarkItDown (default: True)
  --rich-metadata / --simple  Extract rich metadata (default: False)
  --llm-descriptions          Enable AI image descriptions (requires OpenAI)
  --llm-model TEXT            LLM model to use (default: gpt-4o)
  --azure                     Use Azure Document Intelligence for PDFs

  # Image Options
  -i, --images [embed|link|separate]
                              Image handling mode (default: embed)
  --extract-images / --no-extract-images
                              Extract images (default: True)

  # Table Options
  --extract-tables / --no-extract-tables
                              Extract tables (default: True)
  -t, --table-format [github|pipe|grid|html]
                              Table format (default: github)

  # OCR Options
  --ocr                       Force OCR
  --ocr-lang TEXT             Tesseract language code (default: eng)

  # Format-specific options (PDF, HTML, DOCX, XLSX)
  --page-breaks               Include page break markers (PDFs only)
  --html-download-images      Download external images from HTML
  --html-base-url TEXT        Base URL for resolving relative links
  --docx-include-comments     Include comments and tracked changes
  --xlsx-mode TEXT            Multi-sheet handling (combined/separate/selected)
  --xlsx-sheets TEXT          Comma-separated sheet names

  -v, --verbose               Verbose output
  --help                      Show this message and exit
```

## Advanced Features

### AI-Powered Image Descriptions

Enable GPT-4 powered image descriptions:

```bash
# Set OpenAI API key
export OPENAI_API_KEY=your_key_here

# Convert with AI descriptions
pdf2md convert document.pdf --llm-descriptions --llm-model gpt-4o

# Or in Python
config = Config(
    llm_enabled=True,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail for a technical document"
)
```

### Azure Document Intelligence

For high-accuracy PDF conversion:

```bash
# Set Azure credentials
export AZURE_DOCINTEL_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
export AZURE_DOCINTEL_KEY=your_key_here

# Convert with Azure
pdf2md convert scanned.pdf --azure

# Or in Python
config = Config(azure_enabled=True)
```

### Audio Transcription

Convert audio files to text:

```bash
# Requires: pip install SpeechRecognition pydub

pdf2md convert meeting.wav -o transcript.md
pdf2md convert podcast.mp3 -o transcript.md
```

### YouTube Transcripts

Extract YouTube video transcripts:

```bash
# Requires: pip install youtube-transcript-api

# MarkItDown handles YouTube URLs automatically
# Provide the URL via the Streamlit UI or API
```

### Rich Metadata Extraction

Extract detailed metadata using format-specific libraries:

```bash
pdf2md convert document.pdf --rich-metadata

# Extracts: author, title, creation date, keywords, etc.
```

### Batch Processing

```bash
# Convert all files in a directory
pdf2md batch ./documents/ --output ./markdown/

# Specific pattern
pdf2md batch ./documents/ --pattern "*.pdf" --recursive

# Parallel processing (8 workers)
pdf2md batch ./documents/ --parallel 8

# Stop on first error
pdf2md batch ./documents/ --fail-fast
```

### Docker Deployment

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
```

## Architecture

### v2.0 Architecture

```
pdf-to-markdown/
├── src/
│   ├── converters/          # Converter implementations
│   │   ├── document_converter.py    # Base interface
│   │   ├── markitdown_converter.py  # v2.0 primary (13+ formats)
│   │   ├── pymupdf_converter.py     # Legacy PDF (deprecated)
│   │   ├── ocr_converter.py         # Legacy OCR (deprecated)
│   │   ├── html_converter.py        # Legacy HTML (deprecated)
│   │   ├── docx_converter.py        # Legacy DOCX (deprecated)
│   │   └── xlsx_converter.py        # Legacy XLSX (deprecated)
│   ├── core/                # Core logic
│   │   ├── config.py        # Configuration models
│   │   ├── models.py        # Data models (ConversionResult, etc.)
│   │   ├── orchestrator.py  # Converter selection & execution
│   │   └── file_detector.py # File type detection
│   ├── cli/                 # CLI interface
│   │   └── main.py          # Typer CLI with v2.0 commands
│   ├── api/                 # REST API
│   │   └── app.py           # FastAPI with v2.0 endpoints
│   └── web/                 # Web interfaces
│       ├── streamlit_app.py # v2.0 redesigned UI
│       └── streamlit_app_v1_backup.py # v1.0 backup
├── tests/                   # Test suite
│   ├── test_markitdown_converter.py  # MarkItDown tests
│   └── test_*.py            # Legacy converter tests
├── requirements.txt         # Core dependencies (MarkItDown)
├── requirements-markitdown.txt  # Optional AI features
├── requirements-legacy.txt  # Legacy converters (deprecated)
├── .env.example            # Environment configuration template
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose
└── pyproject.toml         # Project metadata
```

### Converter Selection Logic

1. **Use MarkItDown** (default): Handles all 13+ formats
2. **Legacy Mode** (optional): Use format-specific converters
3. **Auto Mode**: Automatically select best converter

## Performance

### v2.0 Performance (MarkItDown)

| Format | Typical Speed | Notes |
|--------|--------------|-------|
| PDF | 0.5-2s/page | Fast, built-in OCR support |
| DOCX | <1s | Excellent formatting preservation |
| XLSX | <1s | Multi-sheet support |
| PPTX | <2s | Full presentation conversion |
| HTML | <1s | External image handling |
| Images | <2s | Optional OCR + AI descriptions |
| Audio | Varies | Depends on audio length |

### Legacy Converters (Deprecated)

| Converter | Speed (per page) | Accuracy | Resource Use |
|-----------|-----------------|----------|--------------|
| PyMuPDF   | 0.12s          | 85-90%   | Low (CPU)    |
| Tesseract | 3s             | 70-85%   | Medium (CPU) |

## Migration from v1.0 to v2.0

### Breaking Changes

1. **Default Converter**: Now uses MarkItDown instead of PyMuPDF
2. **Configuration**: New options for LLM and Azure features
3. **Streamlit UI**: Completely redesigned interface
4. **API Endpoints**: New `/formats` endpoint, updated request models

### Migration Steps

1. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt  # MarkItDown is now core
   ```

2. **Update Configuration**:
   ```python
   # Old (v1.0)
   config = Config(strategy=ConversionStrategy.FAST)

   # New (v2.0)
   config = Config(
       use_markitdown=True,  # New default
       strategy=ConversionStrategy.MARKITDOWN
   )
   ```

3. **CLI Changes**:
   ```bash
   # Old (v1.0) - still works
   pdf2md convert document.pdf --strategy fast

   # New (v2.0) - recommended
   pdf2md convert document.pdf --markitdown
   pdf2md convert document.pdf --llm-descriptions  # New feature
   ```

4. **Legacy Mode** (if needed):
   ```bash
   # Use legacy converters
   pip install -r requirements-legacy.txt
   pdf2md convert document.pdf --legacy --strategy fast
   ```

## Troubleshooting

### Common Issues

**1. MarkItDown Not Available**

```bash
pip install markitdown[all]>=0.1.0
```

**2. OpenAI API Key Not Found**

Set environment variable or configure in .env:
```bash
export OPENAI_API_KEY=your_key_here
```

**3. Azure Credentials Not Found**

Set environment variables or configure in .env:
```bash
export AZURE_DOCINTEL_ENDPOINT=https://...
export AZURE_DOCINTEL_KEY=your_key_here
```

**4. Audio Transcription Not Working**

Install optional dependencies:
```bash
pip install SpeechRecognition pydub
```

**5. YouTube Transcripts Not Available**

Install optional dependency:
```bash
pip install youtube-transcript-api
```

**6. Legacy Converters Not Available**

Install legacy dependencies if needed:
```bash
pip install -r requirements-legacy.txt
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Format code (line length: 100)
black src/ tests/

# Lint
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

### v2.0 Core Technology

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) - Universal document converter
- [OpenAI](https://openai.com/) - AI-powered image descriptions
- [Azure Document Intelligence](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence) - High-accuracy PDF conversion

### Supporting Libraries

- [Typer](https://typer.tiangolo.com/) - CLI framework
- [FastAPI](https://fastapi.tiangolo.com/) - REST API
- [Streamlit](https://streamlit.io/) - Web UI
- [Pydantic](https://pydantic.dev/) - Data validation

### Legacy Converters (Deprecated)

- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR
- [markdownify](https://github.com/matthewwithanm/python-markdownify) - HTML conversion
- [pypandoc](https://github.com/JessicaTegner/pypandoc) - DOCX conversion
- [pandas](https://pandas.pydata.org/) - XLSX table conversion

## Acknowledgments

Special thanks to:
- Microsoft for the excellent MarkItDown library
- The open-source community for all the supporting libraries
- Contributors and users for feedback and improvements

## Support

- 📧 Issues: [GitHub Issues](https://github.com/yourusername/pdf2markdown/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/pdf2markdown/discussions)
- 📖 Documentation: [Wiki](https://github.com/yourusername/pdf2markdown/wiki)

---

**Made with ❤️ for the open-source community**

**v2.0.0** - Powered by Microsoft MarkItDown
