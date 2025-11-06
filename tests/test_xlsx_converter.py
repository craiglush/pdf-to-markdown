"""Tests for XLSX converter."""

import base64
import io
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from pdf2markdown.converters.xlsx_converter import XLSXConverter
from pdf2markdown.core.config import Config, ImageMode, TableFormat


@pytest.fixture
def xlsx_converter():
    """Create XLSX converter instance."""
    config = Config()
    return XLSXConverter(config)


@pytest.fixture
def sample_xlsx_file(tmp_path):
    """Create a temporary XLSX file path."""
    xlsx_file = tmp_path / "test.xlsx"
    xlsx_file.touch()
    return xlsx_file


class TestXLSXConverterBasics:
    """Test basic XLSX converter functionality."""

    def test_converter_initialization(self):
        """Test converter initializes correctly."""
        converter = XLSXConverter()
        assert converter.config is not None
        assert isinstance(converter, XLSXConverter)

    def test_converter_with_custom_config(self):
        """Test converter with custom configuration."""
        config = Config(
            xlsx_mode="separate",
            xlsx_extract_charts=True,
            xlsx_show_formulas=True,
        )
        converter = XLSXConverter(config)
        assert converter.config.xlsx_mode == "separate"
        assert converter.config.xlsx_extract_charts is True

    def test_get_name(self, xlsx_converter):
        """Test converter name."""
        assert "XLSX" in xlsx_converter.get_name()
        assert "pandas" in xlsx_converter.get_name()

    def test_supports_ocr(self, xlsx_converter):
        """Test OCR support flag."""
        assert xlsx_converter.supports_ocr() is False

    def test_get_supported_extensions(self, xlsx_converter):
        """Test supported file extensions."""
        extensions = xlsx_converter.get_supported_extensions()
        assert '.xlsx' in extensions
        assert '.xls' in extensions
        assert '.xlsm' in extensions

    @patch('pdf2markdown.converters.xlsx_converter.PANDAS_AVAILABLE', True)
    @patch('pdf2markdown.converters.xlsx_converter.OPENPYXL_AVAILABLE', True)
    def test_is_available_when_deps_installed(self, xlsx_converter):
        """Test availability check when dependencies are installed."""
        xlsx_converter._pandas_available = True
        xlsx_converter._openpyxl_available = True
        assert xlsx_converter.is_available() is True

    @patch('pdf2markdown.converters.xlsx_converter.PANDAS_AVAILABLE', False)
    def test_is_available_when_pandas_missing(self, xlsx_converter):
        """Test availability check when pandas is missing."""
        xlsx_converter._pandas_available = False
        assert xlsx_converter.is_available() is False

    @patch('pdf2markdown.converters.xlsx_converter.OPENPYXL_AVAILABLE', False)
    def test_is_available_when_openpyxl_missing(self, xlsx_converter):
        """Test availability check when openpyxl is missing."""
        xlsx_converter._openpyxl_available = False
        assert xlsx_converter.is_available() is False


class TestXLSXConversion:
    """Test XLSX conversion functionality."""

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_convert_single_sheet(self, mock_load_workbook, mock_read_excel, xlsx_converter, sample_xlsx_file):
        """Test conversion of single-sheet XLSX."""
        # Create mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'City': ['New York', 'London', 'Tokyo']
        })

        mock_read_excel.return_value = df

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_props = Mock()
        mock_props.title = "Test Workbook"
        mock_props.creator = "Test Author"
        mock_props.created = None
        mock_props.modified = None
        mock_props.subject = None
        mock_props.keywords = None
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        # Convert
        result = xlsx_converter.convert(sample_xlsx_file)

        # Assertions
        assert result is not None
        assert "Alice" in result.markdown
        assert "Bob" in result.markdown
        assert result.metadata.converter_name == xlsx_converter.get_name()
        assert result.metadata.page_count == 1
        assert len(result.tables) > 0

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_convert_multiple_sheets_combined(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test conversion of multiple sheets in combined mode."""
        import pandas as pd

        # Create mock DataFrames for multiple sheets
        df1 = pd.DataFrame({'Col1': [1, 2], 'Col2': [3, 4]})
        df2 = pd.DataFrame({'ColA': ['A', 'B'], 'ColB': ['C', 'D']})

        mock_read_excel.return_value = {
            'Sheet1': df1,
            'Sheet2': df2
        }

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_props = Mock()
        mock_props.title = "Multi Sheet"
        mock_props.creator = None
        mock_props.created = None
        mock_props.modified = None
        mock_props.subject = None
        mock_props.keywords = None
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        mock_load_workbook.return_value = mock_wb

        # Configure for combined mode
        config = Config(xlsx_mode="combined")
        converter = XLSXConverter(config)

        # Convert
        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert "Sheet1" in result.markdown
        assert "Sheet2" in result.markdown
        assert "2 sheet(s)" in result.markdown
        assert len(result.tables) == 2

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_convert_multiple_sheets_separate(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test conversion of multiple sheets in separate mode."""
        import pandas as pd

        df1 = pd.DataFrame({'Col1': [1, 2]})
        df2 = pd.DataFrame({'ColA': ['A', 'B']})

        mock_read_excel.return_value = {
            'Sheet1': df1,
            'Sheet2': df2
        }

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_props = Mock()
        mock_props.title = None
        mock_props.creator = None
        mock_props.created = None
        mock_props.modified = None
        mock_props.subject = None
        mock_props.keywords = None
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        mock_load_workbook.return_value = mock_wb

        # Configure for separate mode
        config = Config(xlsx_mode="separate")
        converter = XLSXConverter(config)

        # Convert
        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert "# Sheet1" in result.markdown
        assert "# Sheet2" in result.markdown

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_convert_selected_sheets(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test conversion of selected sheets only."""
        import pandas as pd

        df1 = pd.DataFrame({'Col1': [1, 2]})

        mock_read_excel.return_value = {'Sheet1': df1}

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_props = Mock()
        mock_props.title = None
        mock_props.creator = None
        mock_props.created = None
        mock_props.modified = None
        mock_props.subject = None
        mock_props.keywords = None
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        # Configure for selected mode
        config = Config(xlsx_mode="selected", xlsx_sheets=['Sheet1'])
        converter = XLSXConverter(config)

        # Convert
        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert "Sheet1" in result.markdown
        mock_read_excel.assert_called_once()

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_convert_empty_sheet(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test conversion of empty sheet."""
        import pandas as pd

        # Empty DataFrame
        df = pd.DataFrame()
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_props = Mock()
        mock_props.title = None
        mock_props.creator = None
        mock_props.created = None
        mock_props.modified = None
        mock_props.subject = None
        mock_props.keywords = None
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        config = Config(xlsx_mode="combined")
        converter = XLSXConverter(config)

        # Convert
        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert "Empty sheet" in result.markdown


class TestXLSXTableFormatting:
    """Test table formatting options."""

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_table_format_github(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test GitHub table format."""
        import pandas as pd

        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        config = Config(table_format=TableFormat.GITHUB)
        converter = XLSXConverter(config)

        result = converter.convert(sample_xlsx_file)

        # GitHub format uses pipes and dashes
        assert '|' in result.markdown

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_table_format_html(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test HTML table format."""
        import pandas as pd

        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        config = Config(table_format=TableFormat.HTML)
        converter = XLSXConverter(config)

        result = converter.convert(sample_xlsx_file)

        # HTML format uses <table> tags
        assert '<table' in result.markdown

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_wide_table_truncation(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test wide table gets truncated."""
        import pandas as pd

        # Create DataFrame with many columns
        data = {f'Col{i}': [i] for i in range(150)}
        df = pd.DataFrame(data)
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock openpyxl workbook
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        config = Config(xlsx_max_sheet_width=100)
        converter = XLSXConverter(config)

        result = converter.convert(sample_xlsx_file)

        # Should indicate table was truncated
        assert "too wide" in result.markdown.lower()


class TestXLSXImageExtraction:
    """Test image and chart extraction."""

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    @patch('pdf2markdown.converters.xlsx_converter.PILImage.open')
    def test_extract_embedded_images(self, mock_pil_open, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test extraction of embedded images."""
        import pandas as pd

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock image
        mock_img_ref = Mock()
        mock_img_ref.getvalue.return_value = b'fake_image_data'

        mock_image = Mock()
        mock_image.ref = mock_img_ref

        # Mock sheet with images
        mock_sheet = Mock()
        mock_sheet._images = [mock_image]

        # Mock workbook
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_wb.__getitem__ = lambda self, key: mock_sheet
        mock_load_workbook.return_value = mock_wb

        # Mock PIL Image
        mock_pil_img = Mock()
        mock_pil_img.size = (100, 100)
        mock_pil_img.format = 'PNG'
        mock_pil_open.return_value = mock_pil_img

        config = Config(extract_images=True, xlsx_extract_charts=False)
        converter = XLSXConverter(config)
        converter._pil_available = True

        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert len(result.images) > 0
        assert result.images[0].width == 100
        assert result.images[0].height == 100

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_extract_charts(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test extraction of charts."""
        import pandas as pd

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock chart
        mock_title = Mock()
        mock_title.text = "Test Chart"
        mock_chart = Mock()
        mock_chart.title = mock_title

        # Mock sheet with charts
        mock_sheet = Mock()
        mock_sheet._charts = [mock_chart]

        # Mock workbook
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_wb.__getitem__ = lambda self, key: mock_sheet
        mock_load_workbook.return_value = mock_wb

        config = Config(xlsx_extract_charts=True)
        converter = XLSXConverter(config)

        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert len(result.images) > 0
        assert "Test Chart" in result.images[0].alt_text

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_image_embedding_modes(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test different image embedding modes."""
        import pandas as pd

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock image
        mock_img_ref = Mock()
        mock_img_ref.getvalue.return_value = b'test_data'

        mock_image = Mock()
        mock_image.ref = mock_img_ref

        mock_sheet = Mock()
        mock_sheet._images = [mock_image]

        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_wb.__getitem__ = lambda self, key: mock_sheet
        mock_load_workbook.return_value = mock_wb

        # Test embed mode
        config = Config(image_mode=ImageMode.EMBED)
        converter = XLSXConverter(config)
        converter._pil_available = True

        with patch('pdf2markdown.converters.xlsx_converter.PILImage.open') as mock_pil:
            mock_pil_img = Mock()
            mock_pil_img.size = (100, 100)
            mock_pil_img.format = 'PNG'
            mock_pil.return_value = mock_pil_img

            result = converter.convert(sample_xlsx_file)

        # Should have base64 data
        assert result.images[0].base64_data is not None
        assert "data:image" in result.markdown


class TestXLSXMetadata:
    """Test metadata extraction."""

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_metadata_extraction(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test metadata extraction from XLSX."""
        import pandas as pd
        from datetime import datetime

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock workbook properties
        mock_props = Mock()
        mock_props.title = "Test Workbook"
        mock_props.creator = "Test Author"
        mock_props.subject = "Test Subject"
        mock_props.keywords = "test, keywords"
        mock_props.created = datetime(2024, 1, 1)
        mock_props.modified = datetime(2024, 1, 2)

        mock_wb = Mock()
        mock_wb.properties = mock_props
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        mock_load_workbook.return_value = mock_wb

        converter = XLSXConverter()

        result = converter.convert(sample_xlsx_file)

        # Assertions
        assert result.metadata.title == "Test Workbook"
        assert result.metadata.author == "Test Author"
        assert result.metadata.subject == "Test Subject"
        assert result.metadata.keywords == "test, keywords"
        assert result.metadata.page_count == 2

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_metadata_without_properties(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test metadata extraction when properties are missing."""
        import pandas as pd

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock workbook without properties
        mock_wb = Mock()
        mock_wb.properties = None
        mock_wb.sheetnames = ['Sheet1']
        mock_load_workbook.return_value = mock_wb

        converter = XLSXConverter()

        result = converter.convert(sample_xlsx_file)

        # Should still work with default metadata
        assert result.metadata is not None
        assert result.metadata.title == sample_xlsx_file.stem


class TestXLSXErrorHandling:
    """Test error handling."""

    def test_convert_nonexistent_file(self, xlsx_converter):
        """Test conversion of non-existent file."""
        with pytest.raises(FileNotFoundError):
            xlsx_converter.convert(Path("/nonexistent/file.xlsx"))

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    def test_convert_invalid_xlsx(self, mock_read_excel, xlsx_converter, sample_xlsx_file):
        """Test conversion of invalid XLSX file."""
        mock_read_excel.side_effect = Exception("Invalid XLSX")

        with pytest.raises(ValueError, match="Failed to read XLSX"):
            xlsx_converter.convert(sample_xlsx_file)

    @patch('pdf2markdown.converters.xlsx_converter.pd.read_excel')
    @patch('pdf2markdown.converters.xlsx_converter.openpyxl.load_workbook')
    def test_metadata_extraction_error(self, mock_load_workbook, mock_read_excel, sample_xlsx_file):
        """Test handling of metadata extraction errors."""
        import pandas as pd

        df = pd.DataFrame({'A': [1]})
        mock_read_excel.return_value = {'Sheet1': df}

        # Mock workbook that raises error
        mock_load_workbook.side_effect = Exception("Metadata error")

        converter = XLSXConverter()

        # Should still complete conversion despite metadata error
        result = converter.convert(sample_xlsx_file)

        assert result is not None
        assert len(result.metadata.warnings) > 0


class TestXLSXEstimation:
    """Test conversion time estimation."""

    def test_estimate_conversion_time(self, xlsx_converter, sample_xlsx_file):
        """Test conversion time estimation."""
        # Create a file with known size
        sample_xlsx_file.write_bytes(b'x' * (1024 * 1024 * 2))  # 2MB

        time_estimate = xlsx_converter.estimate_conversion_time(sample_xlsx_file)

        assert time_estimate > 0
        assert time_estimate >= 1.0  # At least 1 second
