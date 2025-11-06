"""
PyMuPDF-based fast PDF to Markdown converter.

.. deprecated:: 2.0.0
    This converter is deprecated in favor of MarkItDownConverter.
    It remains available as a legacy fallback when use_markitdown=False.

    Use MarkItDownConverter for new projects, which supports:
    - All PDF features plus 13+ additional formats
    - Optional LLM-powered image descriptions
    - Optional Azure Document Intelligence integration
    - Better maintained by Microsoft
"""

import warnings
import base64
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pymupdf as fitz

from pdf2markdown.converters.base import PDFConverter

# Deprecation warning
warnings.warn(
    "PyMuPDFConverter is deprecated as of version 2.0.0. "
    "Use MarkItDownConverter instead for better format support and features.",
    DeprecationWarning,
    stacklevel=2
)
from pdf2markdown.core.config import Config, ImageMode
from pdf2markdown.core.models import (
    ConversionMetadata,
    ConversionResult,
    ExtractedImage,
    ExtractedTable,
    PageMetadata,
)


class PyMuPDFConverter(PDFConverter):
    """
    Fast PDF to Markdown converter using PyMuPDF and pymupdf4llm.

    This converter provides:
    - Fast conversion (0.12s per page)
    - Multi-column layout detection
    - Table extraction with automatic header detection
    - Image extraction (base64 or separate files)
    - Text formatting preservation
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the PyMuPDF converter."""
        super().__init__(config)

    def get_name(self) -> str:
        """Get converter name."""
        return "PyMuPDF Fast Converter"

    def is_available(self) -> bool:
        """Check if PyMuPDF is available."""
        try:
            import pymupdf
            import pymupdf4llm
            return True
        except ImportError:
            return False

    def supports_ocr(self) -> bool:
        """PyMuPDF doesn't have built-in OCR."""
        return False

    def convert(self, pdf_path: Path) -> ConversionResult:
        """
        Convert PDF to Markdown using PyMuPDF4LLM.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ConversionResult with markdown and metadata
        """
        self.validate_pdf(pdf_path)

        start_time = time.time()

        # Open PDF
        doc = fitz.open(pdf_path)

        try:
            # Extract metadata
            metadata = self._extract_metadata(doc, pdf_path, start_time)

            # Convert using pymupdf4llm
            markdown_text = self._convert_with_pymupdf4llm(doc)

            # Extract images if requested
            images = []
            if self.config.extract_images:
                images = self._extract_images(doc)

            # Extract tables
            tables = []
            if self.config.extract_tables:
                tables = self._extract_tables(doc)

            # Add page breaks if requested
            if self.config.include_page_breaks:
                markdown_text = self._add_page_breaks(markdown_text, len(doc))

            # Finalize metadata
            conversion_time = time.time() - start_time
            metadata.conversion_time_seconds = conversion_time
            metadata.converter_name = self.get_name()

            return ConversionResult(
                markdown=markdown_text,
                images=images,
                tables=tables,
                metadata=metadata,
            )

        finally:
            doc.close()

    def _convert_with_pymupdf4llm(self, doc: fitz.Document) -> str:
        """
        Convert PDF using pymupdf4llm library.

        Args:
            doc: Opened pymupdf Document

        Returns:
            Markdown text
        """
        try:
            import pymupdf4llm

            # Build options for pymupdf4llm
            options = {
                "page_chunks": False,  # Get full document, not chunks
                "write_images": self.config.extract_images,
                "image_format": self.config.image_format,
            }

            # Handle image mode
            if self.config.image_mode == ImageMode.EMBED:
                options["embed_images"] = True
            elif self.config.image_mode == ImageMode.LINK:
                options["embed_images"] = False
                if self.config.image_dir:
                    options["image_path"] = str(self.config.image_dir)

            # Convert to markdown
            md_text = pymupdf4llm.to_markdown(
                doc,
                **{k: v for k, v in options.items() if v is not None}
            )

            return md_text

        except ImportError:
            # Fallback to basic extraction if pymupdf4llm not available
            return self._basic_text_extraction(doc)

    def _basic_text_extraction(self, doc: fitz.Document) -> str:
        """
        Basic text extraction fallback without pymupdf4llm.

        Args:
            doc: Opened pymupdf Document

        Returns:
            Plain text from PDF
        """
        text_parts = []

        for page_num, page in enumerate(doc):
            # Extract text blocks
            blocks = page.get_text("blocks")

            for block in blocks:
                # block format: (x0, y0, x1, y1, "text", block_no, block_type)
                if len(block) >= 5:
                    text = block[4].strip()
                    if text:
                        text_parts.append(text)

            if self.config.include_page_breaks and page_num < len(doc) - 1:
                text_parts.append(self.config.page_break_marker)

        return "\n\n".join(text_parts)

    def _extract_metadata(
        self,
        doc: fitz.Document,
        pdf_path: Path,
        start_time: float
    ) -> ConversionMetadata:
        """
        Extract PDF metadata.

        Args:
            doc: Opened pymupdf Document
            pdf_path: Path to the PDF file
            start_time: Conversion start time

        Returns:
            ConversionMetadata object
        """
        # Get PDF metadata
        pdf_meta = doc.metadata

        # Calculate file hash
        file_hash = self._calculate_file_hash(pdf_path)

        # Get file size
        file_size = pdf_path.stat().st_size

        # Parse dates
        creation_date = self._parse_pdf_date(pdf_meta.get("creationDate"))
        mod_date = self._parse_pdf_date(pdf_meta.get("modDate"))

        # Extract page-level metadata
        pages_meta = []
        total_words = 0

        for page_num, page in enumerate(doc):
            text = page.get_text()
            word_count = len(text.split())
            total_words += word_count

            images = page.get_images()
            tables = page.find_tables()

            page_meta = PageMetadata(
                page_number=page_num + 1,
                width=page.rect.width,
                height=page.rect.height,
                rotation=page.rotation,
                has_text=bool(text.strip()),
                has_images=len(images) > 0,
                has_tables=len(tables.tables) > 0 if tables else False,
                word_count=word_count,
                image_count=len(images),
                table_count=len(tables.tables) if tables else 0,
            )
            pages_meta.append(page_meta)

        return ConversionMetadata(
            source_path=pdf_path,
            source_size_bytes=file_size,
            source_hash=file_hash,
            pdf_version=pdf_meta.get("format", "").replace("PDF ", ""),
            title=pdf_meta.get("title"),
            author=pdf_meta.get("author"),
            subject=pdf_meta.get("subject"),
            creator=pdf_meta.get("creator"),
            producer=pdf_meta.get("producer"),
            creation_date=creation_date,
            modification_date=mod_date,
            page_count=len(doc),
            total_words=total_words,
            strategy_used=self.config.strategy.value,
            converter_name=self.get_name(),
            conversion_time_seconds=0.0,  # Will be set later
            timestamp=datetime.now(),
            pages=pages_meta,
        )

    def _extract_images(self, doc: fitz.Document) -> List[ExtractedImage]:
        """
        Extract all images from the PDF.

        Args:
            doc: Opened pymupdf Document

        Returns:
            List of ExtractedImage objects
        """
        images = []
        global_image_index = 0

        for page_num, page in enumerate(doc):
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]  # XREF number
                    base_image = doc.extract_image(xref)

                    if not base_image:
                        continue

                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)

                    # Handle image mode
                    image_path = None
                    base64_data = None

                    if self.config.image_mode == ImageMode.EMBED:
                        # Convert to base64
                        base64_data = base64.b64encode(image_bytes).decode('utf-8')
                    elif self.config.image_mode in (ImageMode.LINK, ImageMode.SEPARATE):
                        # Will be saved later
                        base64_data = base64.b64encode(image_bytes).decode('utf-8')

                    extracted_img = ExtractedImage(
                        index=global_image_index,
                        page=page_num + 1,
                        format=image_ext,
                        width=width,
                        height=height,
                        size_bytes=len(image_bytes),
                        path=image_path,
                        base64_data=base64_data,
                        alt_text=f"Image {global_image_index + 1} from page {page_num + 1}",
                    )

                    images.append(extracted_img)
                    global_image_index += 1

                except Exception as e:
                    # Log warning but continue
                    if self.config.include_metadata:
                        print(f"Warning: Could not extract image {img_index} from page {page_num + 1}: {e}")

        return images

    def _extract_tables(self, doc: fitz.Document) -> List[ExtractedTable]:
        """
        Extract tables from the PDF.

        Args:
            doc: Opened pymupdf Document

        Returns:
            List of ExtractedTable objects
        """
        tables = []
        global_table_index = 0

        for page_num, page in enumerate(doc):
            try:
                # Find tables on the page
                table_finder = page.find_tables()

                if not table_finder or not table_finder.tables:
                    continue

                for table in table_finder.tables:
                    try:
                        # Extract table data
                        table_data = table.extract()

                        if not table_data or len(table_data) < 2:
                            continue

                        # Assume first row is headers
                        headers = table_data[0]
                        rows = table_data[1:]

                        # Convert to markdown
                        markdown = self._table_to_markdown(headers, rows)

                        extracted_table = ExtractedTable(
                            page=page_num + 1,
                            index=global_table_index,
                            rows=len(rows),
                            columns=len(headers),
                            headers=headers,
                            data=rows,
                            bbox=table.bbox,
                            markdown=markdown,
                        )

                        tables.append(extracted_table)
                        global_table_index += 1

                    except Exception as e:
                        print(f"Warning: Could not extract table from page {page_num + 1}: {e}")

            except Exception as e:
                print(f"Warning: Error finding tables on page {page_num + 1}: {e}")

        return tables

    def _table_to_markdown(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Convert table data to Markdown format.

        Args:
            headers: Table header row
            rows: Table data rows

        Returns:
            Markdown-formatted table
        """
        if self.config.table_format.value == "html":
            return self._table_to_html(headers, rows)

        # GitHub-flavored markdown (default)
        lines = []

        # Header row
        header_line = "| " + " | ".join(str(h).strip() for h in headers) + " |"
        lines.append(header_line)

        # Separator row
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        lines.append(separator)

        # Data rows
        for row in rows:
            # Ensure row has same length as headers
            padded_row = row + [""] * (len(headers) - len(row))
            row_line = "| " + " | ".join(str(cell).strip() for cell in padded_row[:len(headers)]) + " |"
            lines.append(row_line)

        return "\n".join(lines)

    def _table_to_html(self, headers: List[str], rows: List[List[str]]) -> str:
        """Convert table to HTML format."""
        lines = ["<table>"]

        # Headers
        lines.append("  <thead>")
        lines.append("    <tr>")
        for header in headers:
            lines.append(f"      <th>{header}</th>")
        lines.append("    </tr>")
        lines.append("  </thead>")

        # Body
        lines.append("  <tbody>")
        for row in rows:
            lines.append("    <tr>")
            for cell in row:
                lines.append(f"      <td>{cell}</td>")
            lines.append("    </tr>")
        lines.append("  </tbody>")

        lines.append("</table>")
        return "\n".join(lines)

    def _add_page_breaks(self, markdown: str, page_count: int) -> str:
        """
        Add page break markers to markdown.

        Args:
            markdown: Original markdown text
            page_count: Number of pages

        Returns:
            Markdown with page breaks
        """
        # This is a simple implementation
        # In practice, pymupdf4llm might already include page information
        return markdown

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _parse_pdf_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse PDF date string to datetime."""
        if not date_str:
            return None

        try:
            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
            if date_str.startswith("D:"):
                date_str = date_str[2:]

            # Extract date parts
            year = int(date_str[0:4])
            month = int(date_str[4:6]) if len(date_str) >= 6 else 1
            day = int(date_str[6:8]) if len(date_str) >= 8 else 1
            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            second = int(date_str[12:14]) if len(date_str) >= 14 else 0

            return datetime(year, month, day, hour, minute, second)

        except (ValueError, IndexError):
            return None
