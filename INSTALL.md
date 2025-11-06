# Installation Guide

## System Requirements

- Python 3.9 or higher
- 2GB RAM minimum (4GB recommended)
- 500MB disk space (plus space for models if using AI converters)

## Quick Install

### Using pip

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/pdf2markdown.git
cd pdf2markdown

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install the package
pip install -r requirements.txt
pip install -e .

# 4. Verify installation
pdf2md --version
pdf2md check
```

## Platform-Specific Instructions

### Ubuntu/Debian Linux

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    ghostscript

# Install Python package
pip install -r requirements.txt
pip install -e .
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11
brew install tesseract tesseract-lang
brew install poppler
brew install libmagic

# Install Python package
pip3 install -r requirements.txt
pip3 install -e .
```

### Windows

```powershell
# Install Python from python.org (3.9+)
# Download and install: https://www.python.org/downloads/

# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR

# Install poppler (for pdf2image)
# Download from: https://github.com/oschwartz10612/poppler-windows/releases/
# Extract and add bin/ to PATH

# Install Python package
pip install -r requirements.txt
pip install -e .
```

## Optional Components

### Web Interface (Streamlit + FastAPI)

```bash
pip install -r requirements-web.txt
```

### High-Accuracy AI Converter (Marker)

⚠️ **Warning**: Downloads ~1GB model on first use

```bash
pip install marker-pdf torch torchvision
```

For GPU acceleration:
```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Development Tools

```bash
pip install -r requirements-dev.txt
```

## Docker Installation

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 1.29+

### Build and Run

```bash
# Clone repository
git clone https://github.com/yourusername/pdf2markdown.git
cd pdf2markdown

# Build all images
docker-compose build

# Run CLI
docker-compose run --rm cli pdf2md --help

# Start web UI
docker-compose --profile web up streamlit

# Start REST API
docker-compose --profile api up api
```

## Verification

### Check Installation

```bash
# Check converter availability
pdf2md check

# Should show:
# ✓ Fast (PyMuPDF): Available
# ✓ OCR (Tesseract): Available
# ○ Accurate (Marker): Not installed (optional)
```

### Test Conversion

```bash
# Download a sample PDF or use your own
pdf2md info your-document.pdf

# Convert to Markdown
pdf2md convert your-document.pdf -o output.md

# View the output
cat output.md
```

## Troubleshooting

### Common Installation Issues

#### 1. Python version too old

```bash
# Check Python version
python --version

# If < 3.9, upgrade:
# Ubuntu/Debian
sudo apt-get install python3.11

# macOS
brew install python@3.11

# Windows: Download from python.org
```

#### 2. pip install fails

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Try with verbose output
pip install -r requirements.txt -v
```

#### 3. Tesseract not found

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Install from
# https://github.com/UB-Mannheim/tesseract/wiki

# Verify installation
tesseract --version
```

#### 4. PyMuPDF import error

```bash
# Uninstall conflicting packages
pip uninstall PyMuPDF fitz pymupdf

# Reinstall
pip install pymupdf
```

#### 5. pdf2image requires poppler

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows: Download from
# https://github.com/oschwartz10612/poppler-windows/releases/
# Extract and add to PATH
```

### Offline Installation

1. Download requirements on a machine with internet:

```bash
pip download -r requirements.txt -d packages/
```

2. Transfer `packages/` directory to offline machine

3. Install from local packages:

```bash
pip install --no-index --find-links=packages/ -r requirements.txt
```

## Upgrading

### Upgrade from pip

```bash
cd pdf2markdown
git pull origin main
pip install -r requirements.txt --upgrade
pip install -e . --upgrade
```

### Upgrade Docker images

```bash
docker-compose build --no-cache
docker-compose --profile api up -d api
```

## Uninstallation

### Remove Python package

```bash
pip uninstall pdf2markdown
```

### Remove all dependencies

```bash
pip uninstall -r requirements.txt -y
```

### Remove system packages (Ubuntu/Debian)

```bash
sudo apt-get remove tesseract-ocr poppler-utils
sudo apt-get autoremove
```

## Next Steps

- Read the [README.md](README.md) for usage instructions
- Check [examples/](examples/) for sample conversions
- Visit [API documentation](http://localhost:8000/docs) after starting the API server
- Join [discussions](https://github.com/yourusername/pdf2markdown/discussions) for help

## Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/yourusername/pdf2markdown/issues)
2. Search [GitHub Discussions](https://github.com/yourusername/pdf2markdown/discussions)
3. Create a new issue with:
   - Your OS and Python version
   - Full error message
   - Steps to reproduce
   - Output of `pdf2md check`
