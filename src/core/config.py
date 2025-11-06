"""Configuration classes and enums for PDF to Markdown conversion."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ConversionStrategy(str, Enum):
    """Conversion strategy selection."""

    AUTO = "auto"  # Automatically detect best strategy
    FAST = "fast"  # Use PyMuPDF4LLM (fastest)
    ACCURATE = "accurate"  # Use Marker (highest accuracy, slow)
    OCR = "ocr"  # Force OCR for scanned documents


class ImageMode(str, Enum):
    """Image extraction and embedding modes."""

    EMBED = "embed"  # Embed as base64 in markdown
    LINK = "link"  # Save separately and link in markdown
    SEPARATE = "separate"  # Extract but don't include in markdown


class TableFormat(str, Enum):
    """Markdown table format styles."""

    GITHUB = "github"  # GitHub-flavored markdown (default)
    PIPE = "pipe"  # Simple pipe-delimited tables
    GRID = "grid"  # Grid-style tables
    HTML = "html"  # HTML tables (for complex structures)


class Config(BaseModel):
    """Configuration for PDF conversion."""

    # Strategy selection
    strategy: ConversionStrategy = Field(
        default=ConversionStrategy.AUTO,
        description="Conversion strategy to use"
    )

    # Image handling
    image_mode: ImageMode = Field(
        default=ImageMode.EMBED,
        description="How to handle extracted images"
    )
    extract_images: bool = Field(
        default=True,
        description="Whether to extract images from PDF"
    )
    image_dir: Optional[Path] = Field(
        default=None,
        description="Directory to save extracted images (for link/separate modes)"
    )
    image_format: str = Field(
        default="png",
        description="Format for extracted images (png, jpg, webp)"
    )
    max_image_width: Optional[int] = Field(
        default=None,
        description="Maximum width for extracted images (None = no resize)"
    )

    # Table handling
    table_format: TableFormat = Field(
        default=TableFormat.GITHUB,
        description="Markdown table format"
    )
    extract_tables: bool = Field(
        default=True,
        description="Whether to extract and convert tables"
    )

    # Text formatting
    preserve_formatting: bool = Field(
        default=True,
        description="Preserve text formatting (bold, italic, etc.)"
    )
    preserve_links: bool = Field(
        default=True,
        description="Preserve hyperlinks"
    )

    # OCR settings
    ocr_enabled: bool = Field(
        default=False,
        description="Enable OCR for scanned PDFs"
    )
    ocr_language: str = Field(
        default="eng",
        description="Tesseract language code(s), e.g., 'eng' or 'eng+fra'"
    )
    ocr_dpi: int = Field(
        default=300,
        description="DPI for OCR image rendering"
    )

    # Layout detection
    detect_columns: bool = Field(
        default=True,
        description="Detect and handle multi-column layouts"
    )
    page_width: Optional[int] = Field(
        default=None,
        description="Override page width for column detection"
    )

    # Output options
    include_metadata: bool = Field(
        default=True,
        description="Include document metadata in output"
    )
    include_page_breaks: bool = Field(
        default=False,
        description="Add page break markers in markdown"
    )
    page_break_marker: str = Field(
        default="---",
        description="Markdown to use for page breaks"
    )

    # Performance
    parallel_pages: bool = Field(
        default=False,
        description="Process pages in parallel (experimental)"
    )
    max_workers: int = Field(
        default=4,
        description="Maximum number of parallel workers"
    )

    # Quality settings
    min_confidence: float = Field(
        default=0.7,
        description="Minimum confidence threshold for auto fallback"
    )
    validate_output: bool = Field(
        default=True,
        description="Validate output quality"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AppSettings(BaseSettings):
    """Application-level settings (environment variables)."""

    # Application
    app_name: str = Field(default="PDF to Markdown Converter")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Paths
    temp_dir: Path = Field(default=Path("/tmp/pdf2md"))
    cache_dir: Path = Field(default=Path.home() / ".cache" / "pdf2md")

    # API settings (for web interface)
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    api_max_file_size: int = Field(default=50 * 1024 * 1024)  # 50MB

    # Celery settings (for async processing)
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # Model settings
    marker_model_dir: Optional[Path] = Field(
        default=None,
        description="Directory for Marker model files"
    )

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "PDF2MD_"


# Global settings instance
settings = AppSettings()
