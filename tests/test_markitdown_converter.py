"""
Tests for MarkItDown converter (v2.0 primary converter).

Tests basic functionality without requiring external dependencies like OpenAI API.
For full integration tests with LLM and Azure features, see test_markitdown_integration.py.
"""

import tempfile
from pathlib import Path

import pytest

from pdf2markdown.converters.markitdown_converter import (
    MARKITDOWN_AVAILABLE,
    MarkItDownConverter,
)
from pdf2markdown.core.config import Config, ImageMode, TableFormat
from pdf2markdown.core.models import ConversionResult


# Skip all tests if MarkItDown not available
pytestmark = pytest.mark.skipif(
    not MARKITDOWN_AVAILABLE, reason="MarkItDown library not installed"
)


class TestMarkItDownConverter:
    """Tests for MarkItDownConverter."""

    def test_converter_initialization(self):
        """Test basic converter initialization."""
        config = Config()
        converter = MarkItDownConverter(config)

        assert converter is not None
        assert converter.is_available()
        assert converter.get_name() == "MarkItDown Converter (Microsoft)"

    def test_supported_extensions(self):
        """Test that converter reports all supported extensions."""
        converter = MarkItDownConverter()
        extensions = converter.get_supported_extensions()

        # Core document formats
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".xlsx" in extensions
        assert ".pptx" in extensions

        # Web formats
        assert ".html" in extensions
        assert ".xml" in extensions
        assert ".json" in extensions

        # Image formats
        assert ".jpg" in extensions
        assert ".png" in extensions

        # Audio formats
        assert ".wav" in extensions
        assert ".mp3" in extensions

        # Other formats
        assert ".epub" in extensions
        assert ".zip" in extensions
        assert ".csv" in extensions

    def test_supports_ocr(self):
        """Test that converter supports OCR for images."""
        converter = MarkItDownConverter()
        assert converter.supports_ocr() is True

    def test_simple_text_file_conversion(self):
        """Test conversion of a simple text file."""
        converter = MarkItDownConverter()

        # Create temporary text file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write("# Test Document\n\nThis is a test.")
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert isinstance(result, ConversionResult)
            assert result.markdown is not None
            assert "Test Document" in result.markdown or "test" in result.markdown.lower()
            assert result.metadata is not None
            assert result.metadata.converter_name == "MarkItDown Converter (Microsoft)"

        finally:
            tmp_path.unlink()

    def test_html_file_conversion(self):
        """Test conversion of HTML file."""
        converter = MarkItDownConverter()

        html_content = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <p>This is a <strong>test</strong> paragraph.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as tmp_file:
            tmp_file.write(html_content)
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert isinstance(result, ConversionResult)
            assert "Hello World" in result.markdown
            assert result.metadata.total_words > 0

        finally:
            tmp_path.unlink()

    def test_json_file_conversion(self):
        """Test conversion of JSON file."""
        converter = MarkItDownConverter()

        json_content = '{"name": "Test", "value": 123, "items": ["a", "b", "c"]}'

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            tmp_file.write(json_content)
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert isinstance(result, ConversionResult)
            assert result.markdown is not None
            # JSON should be formatted in markdown
            assert "Test" in result.markdown or "name" in result.markdown

        finally:
            tmp_path.unlink()

    def test_xml_file_conversion(self):
        """Test conversion of XML file."""
        converter = MarkItDownConverter()

        xml_content = """<?xml version="1.0"?>
        <root>
            <item name="Test">Value</item>
        </root>
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as tmp_file:
            tmp_file.write(xml_content)
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert isinstance(result, ConversionResult)
            assert result.markdown is not None

        finally:
            tmp_path.unlink()

    def test_csv_file_conversion(self):
        """Test conversion of CSV file to markdown table."""
        converter = MarkItDownConverter()

        csv_content = """Name,Age,City
John,30,New York
Jane,25,San Francisco
Bob,35,Chicago
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert isinstance(result, ConversionResult)
            assert result.markdown is not None
            # CSV should be converted to table format
            assert "Name" in result.markdown
            assert "John" in result.markdown or "jane" in result.markdown.lower()

        finally:
            tmp_path.unlink()

    def test_image_mode_configuration(self):
        """Test that image mode is properly configured."""
        config = Config(image_mode=ImageMode.EMBED)
        converter = MarkItDownConverter(config)

        assert converter.config.image_mode == ImageMode.EMBED

        config = Config(image_mode=ImageMode.LINK)
        converter = MarkItDownConverter(config)

        assert converter.config.image_mode == ImageMode.LINK

    def test_table_format_configuration(self):
        """Test that table format is properly configured."""
        config = Config(table_format=TableFormat.GITHUB)
        converter = MarkItDownConverter(config)

        assert converter.config.table_format == TableFormat.GITHUB

    def test_conversion_metadata(self):
        """Test that conversion metadata is properly populated."""
        converter = MarkItDownConverter()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write("Test content for metadata")
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            assert result.metadata is not None
            assert result.metadata.converter_name == "MarkItDown Converter (Microsoft)"
            assert result.metadata.source_file == str(tmp_path)
            assert result.metadata.source_size_bytes > 0
            assert result.metadata.conversion_time_seconds >= 0
            assert result.metadata.total_words > 0
            assert result.metadata.timestamp is not None

        finally:
            tmp_path.unlink()

    def test_file_not_found_error(self):
        """Test that converter raises FileNotFoundError for missing files."""
        converter = MarkItDownConverter()

        with pytest.raises(FileNotFoundError):
            converter.convert(Path("/nonexistent/file.pdf"))

    def test_invalid_file_error(self):
        """Test that converter handles invalid files gracefully."""
        converter = MarkItDownConverter()

        # Create a file with invalid content for the extension
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            tmp_file.write("This is not valid JSON content {{{")
            tmp_path = Path(tmp_file.name)

        try:
            # Should not crash, but may produce error in metadata
            result = converter.convert(tmp_path)
            assert result is not None

        finally:
            tmp_path.unlink()

    def test_rich_conversion_disabled_by_default(self):
        """Test that rich conversion is disabled by default."""
        config = Config()
        assert config.rich_conversion is False

        converter = MarkItDownConverter(config)
        assert converter.config.rich_conversion is False

    def test_llm_features_disabled_by_default(self):
        """Test that LLM features are disabled by default."""
        config = Config()
        assert config.llm_enabled is False
        assert config.llm_model == "gpt-4o"

        converter = MarkItDownConverter(config)
        assert converter.config.llm_enabled is False

    def test_azure_features_disabled_by_default(self):
        """Test that Azure features are disabled by default."""
        config = Config()
        assert config.azure_enabled is False

        converter = MarkItDownConverter(config)
        assert converter.config.azure_enabled is False

    def test_conversion_result_structure(self):
        """Test that conversion result has expected structure."""
        converter = MarkItDownConverter()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write("Test")
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)

            # Check result structure
            assert hasattr(result, "markdown")
            assert hasattr(result, "images")
            assert hasattr(result, "tables")
            assert hasattr(result, "metadata")

            # Check types
            assert isinstance(result.markdown, str)
            assert isinstance(result.images, list)
            assert isinstance(result.tables, list)

        finally:
            tmp_path.unlink()


class TestMarkItDownConverterAdvanced:
    """Advanced tests for MarkItDownConverter (may require additional dependencies)."""

    def test_estimate_conversion_time(self):
        """Test conversion time estimation."""
        converter = MarkItDownConverter()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write("Test" * 1000)
            tmp_path = Path(tmp_file.name)

        try:
            estimated_time = converter.estimate_conversion_time(tmp_path)
            assert estimated_time > 0
            assert estimated_time < 60  # Should be reasonable

        finally:
            tmp_path.unlink()

    def test_get_summary(self):
        """Test conversion result summary."""
        converter = MarkItDownConverter()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write("Test content")
            tmp_path = Path(tmp_file.name)

        try:
            result = converter.convert(tmp_path)
            summary = result.get_summary()

            assert isinstance(summary, dict)
            assert "markdown_length" in summary
            assert "num_images" in summary
            assert "num_tables" in summary

        finally:
            tmp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
