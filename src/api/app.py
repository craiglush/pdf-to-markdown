"""FastAPI application for PDF to Markdown conversion API."""

import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from pdf2markdown import __version__
from pdf2markdown.core.config import Config, ConversionStrategy, ImageMode, TableFormat
from pdf2markdown.core.orchestrator import ConversionOrchestrator

# Create FastAPI app
app = FastAPI(
    title="Document to Markdown API",
    description="High-fidelity document to Markdown conversion REST API. Supports: PDF, HTML, DOCX, XLSX",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Job storage (in production, use Redis or database)
conversion_jobs: Dict[str, dict] = {}


# Request/Response models
class ConversionRequest(BaseModel):
    """Request model for conversion options."""

    strategy: str = "auto"
    image_mode: str = "embed"
    extract_images: bool = True
    extract_tables: bool = True
    table_format: str = "github"
    ocr_enabled: bool = False
    ocr_language: str = "eng"
    include_page_breaks: bool = False
    # HTML-specific options
    html_download_images: bool = True
    html_base_url: Optional[str] = None
    # DOCX-specific options
    docx_include_comments: bool = False
    docx_include_headers_footers: bool = False
    # XLSX-specific options
    xlsx_mode: str = "combined"
    xlsx_sheets: Optional[list[str]] = None
    xlsx_extract_charts: bool = True


class ConversionResponse(BaseModel):
    """Response model for conversion results."""

    job_id: str
    status: str
    message: str
    markdown: Optional[str] = None
    metadata: Optional[dict] = None


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str
    progress: float
    message: str
    result: Optional[dict] = None


# Health check endpoint
@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Document to Markdown API",
        "version": __version__,
        "status": "healthy",
        "formats": ["PDF", "HTML", "DOCX", "XLSX"],
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    orchestrator = ConversionOrchestrator()
    available_converters = orchestrator.list_available_converters()

    return {
        "status": "healthy",
        "version": __version__,
        "converters": available_converters,
    }


@app.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_document(
    file: UploadFile = File(..., description="Document file to convert (PDF, HTML, DOCX, XLSX)"),
    strategy: str = "auto",
    image_mode: str = "embed",
    extract_images: bool = True,
    extract_tables: bool = True,
    table_format: str = "github",
    ocr_enabled: bool = False,
    ocr_language: str = "eng",
    html_download_images: bool = True,
    html_base_url: Optional[str] = None,
    docx_include_comments: bool = False,
    docx_include_headers_footers: bool = False,
    xlsx_mode: str = "combined",
    xlsx_sheets: Optional[str] = None,
    xlsx_extract_charts: bool = True,
) -> ConversionResponse:
    """
    Convert a document file to Markdown.

    Supports: PDF, HTML, DOCX, XLSX

    Args:
        file: Document file to convert
        strategy: Conversion strategy (auto, fast, accurate, ocr) - mainly for PDFs
        image_mode: Image handling (embed, link, separate)
        extract_images: Extract images from document
        extract_tables: Extract tables from document
        table_format: Table format (github, pipe, grid, html)
        ocr_enabled: Enable OCR for scanned PDFs
        ocr_language: Tesseract language code
        html_download_images: Download external images from HTML (otherwise keep as links)
        html_base_url: Base URL for resolving relative links in HTML
        docx_include_comments: Include comments and tracked changes in DOCX
        docx_include_headers_footers: Include headers and footers from DOCX
        xlsx_mode: Multi-sheet handling (combined, separate, selected)
        xlsx_sheets: Comma-separated sheet names for 'selected' mode
        xlsx_extract_charts: Extract charts as images from XLSX

    Returns:
        ConversionResponse with markdown content
    """
    # Validate file type
    supported_extensions = {'.pdf', '.html', '.htm', '.docx', '.xlsx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
        )

    try:
        # Save uploaded file with appropriate suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        # Parse XLSX sheets if provided
        xlsx_sheets_list = None
        if xlsx_sheets:
            xlsx_sheets_list = [s.strip() for s in xlsx_sheets.split(',')]

        # Create configuration
        config = Config(
            strategy=ConversionStrategy(strategy),
            image_mode=ImageMode(image_mode),
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=TableFormat(table_format),
            ocr_enabled=ocr_enabled,
            ocr_language=ocr_language,
            # HTML-specific options
            html_download_images=html_download_images,
            html_base_url=html_base_url,
            # DOCX-specific options
            docx_include_comments=docx_include_comments,
            docx_include_headers_footers=docx_include_headers_footers,
            # XLSX-specific options
            xlsx_mode=xlsx_mode,
            xlsx_sheets=xlsx_sheets_list,
            xlsx_extract_charts=xlsx_extract_charts,
        )

        # Convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(tmp_path)

        # Clean up
        tmp_path.unlink()

        # Generate job ID
        job_id = str(uuid.uuid4())

        return ConversionResponse(
            job_id=job_id,
            status="completed",
            message="Conversion completed successfully",
            markdown=result.markdown,
            metadata=result.metadata.model_dump() if result.metadata else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.post("/convert/async", response_model=JobStatusResponse, tags=["Conversion"])
async def convert_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to convert (PDF, HTML, DOCX, XLSX)"),
    strategy: str = "auto",
    image_mode: str = "embed",
    extract_images: bool = True,
    extract_tables: bool = True,
    table_format: str = "github",
    html_download_images: bool = True,
    html_base_url: Optional[str] = None,
    docx_include_comments: bool = False,
    docx_include_headers_footers: bool = False,
    xlsx_mode: str = "combined",
    xlsx_sheets: Optional[str] = None,
    xlsx_extract_charts: bool = True,
) -> JobStatusResponse:
    """
    Start an asynchronous document conversion job.

    Supports: PDF, HTML, DOCX, XLSX

    Args:
        background_tasks: FastAPI background tasks
        file: Document file to convert
        strategy: Conversion strategy
        image_mode: Image handling mode
        extract_images: Extract images
        extract_tables: Extract tables
        table_format: Table format
        html_download_images: Download external images from HTML
        html_base_url: Base URL for resolving relative links in HTML
        docx_include_comments: Include comments and tracked changes in DOCX
        docx_include_headers_footers: Include headers and footers from DOCX
        xlsx_mode: Multi-sheet handling (combined, separate, selected)
        xlsx_sheets: Comma-separated sheet names for 'selected' mode
        xlsx_extract_charts: Extract charts as images from XLSX

    Returns:
        Job status response with job ID
    """
    # Validate file
    supported_extensions = {'.pdf', '.html', '.htm', '.docx', '.xlsx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save file with appropriate suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    # Initialize job
    conversion_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "Conversion queued",
        "file_path": str(tmp_path),
        "result": None,
    }

    # Add background task
    background_tasks.add_task(
        process_conversion,
        job_id,
        tmp_path,
        strategy,
        image_mode,
        extract_images,
        extract_tables,
        table_format,
        html_download_images,
        html_base_url,
        docx_include_comments,
        docx_include_headers_footers,
        xlsx_mode,
        xlsx_sheets,
        xlsx_extract_charts,
    )

    return JobStatusResponse(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Conversion job started",
    )


async def process_conversion(
    job_id: str,
    file_path: Path,
    strategy: str,
    image_mode: str,
    extract_images: bool,
    extract_tables: bool,
    table_format: str,
    html_download_images: bool = True,
    html_base_url: Optional[str] = None,
    docx_include_comments: bool = False,
    docx_include_headers_footers: bool = False,
    xlsx_mode: str = "combined",
    xlsx_sheets: Optional[str] = None,
    xlsx_extract_charts: bool = True,
) -> None:
    """
    Background task to process document conversion.

    Args:
        job_id: Job identifier
        file_path: Path to document file
        strategy: Conversion strategy
        image_mode: Image handling mode
        extract_images: Extract images
        extract_tables: Extract tables
        table_format: Table format
        html_download_images: Download external images from HTML
        html_base_url: Base URL for resolving relative links in HTML
        docx_include_comments: Include comments and tracked changes in DOCX
        docx_include_headers_footers: Include headers and footers from DOCX
        xlsx_mode: Multi-sheet handling (combined, separate, selected)
        xlsx_sheets: Comma-separated sheet names for 'selected' mode
        xlsx_extract_charts: Extract charts as images from XLSX
    """
    try:
        # Update status
        conversion_jobs[job_id]["status"] = "processing"
        conversion_jobs[job_id]["progress"] = 0.1
        conversion_jobs[job_id]["message"] = "Converting document..."

        # Parse XLSX sheets if provided
        xlsx_sheets_list = None
        if xlsx_sheets:
            xlsx_sheets_list = [s.strip() for s in xlsx_sheets.split(',')]

        # Create configuration
        config = Config(
            strategy=ConversionStrategy(strategy),
            image_mode=ImageMode(image_mode),
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=TableFormat(table_format),
            html_download_images=html_download_images,
            html_base_url=html_base_url,
            docx_include_comments=docx_include_comments,
            docx_include_headers_footers=docx_include_headers_footers,
            xlsx_mode=xlsx_mode,
            xlsx_sheets=xlsx_sheets_list,
            xlsx_extract_charts=xlsx_extract_charts,
        )

        # Convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(file_path)

        # Update with result
        conversion_jobs[job_id]["status"] = "completed"
        conversion_jobs[job_id]["progress"] = 1.0
        conversion_jobs[job_id]["message"] = "Conversion completed"
        conversion_jobs[job_id]["result"] = {
            "markdown": result.markdown,
            "metadata": result.metadata.model_dump() if result.metadata else None,
        }

    except Exception as e:
        conversion_jobs[job_id]["status"] = "failed"
        conversion_jobs[job_id]["message"] = f"Conversion failed: {str(e)}"

    finally:
        # Clean up temp file
        try:
            file_path.unlink()
        except Exception:
            pass


@app.get("/convert/status/{job_id}", response_model=JobStatusResponse, tags=["Conversion"])
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a conversion job.

    Args:
        job_id: Job identifier

    Returns:
        Job status response
    """
    if job_id not in conversion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = conversion_jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result=job.get("result"),
    )


@app.post("/convert/batch", tags=["Conversion"])
async def convert_batch(
    files: List[UploadFile] = File(..., description="Document files to convert (PDF, HTML, DOCX, XLSX)"),
    strategy: str = "auto",
) -> dict:
    """
    Convert multiple document files in batch.

    Supports: PDF, HTML, DOCX, XLSX

    Args:
        files: List of document files
        strategy: Conversion strategy

    Returns:
        Batch conversion results
    """
    results = []

    for file in files:
        try:
            # Determine file extension
            file_ext = Path(file.filename).suffix.lower()

            # Save file with appropriate suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)

            # Convert
            config = Config(strategy=ConversionStrategy(strategy))
            orchestrator = ConversionOrchestrator(config)
            result = orchestrator.convert(tmp_path)

            # Clean up
            tmp_path.unlink()

            results.append({
                "filename": file.filename,
                "status": "success",
                "markdown": result.markdown,
                "pages": result.metadata.page_count if result.metadata else 0,
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e),
            })

    return {
        "total": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results,
    }


@app.get("/converters", tags=["Info"])
async def list_converters() -> dict:
    """
    List available converters and their capabilities.

    Returns:
        Dictionary of available converters
    """
    orchestrator = ConversionOrchestrator()
    available = orchestrator.list_available_converters()

    # Restructure the nested dictionary to include converter info
    converters = {}
    for file_type, strategies in available.items():
        converters[file_type] = {}
        for strategy, is_available in strategies.items():
            converters[file_type][strategy] = {
                "available": is_available,
                "info": orchestrator.get_converter_info(file_type, strategy) if is_available else "Not available",
            }

    return {"converters": converters}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
