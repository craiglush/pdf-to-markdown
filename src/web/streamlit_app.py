"""
Streamlit Web UI for Multi-Format Document to Markdown Converter (v2.0).

Powered by Microsoft MarkItDown - supports 13+ file formats including:
PDF, DOCX, XLSX, PPTX, HTML, Images (with OCR), Audio (with transcription),
YouTube videos, EPub books, and more.
"""

import base64
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import streamlit as st

from pdf2markdown import __version__
from pdf2markdown.core.config import (
    Config,
    ConversionStrategy,
    ImageMode,
    TableFormat,
)
from pdf2markdown.core.models import ConversionResult
from pdf2markdown.core.orchestrator import ConversionOrchestrator

# Page configuration
st.set_page_config(
    page_title="Document to Markdown Converter v2.0",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown(
    """
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
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .format-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def main() -> None:
    """Main Streamlit application."""

    # Header
    st.title("📄 Multi-Format Document to Markdown Converter")
    st.markdown(
        f"*Powered by Microsoft MarkItDown v{__version__} - "
        f"Convert 13+ file formats to Markdown*"
    )

    # Render sidebar configuration once (prevents duplicate widget IDs)
    config_dict = render_sidebar_config()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📤 Upload & Convert",
            "📚 Formats Gallery",
            "⚡ Batch Processing",
            "🔑 API Settings",
        ]
    )

    # Tab 1: Upload & Convert
    with tab1:
        render_upload_tab(config_dict)

    # Tab 2: Formats Gallery
    with tab2:
        render_formats_gallery()

    # Tab 3: Batch Processing
    with tab3:
        render_batch_processing(config_dict)

    # Tab 4: API Settings
    with tab4:
        render_api_settings()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        f"Multi-Format Document to Markdown Converter v{__version__} | "
        "Powered by Microsoft MarkItDown | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_config() -> dict:
    """Render sidebar configuration and return config dictionary."""

    with st.sidebar:
        st.header("⚙️ Configuration")

        # Converter Selection
        st.subheader("🔄 Conversion Engine")
        use_markitdown = st.checkbox(
            "Use MarkItDown (v2.0)",
            value=True,
            key="sidebar_use_markitdown",
            help="Use Microsoft MarkItDown for all formats (recommended). "
            "Disable to use legacy converters.",
        )

        if use_markitdown:
            st.info("✅ Using MarkItDown - supports 13+ formats")
        else:
            st.warning("⚠️ Using legacy converters (deprecated)")

        # Strategy Selection
        st.subheader("📋 Strategy")
        strategy = st.selectbox(
            "Conversion Strategy",
            options=[s.value for s in ConversionStrategy],
            index=0,
            help="markitdown: Microsoft MarkItDown (default)\n"
            "auto: Automatically detect best converter\n"
            "fast: PyMuPDF (PDF only, deprecated)\n"
            "ocr: Tesseract OCR (PDF only, deprecated)",
        )

        # MarkItDown Advanced Features
        if use_markitdown:
            st.subheader("🤖 AI Features (Optional)")

            llm_enabled = st.checkbox(
                "AI Image Descriptions",
                value=False,
                key="sidebar_llm_enabled",
                help="Use OpenAI GPT-4 to generate detailed image descriptions",
            )

            if llm_enabled:
                llm_model = st.selectbox(
                    "LLM Model",
                    options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                    index=0,
                )

                llm_prompt = st.text_area(
                    "Custom Image Prompt (optional)",
                    value="",
                    help="Custom prompt for image description. Leave empty for default.",
                )
            else:
                llm_model = "gpt-4o"
                llm_prompt = None

            azure_enabled = st.checkbox(
                "Azure Document Intelligence",
                value=False,
                key="sidebar_azure_enabled",
                help="Use Azure Document Intelligence for high-accuracy PDF conversion",
            )

            rich_conversion = st.checkbox(
                "Rich Metadata Extraction",
                value=False,
                key="sidebar_rich_conversion",
                help="Extract detailed metadata using format-specific libraries",
            )

        else:
            llm_enabled = False
            llm_model = "gpt-4o"
            llm_prompt = None
            azure_enabled = False
            rich_conversion = False

        # Image Options
        st.subheader("🖼️ Image Options")
        extract_images = st.checkbox("Extract Images", value=True, key="sidebar_extract_images")

        image_mode = st.radio(
            "Image Mode",
            options=[m.value for m in ImageMode],
            index=0,
            help="embed: Base64 in markdown\n"
            "link: Save separately and link\n"
            "separate: Extract but don't link",
        )

        # Table Options
        st.subheader("📊 Table Options")
        extract_tables = st.checkbox("Extract Tables", value=True, key="sidebar_extract_tables")

        table_format = st.selectbox(
            "Table Format",
            options=[f.value for f in TableFormat],
            index=0,
            help="github: GitHub-flavored markdown\n"
            "pipe: Simple pipe tables\n"
            "grid: Grid tables\n"
            "html: HTML tables",
        )

        # OCR Options (for legacy converters and image OCR)
        st.subheader("🔍 OCR Options")
        ocr_enabled = st.checkbox(
            "Force OCR",
            value=False,
            key="sidebar_ocr_enabled",
            help="Force OCR for scanned documents (legacy converters)",
        )

        ocr_language = st.text_input(
            "OCR Language",
            value="eng",
            help="Tesseract language code (e.g., 'eng', 'fra', 'eng+fra')",
        )

        # Format-specific options
        with st.expander("📄 PDF Options"):
            page_breaks = st.checkbox("Include Page Breaks", value=False, key="sidebar_page_breaks")

        with st.expander("🌐 HTML Options"):
            html_download_images = st.checkbox(
                "Download External Images", value=True, key="sidebar_html_download_images"
            )
            html_base_url = st.text_input(
                "Base URL", value="", placeholder="https://example.com"
            )

        with st.expander("📝 DOCX Options"):
            docx_include_comments = st.checkbox("Include Comments", value=False, key="sidebar_docx_include_comments")
            docx_include_headers_footers = st.checkbox(
                "Include Headers/Footers", value=False, key="sidebar_docx_include_headers_footers"
            )

        with st.expander("📊 XLSX Options"):
            xlsx_mode = st.selectbox(
                "Multi-Sheet Handling",
                options=["combined", "separate", "selected"],
                index=0,
            )
            xlsx_sheets = st.text_input(
                "Sheet Names (comma-separated)",
                value="",
                disabled=(xlsx_mode != "selected"),
            )
            xlsx_extract_charts = st.checkbox("Extract Charts", value=True, key="sidebar_xlsx_extract_charts")

        # About section
        st.markdown("---")
        with st.expander("ℹ️ About"):
            st.markdown(
                """
                **Document to Markdown Converter v2.0**

                Powered by Microsoft MarkItDown, supporting:

                📄 **Documents:** PDF, DOCX, XLSX, PPTX
                🌐 **Web:** HTML, XML, JSON
                🖼️ **Images:** JPG, PNG, GIF (with OCR)
                🎵 **Audio:** WAV, MP3, M4A (with transcription)
                📚 **E-books:** EPub
                📦 **Archives:** ZIP
                📧 **Email:** MSG

                **AI Features (Optional):**
                - OpenAI GPT-4 for image descriptions
                - Azure Document Intelligence for PDFs
                - Rich metadata extraction

                [Documentation](https://github.com/yourusername/pdf2markdown)
                """
            )

    return {
        "use_markitdown": use_markitdown,
        "strategy": strategy,
        "llm_enabled": llm_enabled,
        "llm_model": llm_model,
        "llm_prompt": llm_prompt or None,
        "azure_enabled": azure_enabled,
        "rich_conversion": rich_conversion,
        "extract_images": extract_images,
        "image_mode": image_mode,
        "extract_tables": extract_tables,
        "table_format": table_format,
        "ocr_enabled": ocr_enabled,
        "ocr_language": ocr_language,
        "page_breaks": page_breaks,
        "html_download_images": html_download_images,
        "html_base_url": html_base_url or None,
        "docx_include_comments": docx_include_comments,
        "docx_include_headers_footers": docx_include_headers_footers,
        "xlsx_mode": xlsx_mode,
        "xlsx_sheets": xlsx_sheets or None,
        "xlsx_extract_charts": xlsx_extract_charts,
    }


def render_upload_tab(config_dict: dict) -> None:
    """Render the Upload & Convert tab."""

    st.markdown("### 📤 Upload Document")

    # File upload with all supported formats
    uploaded_file = st.file_uploader(
        "Choose a document file",
        type=[
            "pdf",
            "docx",
            "doc",
            "xlsx",
            "xls",
            "pptx",
            "ppt",
            "html",
            "htm",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "wav",
            "mp3",
            "m4a",
            "epub",
            "json",
            "xml",
            "csv",
            "zip",
            "msg",
        ],
        help="Upload any supported document format",
    )

    # YouTube URL input (MarkItDown feature)
    st.markdown("### 🎥 Or Enter YouTube URL")
    youtube_url = st.text_input(
        "YouTube Video URL",
        value="",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Convert YouTube video transcript to Markdown",
    )

    # Display file info
    if uploaded_file is not None:
        file_ext = Path(uploaded_file.name).suffix.upper().lstrip(".")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Type", file_ext)

    # Convert button
    can_convert = uploaded_file is not None or youtube_url.strip()

    if st.button("🚀 Convert to Markdown", type="primary", disabled=not can_convert):
        # Check for API keys if needed
        if config_dict["llm_enabled"] and not os.getenv("OPENAI_API_KEY"):
            st.error(
                "❌ OpenAI API key not set. Please configure in API Settings tab."
            )
            return

        if config_dict["azure_enabled"] and not os.getenv("AZURE_DOCINTEL_KEY"):
            st.error(
                "❌ Azure credentials not set. Please configure in API Settings tab."
            )
            return

        # Convert
        with st.spinner("Converting to Markdown..."):
            if uploaded_file:
                result = convert_document(uploaded_file, config_dict)
            else:
                result = convert_youtube(youtube_url, config_dict)

            if result:
                st.session_state["result"] = result
                st.success("✅ Conversion completed successfully!")

    # Display results
    if "result" in st.session_state:
        display_results(st.session_state["result"])


def render_formats_gallery() -> None:
    """Render the Formats Gallery tab."""

    st.markdown("### 📚 Supported Formats")
    st.markdown(
        "*MarkItDown supports 13+ file formats. Click on each format to learn more.*"
    )

    # Documents
    st.markdown("#### 📄 Documents")
    cols = st.columns(4)
    formats = [
        ("PDF", ".pdf", "Portable Document Format with OCR support"),
        ("DOCX", ".docx", "Microsoft Word documents with formatting"),
        ("XLSX", ".xlsx", "Excel spreadsheets with charts and images"),
        ("PPTX", ".pptx", "PowerPoint presentations"),
    ]

    for col, (name, ext, desc) in zip(cols, formats):
        with col:
            with st.expander(f"{name}"):
                st.markdown(f"**Extension:** `{ext}`")
                st.markdown(f"**Description:** {desc}")

    # Web & Data
    st.markdown("#### 🌐 Web & Data")
    cols = st.columns(4)
    formats = [
        ("HTML", ".html", "Web pages with external images"),
        ("XML", ".xml", "Structured XML documents"),
        ("JSON", ".json", "JSON data files"),
        ("CSV", ".csv", "Comma-separated values"),
    ]

    for col, (name, ext, desc) in zip(cols, formats):
        with col:
            with st.expander(f"{name}"):
                st.markdown(f"**Extension:** `{ext}`")
                st.markdown(f"**Description:** {desc}")

    # Images
    st.markdown("#### 🖼️ Images (with OCR)")
    cols = st.columns(4)
    formats = [
        ("JPEG", ".jpg", "JPEG images with optional OCR"),
        ("PNG", ".png", "PNG images with optional OCR"),
        ("GIF", ".gif", "GIF images with optional OCR"),
        ("BMP", ".bmp", "Bitmap images with optional OCR"),
    ]

    for col, (name, ext, desc) in zip(cols, formats):
        with col:
            with st.expander(f"{name}"):
                st.markdown(f"**Extension:** `{ext}`")
                st.markdown(f"**Description:** {desc}")

    # Audio
    st.markdown("#### 🎵 Audio (with Transcription)")
    cols = st.columns(3)
    formats = [
        ("WAV", ".wav", "WAV audio with speech-to-text"),
        ("MP3", ".mp3", "MP3 audio with speech-to-text"),
        ("M4A", ".m4a", "M4A audio with speech-to-text"),
    ]

    for col, (name, ext, desc) in zip(cols, formats):
        with col:
            with st.expander(f"{name}"):
                st.markdown(f"**Extension:** `{ext}`")
                st.markdown(f"**Description:** {desc}")

    # Other
    st.markdown("#### 📦 Other Formats")
    cols = st.columns(3)
    formats = [
        ("EPub", ".epub", "E-book format"),
        ("ZIP", ".zip", "Archive files"),
        ("MSG", ".msg", "Outlook email messages"),
    ]

    for col, (name, ext, desc) in zip(cols, formats):
        with col:
            with st.expander(f"{name}"):
                st.markdown(f"**Extension:** `{ext}`")
                st.markdown(f"**Description:** {desc}")

    # YouTube
    st.markdown("#### 🎥 Online Content")
    with st.expander("YouTube"):
        st.markdown("**URL:** YouTube video links")
        st.markdown(
            "**Description:** Extract video transcripts and convert to Markdown"
        )


def render_batch_processing(config_dict: dict) -> None:
    """Render the Batch Processing tab."""

    st.markdown("### ⚡ Batch Processing")
    st.markdown("*Convert multiple files at once*")

    uploaded_files = st.file_uploader(
        "Choose multiple files",
        type=[
            "pdf",
            "docx",
            "xlsx",
            "pptx",
            "html",
            "jpg",
            "png",
            "wav",
            "mp3",
            "epub",
            "json",
            "xml",
            "csv",
        ],
        accept_multiple_files=True,
        help="Upload multiple files for batch conversion",
    )

    if uploaded_files:
        st.info(f"📊 Selected {len(uploaded_files)} files")

        # Display file list
        with st.expander("View Files"):
            for file in uploaded_files:
                st.write(
                    f"- {file.name} ({file.size / 1024:.1f} KB)"
                )

        # Parallel processing option
        parallel = st.checkbox(
            "Parallel Processing",
            value=True,
            key="batch_parallel",
            help="Process files in parallel (faster)",
        )

        if st.button("🚀 Convert All", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            results = []

            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Converting {file.name}...")

                result = convert_document(file, config_dict)
                if result:
                    results.append((file.name, result))

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("✅ All conversions completed!")

            # Store results
            st.session_state["batch_results"] = results

    # Display batch results
    if "batch_results" in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Batch Results")

        results = st.session_state["batch_results"]

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(results))
        with col2:
            total_words = sum(
                r.metadata.total_words for _, r in results if r.metadata
            )
            st.metric("Total Words", f"{total_words:,}")
        with col3:
            total_images = sum(
                r.metadata.total_images for _, r in results if r.metadata
            )
            st.metric("Total Images", total_images)

        # Individual results
        for filename, result in results:
            with st.expander(f"📄 {filename}"):
                display_results(result)


def render_api_settings() -> None:
    """Render the API Settings tab."""

    st.markdown("### 🔑 API Credentials")
    st.markdown("*Configure API keys for advanced features*")

    # OpenAI API Key
    st.markdown("#### 🤖 OpenAI (for AI Image Descriptions)")

    current_openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_key = st.text_input(
        "OpenAI API Key",
        value=current_openai_key,
        type="password",
        help="Required for AI-powered image descriptions",
    )

    if st.button("Save OpenAI Key"):
        os.environ["OPENAI_API_KEY"] = openai_key
        st.success("✅ OpenAI API key saved (session only)")
        st.info("💡 For persistent storage, set PDF2MD_LLM_ENABLED=true in .env")

    # Azure Document Intelligence
    st.markdown("---")
    st.markdown("#### ☁️ Azure Document Intelligence")

    current_azure_endpoint = os.getenv("AZURE_DOCINTEL_ENDPOINT", "")
    azure_endpoint = st.text_input(
        "Azure Endpoint",
        value=current_azure_endpoint,
        placeholder="https://your-resource.cognitiveservices.azure.com/",
        help="Azure Document Intelligence endpoint URL",
    )

    current_azure_key = os.getenv("AZURE_DOCINTEL_KEY", "")
    azure_key = st.text_input(
        "Azure Key",
        value=current_azure_key,
        type="password",
        help="Azure Document Intelligence API key",
    )

    if st.button("Save Azure Credentials"):
        os.environ["AZURE_DOCINTEL_ENDPOINT"] = azure_endpoint
        os.environ["AZURE_DOCINTEL_KEY"] = azure_key
        st.success("✅ Azure credentials saved (session only)")
        st.info("💡 For persistent storage, add to .env file")

    # Environment file instructions
    st.markdown("---")
    st.markdown("#### 📝 Persistent Configuration")

    with st.expander("View .env Example"):
        st.code(
            """
# LLM Configuration
PDF2MD_LLM_ENABLED=true
OPENAI_API_KEY=your_openai_api_key_here
PDF2MD_LLM_MODEL=gpt-4o

# Azure Document Intelligence
AZURE_DOCINTEL_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCINTEL_KEY=your_azure_key_here
PDF2MD_AZURE_ENABLED=true

# Conversion Settings
PDF2MD_RICH_CONVERSION=false
PDF2MD_USE_MARKITDOWN=true
        """,
            language="bash",
        )


def display_results(result: ConversionResult) -> None:
    """Display conversion results."""

    st.markdown("---")
    st.header("📊 Results")

    # Summary metrics
    if result.metadata:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pages/Sections", result.metadata.page_count or "N/A")
        with col2:
            st.metric("Words", f"{result.metadata.total_words:,}")
        with col3:
            st.metric("Images", result.metadata.total_images)
        with col4:
            st.metric("Tables", result.metadata.total_tables)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Conversion Time", f"{result.metadata.conversion_time_seconds:.2f}s"
            )
        with col2:
            st.metric("Converter", result.metadata.converter_name or "Unknown")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📝 Markdown", "👁️ Preview", "🖼️ Images", "📋 Metadata"]
    )

    with tab1:
        st.subheader("Markdown Output")

        # Code editor with line numbers
        st.code(result.markdown, language="markdown", line_numbers=True)

        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Markdown",
                data=result.markdown,
                file_name="converted.md",
                mime="text/markdown",
            )
        with col2:
            if result.metadata:
                metadata_json = result.metadata.model_dump_json(indent=2)
                st.download_button(
                    label="📥 Download Metadata",
                    data=metadata_json,
                    file_name="metadata.json",
                    mime="application/json",
                )

    with tab2:
        st.subheader("Preview")
        st.markdown(result.markdown, unsafe_allow_html=False)

    with tab3:
        st.subheader("Extracted Images")

        if result.images:
            total_images = len(result.images)
            st.info(f"📊 Total images extracted: {total_images}")

            # Pagination
            images_per_page = 12
            if total_images > images_per_page:
                if "image_page" not in st.session_state:
                    st.session_state["image_page"] = 0

                total_pages = (total_images + images_per_page - 1) // images_per_page

                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button(
                        "⬅️ Previous", disabled=st.session_state["image_page"] == 0
                    ):
                        st.session_state["image_page"] -= 1

                with col2:
                    st.write(
                        f"Page {st.session_state['image_page'] + 1} of {total_pages}"
                    )
                with col3:
                    if st.button(
                        "Next ➡️",
                        disabled=st.session_state["image_page"] >= total_pages - 1,
                    ):
                        st.session_state["image_page"] += 1

                start_idx = st.session_state["image_page"] * images_per_page
                end_idx = min(start_idx + images_per_page, total_images)
                images_to_display = result.images[start_idx:end_idx]
            else:
                images_to_display = result.images

            # Display images in grid
            cols = st.columns(3)
            for idx, img in enumerate(images_to_display):
                with cols[idx % 3]:
                    if img.base64_data:
                        img_data = base64.b64decode(img.base64_data)
                        st.image(img_data, caption=img.alt_text, use_column_width=True)

                        st.caption(
                            f"📄 Page {img.page} | "
                            f"📐 {img.width}x{img.height} | "
                            f"💾 {img.size_bytes / 1024:.1f} KB"
                        )
        else:
            st.info("ℹ️ No images extracted from this document")

    with tab4:
        st.subheader("Conversion Metadata")

        if result.metadata:
            # Document info
            st.markdown("**📄 Document Information**")
            doc_info = {
                "Title": result.metadata.title or "N/A",
                "Author": result.metadata.author or "N/A",
                "Pages": result.metadata.page_count or "N/A",
                "Creator": result.metadata.creator or "N/A",
                "Subject": result.metadata.subject or "N/A",
            }
            st.json(doc_info)

            # Conversion info
            st.markdown("**⚙️ Conversion Details**")
            conversion_info = {
                "Converter": result.metadata.converter_name,
                "Strategy": result.metadata.strategy_used,
                "Time": f"{result.metadata.conversion_time_seconds:.2f}s",
                "Timestamp": (
                    result.metadata.timestamp.isoformat()
                    if result.metadata.timestamp
                    else "N/A"
                ),
            }
            st.json(conversion_info)

            # Statistics
            st.markdown("**📊 Statistics**")
            stats = {
                "Total Words": result.metadata.total_words,
                "Total Images": result.metadata.total_images,
                "Total Tables": result.metadata.total_tables,
                "File Size": f"{result.metadata.source_size_bytes / 1024:.1f} KB"
                if result.metadata.source_size_bytes
                else "N/A",
            }
            st.json(stats)

            # Warnings/Errors
            if result.metadata.warnings:
                st.warning("⚠️ **Warnings:**")
                for warning in result.metadata.warnings:
                    st.write(f"- {warning}")

            if result.metadata.errors:
                st.error("❌ **Errors:**")
                for error in result.metadata.errors:
                    st.write(f"- {error}")


def convert_document(
    uploaded_file, config_dict: dict
) -> Optional[ConversionResult]:
    """Convert uploaded document file."""

    try:
        # Save to temp file
        file_ext = Path(uploaded_file.name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)

        # Parse XLSX sheets
        xlsx_sheets_list = None
        if config_dict["xlsx_sheets"]:
            xlsx_sheets_list = [s.strip() for s in config_dict["xlsx_sheets"].split(",")]

        # Create config
        config = Config(
            use_markitdown=config_dict["use_markitdown"],
            strategy=ConversionStrategy(config_dict["strategy"]),
            rich_conversion=config_dict["rich_conversion"],
            llm_enabled=config_dict["llm_enabled"],
            llm_model=config_dict["llm_model"],
            llm_prompt=config_dict["llm_prompt"],
            azure_enabled=config_dict["azure_enabled"],
            image_mode=ImageMode(config_dict["image_mode"]),
            extract_images=config_dict["extract_images"],
            extract_tables=config_dict["extract_tables"],
            table_format=TableFormat(config_dict["table_format"]),
            ocr_enabled=config_dict["ocr_enabled"],
            ocr_language=config_dict["ocr_language"],
            include_page_breaks=config_dict["page_breaks"],
            html_download_images=config_dict["html_download_images"],
            html_base_url=config_dict["html_base_url"],
            docx_include_comments=config_dict["docx_include_comments"],
            docx_include_headers_footers=config_dict["docx_include_headers_footers"],
            xlsx_mode=config_dict["xlsx_mode"],
            xlsx_sheets=xlsx_sheets_list,
            xlsx_extract_charts=config_dict["xlsx_extract_charts"],
        )

        # Convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(tmp_path)

        # Clean up
        tmp_path.unlink()

        return result

    except Exception as e:
        st.error(f"❌ Conversion failed: {e}")
        import traceback

        st.code(traceback.format_exc())
        return None


def convert_youtube(youtube_url: str, config_dict: dict) -> Optional[ConversionResult]:
    """Convert YouTube video transcript."""

    try:
        # MarkItDown handles YouTube URLs directly
        # We create a temporary text file with the URL
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write(youtube_url)
            tmp_path = Path(tmp_file.name)

        config = Config(
            use_markitdown=True,
            strategy=ConversionStrategy.MARKITDOWN,
            llm_enabled=config_dict["llm_enabled"],
            llm_model=config_dict["llm_model"],
        )

        # Note: YouTube conversion requires special handling
        # For now, show an info message
        st.info(
            "ℹ️ YouTube conversion requires the youtube-transcript-api package. "
            "Install with: pip install youtube-transcript-api"
        )

        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(tmp_path)

        tmp_path.unlink()

        return result

    except Exception as e:
        st.error(f"❌ YouTube conversion failed: {e}")
        st.info(
            "💡 Make sure you have installed: pip install youtube-transcript-api"
        )
        return None


if __name__ == "__main__":
    main()
