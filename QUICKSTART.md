# Quick Start Guide

Get up and running with PDF to Markdown converter in 5 minutes!

## 1. Installation (1 minute)

```bash
# Clone and install
git clone https://github.com/yourusername/pdf2markdown.git
cd pdf2markdown
pip install -r requirements.txt
pip install -e .
```

## 2. First Conversion (30 seconds)

```bash
# Convert a PDF to Markdown
pdf2md convert your-document.pdf

# Output will be saved as your-document.md
```

That's it! Your PDF is now converted to Markdown.

## 3. Common Use Cases

### Convert with embedded images

```bash
pdf2md convert document.pdf --images embed
```

### Batch convert multiple PDFs

```bash
pdf2md batch ./pdfs/ --output ./markdown/
```

### Convert scanned PDF with OCR

```bash
# Install Tesseract first (see below)
pdf2md convert scanned.pdf --ocr
```

### Start web interface

```bash
pdf2md serve
# Opens at http://localhost:8501
```

## 4. Install OCR (Optional, 2 minutes)

For scanned PDFs:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [here](https://github.com/UB-Mannheim/tesseract/wiki)

## 5. Python Usage

```python
from pdf2markdown import convert_pdf

# Simple conversion
markdown = convert_pdf("document.pdf")
print(markdown)

# Save to file
markdown = convert_pdf("document.pdf", output_path="output.md")
```

## Next Steps

- 📖 Read the [full README](README.md) for detailed documentation
- 🔧 Check [INSTALL.md](INSTALL.md) for installation troubleshooting
- 💻 See [examples/](examples/) for advanced usage
- 🚀 Start the [API server](README.md#rest-api) for programmatic access

## Common Options

```bash
# Get PDF info without converting
pdf2md info document.pdf

# Check what converters are available
pdf2md check

# Convert with specific strategy
pdf2md convert document.pdf --strategy fast

# Extract images to separate files
pdf2md convert document.pdf --images link

# Custom table format
pdf2md convert document.pdf --table-format github
```

## Help

```bash
# General help
pdf2md --help

# Command-specific help
pdf2md convert --help
pdf2md batch --help
pdf2md serve --help
```

## Docker Quick Start

```bash
# Build
docker-compose build

# Convert a PDF
docker-compose run --rm cli pdf2md convert /input/document.pdf

# Start web UI
docker-compose --profile web up streamlit
```

## Troubleshooting

**"Command not found"**
```bash
# Make sure you installed the package
pip install -e .

# Or run directly
python -m pdf2markdown.cli.main convert document.pdf
```

**"PyMuPDF not found"**
```bash
pip install pymupdf pymupdf4llm
```

**"Tesseract not found"**
```bash
# Install system package (see step 4 above)
# Then verify
tesseract --version
```

## Features at a Glance

| Feature | Command | Description |
|---------|---------|-------------|
| Basic conversion | `pdf2md convert file.pdf` | Convert PDF to Markdown |
| Batch processing | `pdf2md batch ./pdfs/` | Convert multiple PDFs |
| OCR support | `pdf2md convert --ocr` | Extract text from scans |
| Web UI | `pdf2md serve` | Browser-based interface |
| REST API | `pdf2md serve --interface fastapi` | HTTP API |
| Docker | `docker-compose up` | Containerized deployment |

---

**Ready to go!** Start converting your PDFs to Markdown now! 🚀
