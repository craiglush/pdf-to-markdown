"""
HTML to Markdown converter using markdownify and BeautifulSoup.

.. deprecated:: 2.0.0
    This converter is deprecated in favor of MarkItDownConverter.
    Use MarkItDownConverter for better HTML support and unified multi-format conversion.
"""

import warnings
import base64
import logging
import re
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from PIL import Image as PILImage

# Deprecation warning
warnings.warn(
    "HTMLConverter is deprecated as of version 2.0.0. Use MarkItDownConverter instead.",
    DeprecationWarning,
    stacklevel=2
)

from pdf2markdown.converters.document_converter import DocumentConverter
from pdf2markdown.core.config import Config, ImageMode
from pdf2markdown.core.models import (
    ConversionMetadata,
    ConversionResult,
    ExtractedImage,
    ExtractedTable,
)

logger = logging.getLogger(__name__)


class HTMLConverter(DocumentConverter):
    """Convert HTML documents to Markdown.

    Uses markdownify for clean Markdown generation and BeautifulSoup for
    HTML preprocessing and image/link handling.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the HTML converter.

        Args:
            config: Conversion configuration
        """
        self.config = config or Config()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PDF2Markdown/1.0)'
        })

    def convert(self, file_path: Path) -> ConversionResult:
        """Convert an HTML file to Markdown.

        Args:
            file_path: Path to the HTML file

        Returns:
            ConversionResult with markdown, images, and metadata

        Raises:
            FileNotFoundError: If the HTML file doesn't exist
            ValueError: If the file is not valid HTML
        """
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {file_path}")

        logger.info(f"Converting HTML file: {file_path}")

        # Read HTML content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            with open(file_path, 'r', encoding='latin-1') as f:
                html_content = f.read()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract metadata
        metadata = self._extract_metadata(soup, file_path)

        # Preprocess HTML
        soup = self._preprocess_html(soup, file_path)

        # Extract images before conversion
        images = self._extract_images(soup, file_path)

        # Extract tables before conversion
        tables = self._extract_tables(soup)

        # Convert to Markdown
        markdown = self._convert_to_markdown(soup)

        # Post-process Markdown
        markdown = self._postprocess_markdown(markdown)

        logger.info(f"Conversion complete: {len(markdown)} chars, "
                   f"{len(images)} images, {len(tables)} tables")

        return ConversionResult(
            markdown=markdown,
            images=images,
            tables=tables,
            metadata=metadata,
        )

    def supports_ocr(self) -> bool:
        """HTML converter doesn't need OCR."""
        return False

    def get_name(self) -> str:
        """Get converter name."""
        return "HTML Converter"

    def is_available(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import markdownify  # noqa: F401
            import bs4  # noqa: F401
            return True
        except ImportError:
            return False

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.html', '.htm']

    def _extract_metadata(self, soup: BeautifulSoup, file_path: Path) -> ConversionMetadata:
        """Extract metadata from HTML document.

        Args:
            soup: Parsed HTML document
            file_path: Path to HTML file

        Returns:
            Conversion metadata
        """
        # Extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)

        # Extract meta tags
        meta_author = soup.find('meta', attrs={'name': 'author'})
        author = meta_author.get('content') if meta_author else None

        meta_description = soup.find('meta', attrs={'name': 'description'})
        subject = meta_description.get('content') if meta_description else None

        # Count pages (HTML doesn't have pages, use sections)
        page_count = len(soup.find_all(['section', 'article'])) or 1

        return ConversionMetadata(
            title=title,
            author=author,
            subject=subject,
            page_count=page_count,
            converter_name=self.get_name(),
        )

    def _preprocess_html(self, soup: BeautifulSoup, file_path: Path) -> BeautifulSoup:
        """Preprocess HTML before conversion.

        Args:
            soup: Parsed HTML document
            file_path: Path to HTML file (for resolving relative URLs)

        Returns:
            Preprocessed HTML
        """
        # Remove script and style tags
        for tag in soup.find_all(['script', 'style']):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, type(soup))):
            if hasattr(comment, 'extract'):
                comment.extract()

        # Handle base URL for relative links/images
        base_url = self.config.html_base_url
        if not base_url:
            # Try to get from <base> tag
            base_tag = soup.find('base', href=True)
            if base_tag:
                base_url = base_tag['href']
            else:
                # Use file path as base
                base_url = file_path.parent.as_uri()

        # Resolve relative URLs in links
        for link in soup.find_all('a', href=True):
            link['href'] = urljoin(base_url, link['href'])

        # Resolve relative URLs in images
        for img in soup.find_all('img', src=True):
            img['src'] = urljoin(base_url, img['src'])

        # Handle semantic HTML preservation
        if self.config.html_preserve_semantic:
            # Mark semantic tags for special handling
            for tag in soup.find_all(['article', 'section', 'aside', 'nav']):
                tag['data-semantic'] = tag.name

        return soup

    def _extract_images(
        self, soup: BeautifulSoup, file_path: Path
    ) -> List[ExtractedImage]:
        """Extract images from HTML.

        Args:
            soup: Parsed HTML document
            file_path: Path to HTML file

        Returns:
            List of extracted images
        """
        images = []
        img_tags = soup.find_all('img')

        for idx, img_tag in enumerate(img_tags):
            src = img_tag.get('src', '')
            if not src:
                continue

            try:
                # Download or read image
                if src.startswith(('http://', 'https://')):
                    if self.config.html_download_images:
                        image_data = self._download_image(src)
                        if not image_data:
                            continue
                    else:
                        # Keep as link
                        images.append(ExtractedImage(
                            name=f"external_image_{idx}",
                            data=b"",
                            width=0,
                            height=0,
                            page=0,
                            format="url",
                            alt_text=img_tag.get('alt', ''),
                            original_url=src,
                        ))
                        continue
                elif src.startswith('data:'):
                    # Data URI
                    image_data = self._decode_data_uri(src)
                else:
                    # Local file
                    image_path = file_path.parent / src
                    if not image_path.exists():
                        logger.warning(f"Image not found: {image_path}")
                        continue
                    with open(image_path, 'rb') as f:
                        image_data = f.read()

                # Get image dimensions
                try:
                    img = PILImage.open(BytesIO(image_data))
                    width, height = img.size
                    img_format = img.format or "unknown"
                except Exception as e:
                    logger.warning(f"Could not read image dimensions: {e}")
                    width, height = 0, 0
                    img_format = "unknown"

                # Determine image name
                parsed_url = urlparse(src)
                img_name = Path(parsed_url.path).name or f"image_{idx}"

                images.append(ExtractedImage(
                    name=img_name,
                    data=image_data,
                    width=width,
                    height=height,
                    page=0,
                    format=img_format.lower(),
                    alt_text=img_tag.get('alt', ''),
                    original_url=src if src.startswith('http') else None,
                ))

                # Update img tag based on image mode
                if self.config.image_mode == ImageMode.EMBED:
                    # Convert to base64 data URI
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    img_tag['src'] = f"data:image/{img_format.lower()};base64,{b64_data}"
                elif self.config.image_mode == ImageMode.LINK:
                    # Will be saved as separate file
                    output_dir = self.config.output_dir or file_path.parent
                    img_tag['src'] = str(output_dir / "images" / img_name)
                elif self.config.image_mode == ImageMode.SEPARATE:
                    # Remove from HTML
                    img_tag.decompose()

            except Exception as e:
                logger.error(f"Error processing image {src}: {e}")

        return images

    def _download_image(self, url: str) -> Optional[bytes]:
        """Download an image from a URL.

        Args:
            url: Image URL

        Returns:
            Image bytes or None if download failed
        """
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")
            return None

    def _decode_data_uri(self, data_uri: str) -> bytes:
        """Decode a data URI.

        Args:
            data_uri: Data URI string

        Returns:
            Decoded bytes
        """
        # Format: data:image/png;base64,iVBORw0KG...
        header, data = data_uri.split(',', 1)
        if 'base64' in header:
            return base64.b64decode(data)
        else:
            # URL encoded
            from urllib.parse import unquote
            return unquote(data).encode('utf-8')

    def _extract_tables(self, soup: BeautifulSoup) -> List[ExtractedTable]:
        """Extract tables from HTML.

        Args:
            soup: Parsed HTML document

        Returns:
            List of extracted tables
        """
        tables = []
        table_tags = soup.find_all('table')

        for idx, table_tag in enumerate(table_tags):
            try:
                # Convert table to markdown
                table_markdown = self._table_to_markdown(table_tag)

                # Extract caption
                caption_tag = table_tag.find('caption')
                caption = caption_tag.get_text(strip=True) if caption_tag else None

                # Count rows and columns
                rows = table_tag.find_all('tr')
                row_count = len(rows)
                col_count = 0
                if rows:
                    cols = rows[0].find_all(['th', 'td'])
                    col_count = len(cols)

                tables.append(ExtractedTable(
                    markdown=table_markdown,
                    page=0,
                    caption=caption,
                    row_count=row_count,
                    col_count=col_count,
                ))

            except Exception as e:
                logger.error(f"Error processing table {idx}: {e}")

        return tables

    def _table_to_markdown(self, table_tag: BeautifulSoup) -> str:
        """Convert an HTML table to Markdown format.

        Args:
            table_tag: HTML table tag

        Returns:
            Markdown table string
        """
        rows = []

        # Process rows
        for tr in table_tag.find_all('tr'):
            cells = []
            for cell in tr.find_all(['th', 'td']):
                # Get cell text and clean it
                text = cell.get_text(strip=True)
                # Escape pipe characters
                text = text.replace('|', '\\|')
                # Replace newlines with spaces
                text = ' '.join(text.split())
                cells.append(text)

            if cells:
                rows.append(cells)

        if not rows:
            return ""

        # Determine if first row is header
        has_header = bool(table_tag.find('thead')) or bool(table_tag.find('th'))

        # Build markdown table
        markdown_lines = []

        if has_header and rows:
            # Header row
            header = rows[0]
            markdown_lines.append('| ' + ' | '.join(header) + ' |')
            markdown_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
            rows = rows[1:]

        # Data rows
        for row in rows:
            # Pad row if necessary
            if markdown_lines and len(row) < len(rows[0]):
                row += [''] * (len(rows[0]) - len(row))
            markdown_lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(markdown_lines)

    def _convert_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert HTML to Markdown.

        Args:
            soup: Preprocessed HTML document

        Returns:
            Markdown string
        """
        # Use markdownify with custom settings
        markdown = md(
            str(soup),
            heading_style="ATX",  # Use # for headings
            bullets="-",  # Use - for bullet lists
            code_language="",  # Preserve code language
            strip=['script', 'style'],  # Strip these tags
            convert=['table'],  # Convert tables
        )

        return markdown

    def _postprocess_markdown(self, markdown: str) -> str:
        """Post-process generated Markdown.

        Args:
            markdown: Raw markdown string

        Returns:
            Cleaned markdown string
        """
        # Remove excessive blank lines (more than 2 consecutive)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Clean up spacing around headings
        markdown = re.sub(r'\n(#{1,6} .+)\n', r'\n\n\1\n\n', markdown)

        # Ensure proper spacing around code blocks
        markdown = re.sub(r'```(\w+)?\n', r'\n```\1\n', markdown)
        markdown = re.sub(r'\n```\n', r'\n```\n\n', markdown)

        # Clean up list formatting
        markdown = re.sub(r'\n([\*\-\+] .+)\n', r'\n\1\n', markdown)

        # Remove leading/trailing whitespace
        markdown = markdown.strip()

        return markdown
