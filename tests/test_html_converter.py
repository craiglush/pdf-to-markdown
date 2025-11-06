"""Tests for HTML to Markdown converter."""

import base64
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pdf2markdown.converters.html_converter import HTMLConverter
from pdf2markdown.core.config import Config, ImageMode


@pytest.fixture
def html_converter():
    """Create an HTML converter instance."""
    config = Config(
        image_mode=ImageMode.LINK,
        html_download_images=False,
        html_preserve_semantic=False,
    )
    return HTMLConverter(config=config)


@pytest.fixture
def sample_html(tmp_path):
    """Create a sample HTML file for testing."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <meta name="author" content="Test Author">
    <meta name="description" content="A test HTML document">
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a <strong>test</strong> paragraph with <em>formatting</em>.</p>

    <h2>Section 1</h2>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>

    <h2>Section 2</h2>
    <table>
        <thead>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
                <th>Column 3</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Row 1, Col 1</td>
                <td>Row 1, Col 2</td>
                <td>Row 1, Col 3</td>
            </tr>
            <tr>
                <td>Row 2, Col 1</td>
                <td>Row 2, Col 2</td>
                <td>Row 2, Col 3</td>
            </tr>
        </tbody>
    </table>

    <h2>Code Example</h2>
    <pre><code class="language-python">
def hello():
    print("Hello, World!")
    </code></pre>

    <p>Link to <a href="https://example.com">external site</a>.</p>
</body>
</html>"""

    html_file = tmp_path / "test.html"
    html_file.write_text(html_content, encoding='utf-8')
    return html_file


@pytest.fixture
def html_with_images(tmp_path):
    """Create HTML file with various image types."""
    # Create a small test image
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_path = tmp_path / "test_image.png"
    img.save(img_path)

    # Create base64 encoded image
    from io import BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    data_uri = f"data:image/png;base64,{b64_data}"

    html_content = f"""<!DOCTYPE html>
<html>
<head><title>Images Test</title></head>
<body>
    <h1>Images</h1>
    <img src="test_image.png" alt="Local image">
    <img src="{data_uri}" alt="Data URI image">
    <img src="https://example.com/image.jpg" alt="External image">
</body>
</html>"""

    html_file = tmp_path / "images.html"
    html_file.write_text(html_content, encoding='utf-8')
    return html_file


@pytest.fixture
def html_with_tables(tmp_path):
    """Create HTML file with complex tables."""
    html_content = """<!DOCTYPE html>
<html>
<head><title>Tables Test</title></head>
<body>
    <h1>Tables</h1>

    <table>
        <caption>Simple Table</caption>
        <tr>
            <th>Name</th>
            <th>Age</th>
            <th>City</th>
        </tr>
        <tr>
            <td>Alice</td>
            <td>30</td>
            <td>New York</td>
        </tr>
        <tr>
            <td>Bob</td>
            <td>25</td>
            <td>London</td>
        </tr>
    </table>

    <table>
        <tr>
            <td>No header</td>
            <td>table</td>
        </tr>
        <tr>
            <td>Data 1</td>
            <td>Data 2</td>
        </tr>
    </table>
</body>
</html>"""

    html_file = tmp_path / "tables.html"
    html_file.write_text(html_content, encoding='utf-8')
    return html_file


class TestHTMLConverter:
    """Test suite for HTMLConverter."""

    def test_converter_available(self, html_converter):
        """Test that converter is available with dependencies installed."""
        assert html_converter.is_available()

    def test_converter_name(self, html_converter):
        """Test converter name."""
        assert html_converter.get_name() == "HTML Converter"

    def test_supported_extensions(self, html_converter):
        """Test supported file extensions."""
        extensions = html_converter.get_supported_extensions()
        assert '.html' in extensions
        assert '.htm' in extensions

    def test_no_ocr_support(self, html_converter):
        """Test that HTML converter doesn't support OCR."""
        assert not html_converter.supports_ocr()

    def test_basic_conversion(self, html_converter, sample_html):
        """Test basic HTML to Markdown conversion."""
        result = html_converter.convert(sample_html)

        # Check result structure
        assert result.markdown is not None
        assert isinstance(result.markdown, str)
        assert len(result.markdown) > 0

        # Check that headings are converted
        assert '# Main Heading' in result.markdown
        assert '## Section 1' in result.markdown

        # Check that formatting is preserved
        assert '**test**' in result.markdown or '*test*' in result.markdown

        # Check that lists are converted
        assert '- Item 1' in result.markdown or '* Item 1' in result.markdown

    def test_metadata_extraction(self, html_converter, sample_html):
        """Test metadata extraction from HTML."""
        result = html_converter.convert(sample_html)
        metadata = result.metadata

        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert metadata.subject == "A test HTML document"
        assert metadata.converter_name == "HTML Converter"

    def test_table_extraction(self, html_converter, html_with_tables):
        """Test table extraction from HTML."""
        result = html_converter.convert(html_with_tables)

        # Should extract 2 tables
        assert len(result.tables) == 2

        # Check first table
        table1 = result.tables[0]
        assert table1.caption == "Simple Table"
        assert table1.row_count == 3  # Header + 2 data rows
        assert table1.col_count == 3
        assert 'Name' in table1.markdown
        assert 'Alice' in table1.markdown

        # Check second table (no header)
        table2 = result.tables[1]
        assert table2.caption is None
        assert table2.row_count == 2

    def test_image_extraction_local(self, html_converter, html_with_images):
        """Test extraction of local images."""
        result = html_converter.convert(html_with_images)

        # Should find at least the local image
        assert len(result.images) > 0

        # Check local image
        local_img = next((img for img in result.images if 'test_image' in img.name), None)
        assert local_img is not None
        assert local_img.width == 100
        assert local_img.height == 100
        assert local_img.alt_text == "Local image"

    def test_image_extraction_data_uri(self, html_converter, html_with_images):
        """Test extraction of data URI images."""
        result = html_converter.convert(html_with_images)

        # Should find data URI image
        data_uri_img = next((img for img in result.images if img.alt_text == "Data URI image"), None)
        assert data_uri_img is not None
        assert len(img.data) > 0

    def test_image_mode_embed(self, sample_html, tmp_path):
        """Test image embedding mode."""
        # Create HTML with local image
        img_path = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (50, 50), color='blue')
        img.save(img_path)

        html_file = tmp_path / "embed_test.html"
        html_file.write_text(
            '<html><body><img src="test.png"></body></html>',
            encoding='utf-8'
        )

        config = Config(image_mode=ImageMode.EMBED)
        converter = HTMLConverter(config=config)
        result = converter.convert(html_file)

        # Markdown should contain base64 data URI
        assert 'data:image/' in result.markdown

    def test_image_mode_separate(self, html_with_images):
        """Test separate image mode (extract but don't link)."""
        config = Config(image_mode=ImageMode.SEPARATE)
        converter = HTMLConverter(config=config)
        result = converter.convert(html_with_images)

        # Images should be extracted
        assert len(result.images) > 0

        # But not embedded in markdown
        # (checking exact markdown is tricky, just verify conversion worked)
        assert len(result.markdown) > 0

    def test_link_resolution(self, tmp_path):
        """Test that relative links are resolved."""
        html_content = """<html><body>
            <a href="page1.html">Page 1</a>
            <a href="/absolute/path.html">Absolute</a>
            <a href="https://example.com">External</a>
        </body></html>"""

        html_file = tmp_path / "links.html"
        html_file.write_text(html_content, encoding='utf-8')

        converter = HTMLConverter()
        result = converter.convert(html_file)

        # Links should be present in markdown
        assert 'https://example.com' in result.markdown

    def test_code_block_preservation(self, html_converter, sample_html):
        """Test that code blocks are preserved."""
        result = html_converter.convert(sample_html)

        # Should contain code block
        assert '```' in result.markdown
        assert 'def hello()' in result.markdown

    def test_malformed_html_handling(self, html_converter, tmp_path):
        """Test handling of malformed HTML."""
        malformed_html = """<html>
            <body>
                <p>Unclosed paragraph
                <div>Unclosed div
                <strong>Unclosed strong
            </body>
        """

        html_file = tmp_path / "malformed.html"
        html_file.write_text(malformed_html, encoding='utf-8')

        # Should not raise exception (BeautifulSoup handles it)
        result = html_converter.convert(html_file)
        assert result.markdown is not None

    def test_empty_html(self, html_converter, tmp_path):
        """Test conversion of empty HTML."""
        html_file = tmp_path / "empty.html"
        html_file.write_text("<html><body></body></html>", encoding='utf-8')

        result = html_converter.convert(html_file)
        assert result.markdown is not None
        # May be empty or whitespace only
        assert isinstance(result.markdown, str)

    def test_file_not_found(self, html_converter):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            html_converter.convert(Path("/nonexistent/file.html"))

    def test_unicode_content(self, html_converter, tmp_path):
        """Test handling of Unicode content."""
        html_content = """<html><body>
            <h1>Unicode Test</h1>
            <p>Chinese: 你好世界</p>
            <p>Arabic: مرحبا بالعالم</p>
            <p>Emoji: 🎉 🚀 ✨</p>
        </body></html>"""

        html_file = tmp_path / "unicode.html"
        html_file.write_text(html_content, encoding='utf-8')

        result = html_converter.convert(html_file)
        assert '你好世界' in result.markdown
        assert 'مرحبا بالعالم' in result.markdown
        assert '🎉' in result.markdown

    def test_base_url_configuration(self, tmp_path):
        """Test base URL configuration for link resolution."""
        html_content = """<html><body>
            <img src="image.png">
            <a href="page.html">Link</a>
        </body></html>"""

        html_file = tmp_path / "base_url_test.html"
        html_file.write_text(html_content, encoding='utf-8')

        config = Config(html_base_url="https://example.com/docs/")
        converter = HTMLConverter(config=config)
        result = converter.convert(html_file)

        # Links should be resolved relative to base URL
        assert len(result.markdown) > 0

    def test_semantic_preservation(self, tmp_path):
        """Test semantic HTML preservation option."""
        html_content = """<html><body>
            <article>
                <h1>Article Title</h1>
                <p>Article content</p>
            </article>
            <aside>
                <p>Sidebar content</p>
            </aside>
        </body></html>"""

        html_file = tmp_path / "semantic.html"
        html_file.write_text(html_content, encoding='utf-8')

        config = Config(html_preserve_semantic=True)
        converter = HTMLConverter(config=config)
        result = converter.convert(html_file)

        # Should convert successfully
        assert result.markdown is not None
        assert 'Article Title' in result.markdown

    @patch('requests.Session.get')
    def test_external_image_download(self, mock_get, tmp_path):
        """Test downloading external images."""
        # Mock response with image data
        from PIL import Image
        from io import BytesIO

        img = Image.new('RGB', (100, 100), color='green')
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        mock_response = Mock()
        mock_response.content = buffer.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        html_content = """<html><body>
            <img src="https://example.com/test.png" alt="External">
        </body></html>"""

        html_file = tmp_path / "external_img.html"
        html_file.write_text(html_content, encoding='utf-8')

        config = Config(html_download_images=True)
        converter = HTMLConverter(config=config)
        result = converter.convert(html_file)

        # Should have downloaded and extracted the image
        assert len(result.images) > 0
        external_img = result.images[0]
        assert external_img.original_url == "https://example.com/test.png"
        assert len(external_img.data) > 0

    def test_table_with_pipes(self, html_converter, tmp_path):
        """Test table cells containing pipe characters."""
        html_content = """<html><body>
            <table>
                <tr>
                    <td>Column | with | pipes</td>
                    <td>Normal column</td>
                </tr>
            </table>
        </body></html>"""

        html_file = tmp_path / "pipes.html"
        html_file.write_text(html_content, encoding='utf-8')

        result = html_converter.convert(html_file)

        # Pipes should be escaped
        assert len(result.tables) > 0
        assert '\\|' in result.tables[0].markdown

    def test_nested_lists(self, html_converter, tmp_path):
        """Test conversion of nested lists."""
        html_content = """<html><body>
            <ul>
                <li>Item 1
                    <ul>
                        <li>Nested 1.1</li>
                        <li>Nested 1.2</li>
                    </ul>
                </li>
                <li>Item 2</li>
            </ul>
        </body></html>"""

        html_file = tmp_path / "nested_lists.html"
        html_file.write_text(html_content, encoding='utf-8')

        result = html_converter.convert(html_file)

        # Should contain nested structure
        assert 'Item 1' in result.markdown
        assert 'Nested 1.1' in result.markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
