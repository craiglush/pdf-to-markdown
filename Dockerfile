# Multi-stage Dockerfile for PDF to Markdown converter

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
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


# Development stage
FROM base as development

USER root

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

USER appuser

CMD ["bash"]


# API stage
FROM base as api

# Expose API port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "pdf2markdown.api.app:app", "--host", "0.0.0.0", "--port", "8000"]


# Streamlit stage
FROM base as streamlit

# Install web dependencies
USER root
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

USER appuser

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "src/web/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
