"""Streamlit web interface for PDF to Markdown conversion."""

import base64
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

from pdf2markdown import __version__
from pdf2markdown.core.config import Config, ConversionStrategy, ImageMode, TableFormat
from pdf2markdown.core.models import ConversionResult
from pdf2markdown.core.orchestrator import ConversionOrchestrator

# Page configuration
st.set_page_config(
    page_title="Document to Markdown Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)


def main() -> None:
    """Main Streamlit application."""

    # Header
    st.title("📄 Document to Markdown Converter")
    st.markdown(f"*High-fidelity document to Markdown conversion v{__version__}*")
    st.markdown("**Supported formats:** PDF, HTML, DOCX, XLSX")
    st.markdown("---")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        strategy = st.selectbox(
            "Conversion Strategy",
            options=[s.value for s in ConversionStrategy],
            index=0,
            help="Auto: Automatically detect best strategy\n"
                 "Fast: PyMuPDF (fastest)\n"
                 "OCR: For scanned PDFs\n"
                 "Accurate: AI-powered (if available)",
        )

        st.subheader("Image Options")
        extract_images = st.checkbox("Extract Images", value=True)

        image_mode = st.radio(
            "Image Mode",
            options=[m.value for m in ImageMode],
            index=0,
            help="Embed: Base64 in markdown\n"
                 "Link: Save separately\n"
                 "Separate: Extract but don't link",
        )

        st.subheader("Table Options")
        extract_tables = st.checkbox("Extract Tables", value=True)

        table_format = st.selectbox(
            "Table Format",
            options=[f.value for f in TableFormat],
            index=0,
        )

        st.subheader("Advanced Options")
        ocr_enabled = st.checkbox("Force OCR", value=False)

        ocr_language = st.text_input(
            "OCR Language",
            value="eng",
            help="Tesseract language code (e.g., 'eng', 'fra', 'eng+fra')",
        )

        page_breaks = st.checkbox("Include Page Breaks (PDF only)", value=False)

        st.subheader("HTML Options")
        html_download_images = st.checkbox(
            "Download External Images",
            value=True,
            help="Download external images from HTML (otherwise keep as links)"
        )

        html_base_url = st.text_input(
            "Base URL",
            value="",
            help="Base URL for resolving relative links in HTML",
            placeholder="https://example.com"
        )

        st.subheader("DOCX Options")
        docx_include_comments = st.checkbox(
            "Include Comments",
            value=False,
            help="Include comments and tracked changes in DOCX conversion"
        )

        docx_include_headers_footers = st.checkbox(
            "Include Headers/Footers",
            value=False,
            help="Include headers and footers from DOCX"
        )

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "Convert documents to Markdown with support for:\n"
            "- **PDF:** Complex tables, images, OCR for scanned PDFs\n"
            "- **HTML:** External images, relative links, semantic tags\n"
            "- **DOCX:** Formatting, tables, images (pypandoc or mammoth)\n"
            "- **XLSX:** Spreadsheets, charts (coming in Phase 4)"
        )

    # Main content area
    uploaded_file = st.file_uploader(
        "Choose a document file",
        type=["pdf", "html", "htm", "docx", "xlsx"],
        help="Upload a document file to convert to Markdown (PDF, HTML, DOCX, XLSX)",
    )

    if uploaded_file is not None:
        # Display file info
        file_ext = Path(uploaded_file.name).suffix.upper().lstrip('.')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Type", file_ext)

        # Convert button
        if st.button("🚀 Convert to Markdown", type="primary"):
            with st.spinner(f"Converting {file_ext} to Markdown..."):
                result = convert_document(
                    uploaded_file,
                    strategy=strategy,
                    image_mode=image_mode,
                    extract_images=extract_images,
                    extract_tables=extract_tables,
                    table_format=table_format,
                    ocr_enabled=ocr_enabled,
                    ocr_language=ocr_language,
                    page_breaks=page_breaks,
                    html_download_images=html_download_images,
                    html_base_url=html_base_url or None,
                    docx_include_comments=docx_include_comments,
                    docx_include_headers_footers=docx_include_headers_footers,
                )

                if result:
                    st.session_state['result'] = result
                    st.success("✅ Conversion completed successfully!")

    # Display results if available
    if 'result' in st.session_state:
        result: ConversionResult = st.session_state['result']

        st.markdown("---")
        st.header("📊 Results")

        # Summary metrics
        if result.metadata:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Pages", result.metadata.page_count)
            with col2:
                st.metric("Words", f"{result.metadata.total_words:,}")
            with col3:
                st.metric("Images", result.metadata.total_images)
            with col4:
                st.metric("Tables", result.metadata.total_tables)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Conversion Time", f"{result.metadata.conversion_time_seconds:.2f}s")
            with col2:
                st.metric("Strategy", result.metadata.strategy_used)

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Markdown", "👁️ Preview", "🖼️ Images", "📋 Metadata"])

        with tab1:
            st.subheader("Markdown Output")

            # Code editor
            st.code(result.markdown, language="markdown", line_numbers=True)

            # Download button
            st.download_button(
                label="📥 Download Markdown",
                data=result.markdown,
                file_name="converted.md",
                mime="text/markdown",
            )

        with tab2:
            st.subheader("Preview")
            st.markdown(result.markdown, unsafe_allow_html=True)

        with tab3:
            st.subheader("Extracted Images")

            if result.images:
                cols = st.columns(3)
                for idx, img in enumerate(result.images):
                    with cols[idx % 3]:
                        if img.base64_data:
                            # Display image
                            img_data = base64.b64decode(img.base64_data)
                            st.image(img_data, caption=img.alt_text, use_container_width=True)

                            # Image info
                            st.caption(
                                f"📄 Page {img.page} | "
                                f"📐 {img.width}x{img.height} | "
                                f"💾 {img.size_bytes / 1024:.1f} KB"
                            )
            else:
                st.info("No images extracted from this document")

        with tab4:
            st.subheader("Conversion Metadata")

            if result.metadata:
                # Document info
                st.write("**Document Information**")
                doc_info = {
                    "Title": result.metadata.title or "N/A",
                    "Author": result.metadata.author or "N/A",
                    "Pages": result.metadata.page_count,
                    "PDF Version": result.metadata.pdf_version or "N/A",
                    "Creator": result.metadata.creator or "N/A",
                }
                st.json(doc_info)

                # Conversion info
                st.write("**Conversion Details**")
                conversion_info = {
                    "Converter": result.metadata.converter_name,
                    "Strategy": result.metadata.strategy_used,
                    "Time": f"{result.metadata.conversion_time_seconds:.2f}s",
                    "Timestamp": result.metadata.timestamp.isoformat(),
                }
                st.json(conversion_info)

                # Warnings/Errors
                if result.metadata.warnings:
                    st.warning("**Warnings:**")
                    for warning in result.metadata.warnings:
                        st.write(f"- {warning}")

                if result.metadata.errors:
                    st.error("**Errors:**")
                    for error in result.metadata.errors:
                        st.write(f"- {error}")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        f"Document to Markdown Converter v{__version__} | "
        "Built with Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


def convert_document(
    uploaded_file,
    strategy: str,
    image_mode: str,
    extract_images: bool,
    extract_tables: bool,
    table_format: str,
    ocr_enabled: bool,
    ocr_language: str,
    page_breaks: bool,
    html_download_images: bool,
    html_base_url: Optional[str],
    docx_include_comments: bool,
    docx_include_headers_footers: bool,
) -> Optional[ConversionResult]:
    """
    Convert uploaded document file.

    Args:
        uploaded_file: Streamlit UploadedFile object
        strategy: Conversion strategy
        image_mode: Image extraction mode
        extract_images: Whether to extract images
        extract_tables: Whether to extract tables
        table_format: Table format
        ocr_enabled: Enable OCR
        ocr_language: OCR language code
        page_breaks: Include page breaks
        html_download_images: Download external images from HTML
        html_base_url: Base URL for resolving relative links in HTML
        docx_include_comments: Include comments and tracked changes in DOCX
        docx_include_headers_footers: Include headers and footers from DOCX

    Returns:
        ConversionResult or None if error
    """
    try:
        # Determine file extension
        file_ext = Path(uploaded_file.name).suffix.lower()

        # Save uploaded file to temporary location with appropriate suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)

        # Create configuration
        config = Config(
            strategy=ConversionStrategy(strategy),
            image_mode=ImageMode(image_mode),
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=TableFormat(table_format),
            ocr_enabled=ocr_enabled,
            ocr_language=ocr_language,
            include_page_breaks=page_breaks,
            html_download_images=html_download_images,
            html_base_url=html_base_url,
            docx_include_comments=docx_include_comments,
            docx_include_headers_footers=docx_include_headers_footers,
        )

        # Convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(tmp_path)

        # Clean up temp file
        tmp_path.unlink()

        return result

    except Exception as e:
        st.error(f"❌ Conversion failed: {e}")
        return None


if __name__ == "__main__":
    main()
