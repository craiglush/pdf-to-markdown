"""
Base converter classes - Backward compatibility module.

This module maintains backward compatibility by re-exporting the PDF converter classes.
New code should import from pdf_converter.py directly.

Deprecated: This module is kept for backward compatibility only.
"""

# Re-export for backward compatibility
from pdf2markdown.converters.pdf_converter import PDFConverter

__all__ = ["PDFConverter"]
