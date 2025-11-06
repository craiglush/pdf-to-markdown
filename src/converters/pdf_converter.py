"""PDF-specific base converter class."""

from abc import abstractmethod
from pathlib import Path
from typing import List

from pdf2markdown.converters.document_converter import DocumentConverter
from pdf2markdown.core.models import ConversionResult


class PDFConverter(DocumentConverter):
    """
    Abstract base class specifically for PDF to Markdown converters.

    This class inherits from DocumentConverter and adds PDF-specific
    functionality while maintaining backward compatibility.
    """

    def get_supported_extensions(self) -> List[str]:
        """
        PDF converters support .pdf extension.

        Returns:
            List containing ['.pdf']
        """
        return ['.pdf']

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

    def validate_pdf(self, pdf_path: Path) -> None:
        """
        Validate that the file exists and is a PDF.

        This method is kept for backward compatibility.

        Args:
            pdf_path: Path to the PDF file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a PDF
        """
        # Use the parent validate_file method
        self.validate_file(pdf_path)

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
