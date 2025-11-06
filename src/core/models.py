"""Data models for conversion results and metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ExtractedImage(BaseModel):
    """Represents an extracted image from a PDF."""

    index: int
    page: int
    format: str
    width: int
    height: int
    size_bytes: int
    path: Optional[Path] = None
    base64_data: Optional[str] = None
    alt_text: str = ""

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class ExtractedTable(BaseModel):
    """Represents an extracted table from a PDF."""

    page: int
    index: int
    rows: int
    columns: int
    headers: List[str]
    data: List[List[str]]
    bbox: Optional[tuple[float, float, float, float]] = None  # x0, y0, x1, y1
    markdown: str

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class PageMetadata(BaseModel):
    """Metadata for a single page."""

    page_number: int
    width: float
    height: float
    rotation: int = 0
    has_text: bool = True
    has_images: bool = False
    has_tables: bool = False
    word_count: int = 0
    image_count: int = 0
    table_count: int = 0


class ConversionMetadata(BaseModel):
    """Metadata about the conversion process."""

    # Source document info
    source_path: Path
    source_size_bytes: int
    source_hash: Optional[str] = None

    # PDF metadata
    pdf_version: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None

    # Document structure
    page_count: int
    total_words: int = 0
    total_images: int = 0
    total_tables: int = 0

    # Conversion details
    strategy_used: str
    converter_name: str
    conversion_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)

    # Quality metrics
    confidence_score: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Page-level metadata
    pages: List[PageMetadata] = field(default_factory=list)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


@dataclass
class ConversionResult:
    """Complete result of a PDF conversion."""

    # Core output
    markdown: str

    # Extracted assets
    images: List[ExtractedImage] = field(default_factory=list)
    tables: List[ExtractedTable] = field(default_factory=list)

    # Metadata
    metadata: Optional[ConversionMetadata] = None

    # Output paths (if saved)
    output_path: Optional[Path] = None
    image_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate and compute derived fields."""
        if self.metadata:
            self.metadata.total_images = len(self.images)
            self.metadata.total_tables = len(self.tables)

    def save(self, output_path: Path, save_images: bool = True) -> None:
        """
        Save the conversion result to files.

        Args:
            output_path: Path to save the markdown file
            save_images: Whether to save extracted images
        """
        # Save markdown
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.markdown, encoding='utf-8')
        self.output_path = output_path

        # Save images if requested
        if save_images and self.images:
            image_dir = output_path.parent / f"{output_path.stem}_images"
            image_dir.mkdir(exist_ok=True)
            self.image_dir = image_dir

            for img in self.images:
                if img.base64_data:
                    # Save base64 image
                    import base64
                    img_path = image_dir / f"image_{img.page}_{img.index}.{img.format}"
                    img_data = base64.b64decode(img.base64_data)
                    img_path.write_bytes(img_data)
                    img.path = img_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "markdown": self.markdown,
            "images": [img.model_dump() for img in self.images],
            "tables": [tbl.model_dump() for tbl in self.tables],
            "metadata": self.metadata.model_dump() if self.metadata else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "image_dir": str(self.image_dir) if self.image_dir else None,
        }

    def get_summary(self) -> str:
        """Get a human-readable summary of the conversion."""
        if not self.metadata:
            return "Conversion completed"

        lines = [
            f"✓ Converted: {self.metadata.source_path.name}",
            f"  Pages: {self.metadata.page_count}",
            f"  Words: {self.metadata.total_words:,}",
            f"  Images: {self.metadata.total_images}",
            f"  Tables: {self.metadata.total_tables}",
            f"  Time: {self.metadata.conversion_time_seconds:.2f}s",
            f"  Strategy: {self.metadata.strategy_used}",
        ]

        if self.metadata.warnings:
            lines.append(f"  ⚠ Warnings: {len(self.metadata.warnings)}")

        if self.metadata.errors:
            lines.append(f"  ✗ Errors: {len(self.metadata.errors)}")

        return "\n".join(lines)
