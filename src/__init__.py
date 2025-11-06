"""
PDF to Markdown Converter
~~~~~~~~~~~~~~~~~~~~~~~~~

A high-fidelity PDF to Markdown converter with support for:
- Complex tables with merged cells
- Image extraction and embedding
- Multi-column layouts
- OCR for scanned PDFs
- Multiple output formats

Example usage:
    >>> from pdf2markdown import convert_pdf
    >>> markdown = convert_pdf("document.pdf", strategy="auto")
    >>> print(markdown)

"""

__version__ = "0.1.0"
__author__ = "PDF2MD Team"
__license__ = "MIT"

from pdf2markdown.core.orchestrator import ConversionOrchestrator
from pdf2markdown.converters.pymupdf_converter import PyMuPDFConverter

# Convenience function for simple conversions
def convert_pdf(
    pdf_path: str,
    output_path: str | None = None,
    strategy: str = "auto",
    **kwargs
) -> str:
    """
    Convert a PDF file to Markdown.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Optional path to save the output Markdown
        strategy: Conversion strategy ('auto', 'fast', 'accurate', 'ocr')
        **kwargs: Additional conversion options

    Returns:
        The generated Markdown content as a string
    """
    orchestrator = ConversionOrchestrator()
    result = orchestrator.convert(pdf_path, strategy=strategy, **kwargs)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.markdown)

    return result.markdown


__all__ = [
    "convert_pdf",
    "ConversionOrchestrator",
    "PyMuPDFConverter",
]
