# Multi-stage Dockerfile for Multi-Format Document to Markdown Converter v2.0
# Powered by Microsoft MarkItDown

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# Note: Tesseract and poppler still useful for OCR and PDF preprocessing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    ghostscript \
    pandoc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install core dependencies (includes MarkItDown)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Install package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Default command (CLI)
CMD ["pdf2md", "--help"]


# Development stage with all features
FROM base as development

USER root

# Install all optional dependencies
COPY requirements-dev.txt .
COPY requirements-markitdown.txt .
COPY requirements-legacy.txt .

RUN pip install --no-cache-dir -r requirements-dev.txt && \
    pip install --no-cache-dir -r requirements-markitdown.txt && \
    pip install --no-cache-dir -r requirements-legacy.txt

USER appuser

CMD ["bash"]


# Full-featured stage (with AI and legacy support)
FROM base as full

USER root

# Install MarkItDown optional features and legacy converters
COPY requirements-markitdown.txt .
COPY requirements-legacy.txt .

RUN pip install --no-cache-dir -r requirements-markitdown.txt && \
    pip install --no-cache-dir -r requirements-legacy.txt

USER appuser

CMD ["pdf2md", "--help"]


# API stage (v2.0)
FROM base as api

USER root

# Install web dependencies (FastAPI, uvicorn) and optional MarkItDown features
COPY requirements-web.txt .
COPY requirements-markitdown.txt .
RUN pip install --no-cache-dir -r requirements-web.txt && \
    pip install --no-cache-dir -r requirements-markitdown.txt || true

USER appuser

# Expose API port
EXPOSE 8000

# Environment variables for API
ENV PDF2MD_USE_MARKITDOWN=true \
    PDF2MD_API_WORKERS=4

# Run FastAPI server
CMD ["uvicorn", "pdf2markdown.api.app:app", "--host", "0.0.0.0", "--port", "8000"]


# Streamlit stage (v2.0)
FROM base as streamlit

USER root

# Install web dependencies and optional features
COPY requirements-web.txt .
COPY requirements-markitdown.txt .

RUN pip install --no-cache-dir -r requirements-web.txt && \
    pip install --no-cache-dir -r requirements-markitdown.txt || true

USER appuser

# Expose Streamlit port
EXPOSE 8501

# Environment variables for Streamlit
ENV PDF2MD_USE_MARKITDOWN=true

# Run Streamlit v2.0 UI
CMD ["streamlit", "run", "src/web/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
