"""OCR-based converter for scanned PDFs using pytesseract."""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from pdf2markdown.converters.base import PDFConverter
from pdf2markdown.core.config import Config
from pdf2markdown.core.models import (
    ConversionMetadata,
    ConversionResult,
    ExtractedImage,
    PageMetadata,
)


class OCRConverter(PDFConverter):
    """
    OCR-based converter for scanned PDFs using Tesseract.

    This converter:
    - Converts PDF pages to images
    - Runs OCR on each page
    - Extracts text to Markdown
    - Handles scanned documents without text layers
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the OCR converter."""
        super().__init__(config)

    def get_name(self) -> str:
        """Get converter name."""
        return "OCR Converter (Tesseract)"

    def is_available(self) -> bool:
        """Check if pytesseract and dependencies are available."""
        try:
            import pytesseract
            from pdf2image import convert_from_path

            # Test if tesseract is actually installed
            pytesseract.get_tesseract_version()
            return True
        except (ImportError, Exception):
            return False

    def supports_ocr(self) -> bool:
        """This converter is specifically for OCR."""
        return True

    def convert(self, pdf_path: Path) -> ConversionResult:
        """
        Convert a scanned PDF to Markdown using OCR.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ConversionResult with OCR-extracted text
        """
        self.validate_pdf(pdf_path)

        start_time = time.time()

        # Convert PDF to images
        images = self._pdf_to_images(pdf_path)

        # Process each page with OCR
        markdown_parts = []
        page_metadata = []
        total_words = 0

        for page_num, image in enumerate(images, start=1):
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)

            # Run OCR
            text = self._ocr_image(processed_image)

            # Count words
            word_count = len(text.split())
            total_words += word_count

            # Add to markdown
            if text.strip():
                if self.config.include_metadata:
                    markdown_parts.append(f"<!-- Page {page_num} -->")
                markdown_parts.append(text)

                if self.config.include_page_breaks and page_num < len(images):
                    markdown_parts.append(self.config.page_break_marker)

            # Create page metadata
            page_meta = PageMetadata(
                page_number=page_num,
                width=float(image.width),
                height=float(image.height),
                rotation=0,
                has_text=bool(text.strip()),
                has_images=False,
                has_tables=False,
                word_count=word_count,
                image_count=0,
                table_count=0,
            )
            page_metadata.append(page_meta)

        # Combine markdown
        markdown_text = "\n\n".join(markdown_parts)

        # Create metadata
        conversion_time = time.time() - start_time

        metadata = ConversionMetadata(
            source_path=pdf_path,
            source_size_bytes=pdf_path.stat().st_size,
            source_hash=self._calculate_file_hash(pdf_path),
            page_count=len(images),
            total_words=total_words,
            strategy_used=self.config.strategy.value,
            converter_name=self.get_name(),
            conversion_time_seconds=conversion_time,
            timestamp=datetime.now(),
            pages=page_metadata,
            warnings=[
                "OCR-based conversion may have lower accuracy than native text extraction",
                f"Processed with Tesseract language: {self.config.ocr_language}",
            ],
        )

        return ConversionResult(
            markdown=markdown_text,
            images=[],
            tables=[],
            metadata=metadata,
        )

    def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of PIL Image objects
        """
        try:
            images = convert_from_path(
                str(pdf_path),
                dpi=self.config.ocr_dpi,
                fmt=self.config.image_format,
            )
            return images
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert('L')

        # Optional: Apply additional preprocessing
        # - Increase contrast
        # - Remove noise
        # - Deskew
        # These are advanced features that can be added later

        return image

    def _ocr_image(self, image: Image.Image) -> str:
        """
        Run OCR on an image.

        Args:
            image: PIL Image to OCR

        Returns:
            Extracted text
        """
        try:
            # Configure OCR
            config = '--psm 3'  # Fully automatic page segmentation

            # Run Tesseract
            text = pytesseract.image_to_string(
                image,
                lang=self.config.ocr_language,
                config=config,
            )

            return text.strip()

        except Exception as e:
            print(f"Warning: OCR failed: {e}")
            return ""

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def estimate_conversion_time(self, pdf_path: Path) -> float:
        """
        Estimate OCR conversion time.

        OCR is much slower than text extraction.
        Roughly 2-5 seconds per page at 300 DPI.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Estimated time in seconds
        """
        try:
            import pymupdf as fitz

            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()

            # Estimate 3 seconds per page for OCR
            return page_count * 3.0

        except Exception:
            return 30.0  # Default estimate
