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
    title="PDF to Markdown API",
    description="High-fidelity PDF to Markdown conversion REST API",
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
        "name": "PDF to Markdown API",
        "version": __version__,
        "status": "healthy",
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
        "converters": {
            k.value: v for k, v in available_converters.items()
        },
    }


@app.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_pdf(
    file: UploadFile = File(..., description="PDF file to convert"),
    strategy: str = "auto",
    image_mode: str = "embed",
    extract_images: bool = True,
    extract_tables: bool = True,
    table_format: str = "github",
    ocr_enabled: bool = False,
    ocr_language: str = "eng",
) -> ConversionResponse:
    """
    Convert a PDF file to Markdown.

    Args:
        file: PDF file to convert
        strategy: Conversion strategy (auto, fast, accurate, ocr)
        image_mode: Image handling (embed, link, separate)
        extract_images: Extract images from PDF
        extract_tables: Extract tables from PDF
        table_format: Table format (github, pipe, grid, html)
        ocr_enabled: Enable OCR for scanned PDFs
        ocr_language: Tesseract language code

    Returns:
        ConversionResponse with markdown content
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
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
async def convert_pdf_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    strategy: str = "auto",
    image_mode: str = "embed",
    extract_images: bool = True,
    extract_tables: bool = True,
    table_format: str = "github",
) -> JobStatusResponse:
    """
    Start an asynchronous PDF conversion job.

    Args:
        background_tasks: FastAPI background tasks
        file: PDF file to convert
        strategy: Conversion strategy
        image_mode: Image handling mode
        extract_images: Extract images
        extract_tables: Extract tables
        table_format: Table format

    Returns:
        Job status response with job ID
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    # Initialize job
    conversion_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "Conversion queued",
        "pdf_path": str(tmp_path),
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
    )

    return JobStatusResponse(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Conversion job started",
    )


async def process_conversion(
    job_id: str,
    pdf_path: Path,
    strategy: str,
    image_mode: str,
    extract_images: bool,
    extract_tables: bool,
    table_format: str,
) -> None:
    """
    Background task to process PDF conversion.

    Args:
        job_id: Job identifier
        pdf_path: Path to PDF file
        strategy: Conversion strategy
        image_mode: Image handling mode
        extract_images: Extract images
        extract_tables: Extract tables
        table_format: Table format
    """
    try:
        # Update status
        conversion_jobs[job_id]["status"] = "processing"
        conversion_jobs[job_id]["progress"] = 0.1
        conversion_jobs[job_id]["message"] = "Converting PDF..."

        # Create configuration
        config = Config(
            strategy=ConversionStrategy(strategy),
            image_mode=ImageMode(image_mode),
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=TableFormat(table_format),
        )

        # Convert
        orchestrator = ConversionOrchestrator(config)
        result = orchestrator.convert(pdf_path)

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
            pdf_path.unlink()
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
    files: List[UploadFile] = File(...),
    strategy: str = "auto",
) -> dict:
    """
    Convert multiple PDF files in batch.

    Args:
        files: List of PDF files
        strategy: Conversion strategy

    Returns:
        Batch conversion results
    """
    results = []

    for file in files:
        try:
            # Save file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
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

    return {
        "converters": {
            k.value: {
                "available": v,
                "info": orchestrator.get_converter_info(k) if v else "Not available",
            }
            for k, v in available.items()
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
