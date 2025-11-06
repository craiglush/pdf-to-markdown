"""Configuration classes and enums for document to Markdown conversion."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ConversionStrategy(str, Enum):
    """Conversion strategy selection."""

    AUTO = "auto"  # Automatically detect best strategy
    FAST = "fast"  # Use PyMuPDF4LLM or MarkItDown (fastest)
    ACCURATE = "accurate"  # Use Marker or Azure Document Intelligence (highest accuracy, slow)
    OCR = "ocr"  # Force OCR for scanned documents
    MARKITDOWN = "markitdown"  # Use MarkItDown for all formats


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
    """Configuration for document conversion (PDF, HTML, DOCX, XLSX, PPTX, audio, etc.)."""

    # MarkItDown settings (v2.0 core converter)
    use_markitdown: bool = Field(
        default=True,
        description="Use MarkItDown as primary converter (recommended)"
    )
    rich_conversion: bool = Field(
        default=False,
        description="Extract detailed metadata using format-specific libraries (slower)"
    )

    # LLM-powered features
    llm_enabled: bool = Field(
        default=False,
        description="Enable LLM-powered image descriptions (requires OpenAI API key)"
    )
    llm_model: str = Field(
        default="gpt-4o",
        description="OpenAI model for image descriptions (gpt-4o, gpt-4-turbo, etc.)"
    )
    llm_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for LLM image descriptions"
    )

    # Azure Document Intelligence
    azure_enabled: bool = Field(
        default=False,
        description="Use Azure Document Intelligence for high-accuracy PDF conversion"
    )

    # MarkItDown plugins
    markitdown_enable_plugins: bool = Field(
        default=False,
        description="Enable 3rd-party MarkItDown plugins (disabled by default for security)"
    )

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

    # General table settings (applies to all formats)
    max_table_width: int = Field(
        default=120,
        description="Maximum table width in characters (wider tables use HTML or CSV)"
    )

    # HTML-specific settings
    html_preserve_semantic: bool = Field(
        default=False,
        description="Preserve semantic HTML tags in markdown comments"
    )
    html_download_images: bool = Field(
        default=True,
        description="Download and save remote images from HTML"
    )
    html_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for resolving relative URLs in HTML"
    )

    # DOCX-specific settings
    docx_include_comments: bool = Field(
        default=False,
        description="Include document comments in output"
    )
    docx_include_headers_footers: bool = Field(
        default=True,
        description="Include headers and footers in output"
    )
    docx_show_changes: bool = Field(
        default=False,
        description="Show tracked changes in output"
    )

    # XLSX-specific settings
    xlsx_mode: str = Field(
        default="combined",
        description="Multi-sheet handling: 'combined', 'separate', or 'selected'"
    )
    xlsx_sheets: Optional[list[str]] = Field(
        default=None,
        description="List of sheet names to convert (for 'selected' mode)"
    )
    xlsx_show_formulas: bool = Field(
        default=False,
        description="Show formulas alongside values"
    )
    xlsx_extract_charts: bool = Field(
        default=True,
        description="Extract charts as images"
    )
    xlsx_max_sheet_width: int = Field(
        default=100,
        description="Maximum number of columns per sheet"
    )

    # Validators to ensure enum fields are properly coerced from strings
    @field_validator('strategy', mode='before')
    @classmethod
    def validate_strategy(cls, v):
        if isinstance(v, str):
            return ConversionStrategy(v)
        return v

    @field_validator('image_mode', mode='before')
    @classmethod
    def validate_image_mode(cls, v):
        if isinstance(v, str):
            return ImageMode(v)
        return v

    @field_validator('table_format', mode='before')
    @classmethod
    def validate_table_format(cls, v):
        if isinstance(v, str):
            return TableFormat(v)
        return v


class AppSettings(BaseSettings):
    """Application-level settings (environment variables)."""

    # Application
    app_name: str = Field(default="Document to Markdown Converter")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Paths
    temp_dir: Path = Field(default=Path("/tmp/pdf2md"))
    cache_dir: Path = Field(default=Path.home() / ".cache" / "pdf2md")

    # MarkItDown settings
    use_markitdown: bool = Field(default=True)
    rich_conversion: bool = Field(default=False)
    llm_enabled: bool = Field(default=False)
    llm_model: str = Field(default="gpt-4o")
    azure_enabled: bool = Field(default=False)
    markitdown_enable_plugins: bool = Field(default=False)

    # Conversion settings
    strategy: str = Field(default="auto")
    image_mode: str = Field(default="embed")
    table_format: str = Field(default="github")
    batch_workers: int = Field(default=4)

    # Cache settings
    cache_enabled: bool = Field(default=False)

    # API settings (for web interface)
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    api_max_file_size: int = Field(default=50 * 1024 * 1024)  # 50MB

    # Streamlit settings
    streamlit_port: int = Field(default=8501)

    # Celery settings (for async processing)
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # Model settings (legacy)
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
