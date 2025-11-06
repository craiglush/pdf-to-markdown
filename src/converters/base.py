"""Base abstract class for PDF converters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from pdf2markdown.core.config import Config
from pdf2markdown.core.models import ConversionResult


class PDFConverter(ABC):
    """
    Abstract base class for PDF to Markdown converters.

    All converter implementations must inherit from this class and
    implement the required methods.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the converter.

        Args:
            config: Configuration for conversion options
        """
        self.config = config or Config()

    @abstractmethod
    def convert(self, pdf_path: Path) -> ConversionResult:
        """
        Convert a PDF file to Markdown.

        Args:
            pdf_path: Path to the PDF file to convert

        Returns:
            ConversionResult containing the markdown and metadata

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
            Exception: For other conversion errors
        """
        pass

    @abstractmethod
    def supports_ocr(self) -> bool:
        """
        Check if this converter supports OCR for scanned documents.

        Returns:
            True if OCR is supported, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this converter.

        Returns:
            Human-readable name of the converter
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this converter is available (dependencies installed, etc.).

        Returns:
            True if the converter can be used, False otherwise
        """
        pass

    def validate_pdf(self, pdf_path: Path) -> None:
        """
        Validate that the file exists and is a PDF.

        Args:
            pdf_path: Path to the PDF file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")

        # Check file extension
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

    def detect_scanned_pdf(self, pdf_path: Path) -> bool:
        """
        Detect if a PDF is scanned (image-based) or has a text layer.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if the PDF appears to be scanned, False if it has text
        """
        try:
            import pymupdf as fitz

            doc = fitz.open(pdf_path)

            # Check first few pages for text content
            pages_to_check = min(3, len(doc))
            text_found = False

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()

                if text:
                    text_found = True
                    break

            doc.close()

            # If no text found in first few pages, likely scanned
            return not text_found

        except Exception:
            # If we can't determine, assume not scanned
            return False

    def estimate_conversion_time(self, pdf_path: Path) -> float:
        """
        Estimate the time required to convert this PDF.

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

            # Base estimate: 0.1 seconds per page for fast converters
            # Add overhead for images and tables
            return page_count * 0.1

        except Exception:
            # Default estimate if we can't open the file
            return 10.0

    def __repr__(self) -> str:
        """String representation of the converter."""
        return f"{self.__class__.__name__}(available={self.is_available()})"
