"""
Advanced usage examples for PDF to Markdown converter.

This script demonstrates various features and use cases.
"""

from pathlib import Path
from pdf2markdown import convert_pdf
from pdf2markdown.core.config import Config, ConversionStrategy, ImageMode, TableFormat
from pdf2markdown.core.orchestrator import ConversionOrchestrator


def example_1_simple_conversion():
    """Example 1: Simple one-line conversion"""
    print("\n=== Example 1: Simple Conversion ===")

    markdown = convert_pdf(
        "sample.pdf",
        output_path="output1.md",
    )

    print(f"Converted to Markdown: {len(markdown)} characters")


def example_2_custom_config():
    """Example 2: Conversion with custom configuration"""
    print("\n=== Example 2: Custom Configuration ===")

    # Create custom configuration
    config = Config(
        strategy=ConversionStrategy.FAST,
        image_mode=ImageMode.LINK,
        extract_images=True,
        extract_tables=True,
        table_format=TableFormat.GITHUB,
        preserve_formatting=True,
        include_page_breaks=True,
        page_break_marker="<!-- PAGE BREAK -->",
    )

    # Convert with custom config
    orchestrator = ConversionOrchestrator(config)
    result = orchestrator.convert("sample.pdf")

    # Access results
    print(f"Pages: {result.metadata.page_count}")
    print(f"Words: {result.metadata.total_words}")
    print(f"Images: {len(result.images)}")
    print(f"Tables: {len(result.tables)}")

    # Save results
    result.save("output2.md", save_images=True)
    print(f"Saved to: output2.md")


def example_3_ocr_conversion():
    """Example 3: OCR for scanned PDFs"""
    print("\n=== Example 3: OCR Conversion ===")

    config = Config(
        strategy=ConversionStrategy.OCR,
        ocr_enabled=True,
        ocr_language="eng",  # or "eng+fra" for multiple languages
        ocr_dpi=300,  # Higher DPI = better quality, slower
    )

    orchestrator = ConversionOrchestrator(config)
    result = orchestrator.convert("scanned.pdf")

    print(f"OCR completed in {result.metadata.conversion_time_seconds:.2f}s")
    print(result.get_summary())


def example_4_batch_processing():
    """Example 4: Batch process multiple PDFs"""
    print("\n=== Example 4: Batch Processing ===")

    pdf_dir = Path("pdfs")
    output_dir = Path("markdown")
    output_dir.mkdir(exist_ok=True)

    orchestrator = ConversionOrchestrator()

    # Process all PDFs
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs to process")

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")

        try:
            result = orchestrator.convert(pdf_file)
            output_path = output_dir / f"{pdf_file.stem}.md"
            result.save(output_path)

            print(f"✓ Saved: {output_path}")
            print(f"  Pages: {result.metadata.page_count}")
            print(f"  Time: {result.metadata.conversion_time_seconds:.2f}s")

        except Exception as e:
            print(f"✗ Error: {e}")


def example_5_image_extraction():
    """Example 5: Extract images to separate files"""
    print("\n=== Example 5: Image Extraction ===")

    config = Config(
        extract_images=True,
        image_mode=ImageMode.LINK,
        image_dir=Path("extracted_images"),
        image_format="png",
        max_image_width=1920,  # Resize large images
    )

    orchestrator = ConversionOrchestrator(config)
    result = orchestrator.convert("document.pdf")

    print(f"Extracted {len(result.images)} images")

    for img in result.images:
        print(f"  - Image {img.index}: {img.width}x{img.height} ({img.format})")
        if img.path:
            print(f"    Saved to: {img.path}")


def example_6_table_extraction():
    """Example 6: Focus on table extraction"""
    print("\n=== Example 6: Table Extraction ===")

    config = Config(
        extract_tables=True,
        table_format=TableFormat.GITHUB,
    )

    orchestrator = ConversionOrchestrator(config)
    result = orchestrator.convert("document.pdf")

    print(f"Found {len(result.tables)} tables")

    for table in result.tables:
        print(f"\n--- Table {table.index} (Page {table.page}) ---")
        print(f"Size: {table.rows} rows × {table.columns} columns")
        print(f"Headers: {', '.join(table.headers)}")
        print("\nMarkdown:")
        print(table.markdown[:200] + "..." if len(table.markdown) > 200 else table.markdown)


def example_7_quality_check():
    """Example 7: Quality validation and warnings"""
    print("\n=== Example 7: Quality Validation ===")

    config = Config(
        validate_output=True,
        min_confidence=0.7,
    )

    orchestrator = ConversionOrchestrator(config)
    result = orchestrator.convert("document.pdf")

    # Check metadata for warnings
    if result.metadata.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.metadata.warnings:
            print(f"  - {warning}")

    if result.metadata.errors:
        print("\n❌ Errors:")
        for error in result.metadata.errors:
            print(f"  - {error}")

    # Check confidence score
    if result.metadata.confidence_score:
        print(f"\nConfidence Score: {result.metadata.confidence_score:.2%}")


def example_8_programmatic_access():
    """Example 8: Access conversion results programmatically"""
    print("\n=== Example 8: Programmatic Access ===")

    result = convert_pdf("sample.pdf")

    # Get markdown as string
    markdown_text = result.markdown

    # Get page-level information
    for page_meta in result.metadata.pages:
        print(f"\nPage {page_meta.page_number}:")
        print(f"  Size: {page_meta.width}x{page_meta.height}")
        print(f"  Words: {page_meta.word_count}")
        print(f"  Images: {page_meta.image_count}")
        print(f"  Tables: {page_meta.table_count}")

    # Get document metadata
    meta = result.metadata
    print(f"\nDocument Info:")
    print(f"  Title: {meta.title}")
    print(f"  Author: {meta.author}")
    print(f"  Created: {meta.creation_date}")
    print(f"  Pages: {meta.page_count}")

    # Convert to dictionary for JSON export
    result_dict = result.to_dict()
    print(f"\nResult as dict: {len(result_dict)} keys")


def example_9_auto_strategy():
    """Example 9: Automatic strategy selection"""
    print("\n=== Example 9: Auto Strategy ===")

    # Let the orchestrator choose the best strategy
    config = Config(strategy=ConversionStrategy.AUTO)
    orchestrator = ConversionOrchestrator(config)

    # Convert different types of PDFs
    pdfs = [
        ("text_document.pdf", "Regular PDF with text"),
        ("scanned_document.pdf", "Scanned PDF without text layer"),
    ]

    for pdf_file, description in pdfs:
        print(f"\n{description}: {pdf_file}")

        try:
            result = orchestrator.convert(pdf_file)
            print(f"  Strategy used: {result.metadata.strategy_used}")
            print(f"  Converter: {result.metadata.converter_name}")
            print(f"  Time: {result.metadata.conversion_time_seconds:.2f}s")
        except FileNotFoundError:
            print(f"  (File not found - example only)")


def example_10_error_handling():
    """Example 10: Proper error handling"""
    print("\n=== Example 10: Error Handling ===")

    orchestrator = ConversionOrchestrator()

    try:
        result = orchestrator.convert("nonexistent.pdf")

    except FileNotFoundError as e:
        print(f"File not found: {e}")

    except ValueError as e:
        print(f"Invalid file: {e}")

    except Exception as e:
        print(f"Conversion error: {e}")
        print("Check that all dependencies are installed:")
        print("  - PyMuPDF")
        print("  - pytesseract (for OCR)")
        print("  - poppler-utils (for pdf2image)")


if __name__ == "__main__":
    print("PDF to Markdown Converter - Advanced Examples")
    print("=" * 50)

    # Run examples (comment out those that require actual PDF files)
    # example_1_simple_conversion()
    # example_2_custom_config()
    # example_3_ocr_conversion()
    # example_4_batch_processing()
    # example_5_image_extraction()
    # example_6_table_extraction()
    # example_7_quality_check()
    # example_8_programmatic_access()
    # example_9_auto_strategy()
    example_10_error_handling()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run these examples:")
    print("1. Uncomment the example functions above")
    print("2. Provide sample PDF files")
    print("3. Run: python examples/advanced_usage.py")
