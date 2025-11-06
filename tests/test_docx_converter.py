"""Tests for DOCX to Markdown converter."""

import io
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

import pytest

from pdf2markdown.converters.docx_converter import DOCXConverter
from pdf2markdown.core.config import Config


@pytest.fixture
def docx_converter():
    """Create a DOCX converter instance."""
    config = Config(
        docx_include_comments=False,
        docx_include_headers_footers=False,
    )
    return DOCXConverter(config=config)


@pytest.fixture
def mock_docx_document():
    """Create a mock python-docx Document."""
    mock_doc = Mock()
    mock_doc.core_properties = Mock()
    mock_doc.core_properties.title = "Test Document"
    mock_doc.core_properties.author = "Test Author"
    mock_doc.core_properties.subject = "Test Subject"
    mock_doc.paragraphs = [Mock() for _ in range(50)]  # 50 paragraphs
    return mock_doc


class TestDOCXConverter:
    """Test suite for DOCXConverter."""

    def test_converter_name(self, docx_converter):
        """Test converter name."""
        assert docx_converter.get_name() == "DOCX Converter"

    def test_supported_extensions(self, docx_converter):
        """Test supported file extensions."""
        extensions = docx_converter.get_supported_extensions()
        assert '.docx' in extensions

    def test_no_ocr_support(self, docx_converter):
        """Test that DOCX converter doesn't support OCR."""
        assert not docx_converter.supports_ocr()

    def test_availability_check(self):
        """Test availability depends on pypandoc or mammoth."""
        with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc', return_value=True):
            with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth', return_value=False):
                converter = DOCXConverter()
                assert converter.is_available()

        with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc', return_value=False):
            with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth', return_value=True):
                converter = DOCXConverter()
                assert converter.is_available()

        with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc', return_value=False):
            with patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth', return_value=False):
                converter = DOCXConverter()
                assert not converter.is_available()

    def test_file_not_found(self, docx_converter):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            docx_converter.convert(Path("/nonexistent/file.docx"))

    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc')
    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth')
    def test_convert_with_pypandoc(self, mock_check_mammoth, mock_check_pypandoc, tmp_path):
        """Test conversion using pypandoc."""
        # Setup
        mock_check_pypandoc.return_value = True
        mock_check_mammoth.return_value = False

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake docx content")

        converter = DOCXConverter()

        # Mock pypandoc conversion
        with patch('pdf2markdown.converters.docx_converter.pypandoc') as mock_pypandoc:
            mock_pypandoc.convert_file.return_value = "# Test Heading\n\nTest content"

            # Mock metadata extraction
            with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
                mock_doc = Mock()
                mock_doc.core_properties = Mock()
                mock_doc.core_properties.title = "Test"
                mock_doc.core_properties.author = "Author"
                mock_doc.core_properties.subject = None
                mock_doc.paragraphs = [Mock()] * 25
                mock_doc.part.rels.values.return_value = []
                mock_docx.Document.return_value = mock_doc

                result = converter.convert(docx_file)

                # Assertions
                assert result.markdown is not None
                assert "Test Heading" in result.markdown
                assert result.metadata.title == "Test"
                assert result.metadata.author == "Author"
                assert "pypandoc" in result.metadata.converter_name.lower()

    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc')
    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth')
    def test_convert_with_mammoth_fallback(self, mock_check_mammoth, mock_check_pypandoc, tmp_path):
        """Test conversion falling back to mammoth when pypandoc fails."""
        # Setup
        mock_check_pypandoc.return_value = True
        mock_check_mammoth.return_value = True

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake docx content")

        converter = DOCXConverter()

        # Mock pypandoc to fail
        with patch('pdf2markdown.converters.docx_converter.pypandoc') as mock_pypandoc:
            mock_pypandoc.convert_file.side_effect = Exception("pypandoc failed")

            # Mock mammoth conversion
            with patch('pdf2markdown.converters.docx_converter.mammoth') as mock_mammoth:
                mock_result = Mock()
                mock_result.value = "# Mammoth Heading\n\nMammoth content"
                mock_result.messages = []
                mock_mammoth.convert_to_markdown.return_value = mock_result

                # Mock metadata extraction
                with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
                    mock_doc = Mock()
                    mock_doc.core_properties = Mock()
                    mock_doc.core_properties.title = "Test"
                    mock_doc.core_properties.author = None
                    mock_doc.core_properties.subject = None
                    mock_doc.paragraphs = [Mock()] * 25
                    mock_doc.part.rels.values.return_value = []
                    mock_docx.Document.return_value = mock_doc

                    result = converter.convert(docx_file)

                    # Assertions
                    assert result.markdown is not None
                    assert "Mammoth Heading" in result.markdown
                    assert "mammoth" in result.metadata.converter_name.lower()

    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_pypandoc')
    @patch('pdf2markdown.converters.docx_converter.DOCXConverter._check_mammoth')
    def test_convert_failure_both_methods(self, mock_check_mammoth, mock_check_pypandoc, tmp_path):
        """Test conversion failure when both methods fail."""
        # Setup
        mock_check_pypandoc.return_value = True
        mock_check_mammoth.return_value = True

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake docx content")

        converter = DOCXConverter()

        # Mock both to fail
        with patch('pdf2markdown.converters.docx_converter.pypandoc') as mock_pypandoc:
            mock_pypandoc.convert_file.side_effect = Exception("pypandoc failed")

            with patch('pdf2markdown.converters.docx_converter.mammoth') as mock_mammoth:
                mock_mammoth.convert_to_markdown.side_effect = Exception("mammoth failed")

                # Mock metadata extraction
                with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
                    mock_doc = Mock()
                    mock_doc.core_properties = Mock()
                    mock_doc.core_properties.title = None
                    mock_doc.core_properties.author = None
                    mock_doc.core_properties.subject = None
                    mock_doc.paragraphs = []
                    mock_doc.part.rels.values.return_value = []
                    mock_docx.Document.return_value = mock_doc

                    with pytest.raises(ValueError, match="DOCX conversion failed"):
                        converter.convert(docx_file)

    def test_metadata_extraction(self, docx_converter, tmp_path):
        """Test metadata extraction from DOCX."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
            mock_doc = Mock()
            mock_doc.core_properties = Mock()
            mock_doc.core_properties.title = "My Document"
            mock_doc.core_properties.author = "John Doe"
            mock_doc.core_properties.subject = "Test Subject"
            mock_doc.paragraphs = [Mock()] * 50  # 50 paragraphs = ~2 pages
            mock_docx.Document.return_value = mock_doc

            metadata = docx_converter._extract_metadata(docx_file)

            assert metadata.title == "My Document"
            assert metadata.author == "John Doe"
            assert metadata.subject == "Test Subject"
            assert metadata.page_count == 2  # 50 paragraphs / 25 per page

    def test_metadata_extraction_without_python_docx(self, docx_converter, tmp_path):
        """Test metadata extraction when python-docx is not available."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.docx', side_effect=ImportError):
            metadata = docx_converter._extract_metadata(docx_file)

            # Should return default metadata
            assert metadata.title is None
            assert metadata.author is None
            assert metadata.subject is None
            assert metadata.page_count == 1

    def test_image_extraction(self, docx_converter, tmp_path):
        """Test image extraction from DOCX."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        # Create fake image data
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
            # Mock document with image relationship
            mock_doc = Mock()
            mock_rel = Mock()
            mock_rel.target_ref = "word/media/image1.png"
            mock_rel.target_part = Mock()
            mock_rel.target_part.blob = img_data

            mock_doc.part.rels.values.return_value = [mock_rel]
            mock_docx.Document.return_value = mock_doc

            images = docx_converter._extract_images(docx_file)

            assert len(images) == 1
            assert images[0].name == "image1.png"
            assert images[0].width == 100
            assert images[0].height == 100
            assert images[0].format == "png"

    def test_image_extraction_without_python_docx(self, docx_converter, tmp_path):
        """Test image extraction when python-docx is not available."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.docx', side_effect=ImportError):
            images = docx_converter._extract_images(docx_file)

            # Should return empty list
            assert len(images) == 0

    def test_table_extraction(self, docx_converter):
        """Test table extraction from markdown."""
        markdown = """
# Document

Some text before table.

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

Some text after table.

| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |

End of document.
"""

        tables = docx_converter._extract_tables(markdown)

        assert len(tables) == 2
        assert tables[0].col_count == 3
        assert tables[1].col_count == 2

    def test_postprocess_markdown(self, docx_converter):
        """Test markdown post-processing."""
        markdown = """


# Heading



Some text


- List item


"""

        result = docx_converter._postprocess_markdown(markdown)

        # Should clean up excessive blank lines
        assert '\n\n\n' not in result
        # Should trim whitespace
        assert not result.startswith('\n')
        assert not result.endswith('\n\n')

    def test_pypandoc_with_comments(self, tmp_path):
        """Test pypandoc conversion with comments enabled."""
        config = Config(docx_include_comments=True)
        converter = DOCXConverter(config=config)

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.pypandoc') as mock_pypandoc:
            mock_pypandoc.convert_file.return_value = "# Test"

            converter._convert_with_pypandoc(docx_file)

            # Check that --track-changes was added to extra_args
            call_args = mock_pypandoc.convert_file.call_args
            assert '--track-changes=all' in call_args[1]['extra_args']

    def test_mammoth_style_map(self, docx_converter, tmp_path):
        """Test mammoth conversion uses correct style map."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.mammoth') as mock_mammoth:
            with patch('builtins.open', mock_open(read_data=b"fake")):
                mock_result = Mock()
                mock_result.value = "# Heading"
                mock_result.messages = []
                mock_mammoth.convert_to_markdown.return_value = mock_result

                markdown = docx_converter._convert_with_mammoth(docx_file)

                # Verify style_map was used
                call_args = mock_mammoth.convert_to_markdown.call_args
                assert 'style_map' in call_args[1]
                assert 'Heading 1' in call_args[1]['style_map']

    def test_mammoth_with_messages(self, docx_converter, tmp_path):
        """Test mammoth conversion handles messages."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.mammoth') as mock_mammoth:
            with patch('builtins.open', mock_open(read_data=b"fake")):
                mock_result = Mock()
                mock_result.value = "# Heading"
                mock_result.messages = ["Warning: Style not found"]
                mock_mammoth.convert_to_markdown.return_value = mock_result

                # Should not raise, just log
                markdown = docx_converter._convert_with_mammoth(docx_file)
                assert markdown == "# Heading"

    def test_complex_table_extraction(self, docx_converter):
        """Test extraction of complex markdown tables."""
        markdown = """
| Col1 | Col2 | Col3 |
|:-----|:----:|-----:|
| Left | Center | Right |
| A | B | C |
"""

        tables = docx_converter._extract_tables(markdown)

        assert len(tables) == 1
        assert tables[0].row_count == 2  # Excludes separator line
        assert tables[0].col_count == 3

    def test_empty_document_handling(self, docx_converter, tmp_path):
        """Test handling of empty DOCX document."""
        docx_file = tmp_path / "empty.docx"
        docx_file.write_bytes(b"fake content")

        with patch('pdf2markdown.converters.docx_converter.pypandoc') as mock_pypandoc:
            mock_pypandoc.convert_file.return_value = ""

            with patch('pdf2markdown.converters.docx_converter.docx') as mock_docx:
                mock_doc = Mock()
                mock_doc.core_properties = Mock()
                mock_doc.core_properties.title = None
                mock_doc.core_properties.author = None
                mock_doc.core_properties.subject = None
                mock_doc.paragraphs = []
                mock_doc.part.rels.values.return_value = []
                mock_docx.Document.return_value = mock_doc

                converter = DOCXConverter()
                converter._pypandoc_available = True
                converter._mammoth_available = False

                result = converter.convert(docx_file)

                # Should handle empty document gracefully
                assert result.markdown == ""
                assert result.metadata.page_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
