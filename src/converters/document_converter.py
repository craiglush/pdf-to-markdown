"""Base abstract class for all document converters (PDF, HTML, DOCX, XLSX, etc.)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from pdf2markdown.core.config import Config
from pdf2markdown.core.models import ConversionResult


class DocumentConverter(ABC):
    """
    Abstract base class for all document to Markdown converters.

    This is the foundation for all format-specific converters (PDF, HTML, DOCX, XLSX).
    All converter implementations must inherit from this class and implement the
    required methods.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the converter.

        Args:
            config: Configuration for conversion options
        """
        self.config = config or Config()

    @abstractmethod
    def convert(self, file_path: Path) -> ConversionResult:
        """
        Convert a document file to Markdown.

        Args:
            file_path: Path to the document file to convert

        Returns:
            ConversionResult containing the markdown and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not valid or supported
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
        Get the human-readable name of this converter.

        Returns:
            Converter name (e.g., "PyMuPDF Fast Converter", "HTML Converter")
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

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get the list of file extensions this converter supports.

        Returns:
            List of extensions (e.g., ['.pdf'], ['.html', '.htm'])
        """
        pass

    def validate_file(self, file_path: Path) -> None:
        """
        Validate that the file exists and is supported by this converter.

        Args:
            file_path: Path to the file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file extension
        extension = file_path.suffix.lower()
        supported = self.get_supported_extensions()

        if extension not in supported:
            raise ValueError(
                f"File extension '{extension}' not supported by {self.get_name()}. "
                f"Supported extensions: {', '.join(supported)}"
            )

    def estimate_conversion_time(self, file_path: Path) -> float:
        """
        Estimate the time required to convert this file.

        Args:
            file_path: Path to the file

        Returns:
            Estimated time in seconds
        """
        # Default implementation: simple file size based estimation
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            # Rough estimate: 1 second per MB
            return max(1.0, file_size_mb)
        except Exception:
            return 10.0  # Default fallback

    def __repr__(self) -> str:
        """String representation of the converter."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.get_name()}', "
            f"available={self.is_available()}, "
            f"extensions={self.get_supported_extensions()})"
        )
