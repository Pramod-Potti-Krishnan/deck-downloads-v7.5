"""
v7.5 Presentation Download Service - FastAPI Server
===================================================

REST API for converting v7.5-main presentations to PDF/PPTX formats.
"""

import os
import io
import logging
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import uvicorn

from converters.pdf_converter import PDFConverter
from converters.pptx_converter import PPTXConverter
from converters.native_pptx_converter import NativePPTXConverter

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="v7.5 Download Service",
    description="Convert v7.5-main presentations to PDF and PPTX formats",
    version="1.0.0"
)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class PDFConversionRequest(BaseModel):
    """Request model for PDF conversion"""
    presentation_url: str = Field(
        ...,
        description="Full URL to presentation (e.g., https://v75-main.railway.app/p/{id})",
        example="https://v75-main.railway.app/p/abc123"
    )
    slide_count: Optional[int] = Field(
        default=None,
        description="Number of slides in the presentation (optional, will be auto-detected if missing)",
        gt=0,
        example=7
    )
    quality: Literal["high", "medium", "low"] = Field(
        default="high",
        description="Quality level for PDF generation (high: 1920×1080, medium: 1440×810, low: 960×540)"
    )
    # Allow extra fields to prevent 422 errors from older clients
    landscape: Optional[bool] = None
    aspect_ratio: Optional[str] = None


class PPTXConversionRequest(BaseModel):
    """Request model for PPTX conversion"""
    presentation_url: str = Field(
        ...,
        description="Full URL to presentation (e.g., https://v75-main.railway.app/p/{id})",
        example="https://v75-main.railway.app/p/abc123"
    )
    slide_count: Optional[int] = Field(
        default=None,
        description="Number of slides in the presentation (optional, will be auto-detected if missing)",
        gt=0,
        example=7
    )
    variant: Literal["screenshot", "native"] = Field(
        default="native",
        description="PPTX generation variant: 'screenshot' or 'native' (default)"
    )
    aspect_ratio: Literal["16:9", "4:3"] = Field(
        default="16:9",
        description="Slide aspect ratio"
    )
    quality: Literal["high", "medium", "low"] = Field(
        default="high",
        description="Image quality level"
    )


# Startup validation
@app.on_event("startup")
async def startup_validation():
    """Validate Playwright browser installation on startup"""
    logger.info("=" * 60)
    logger.info("🔍 Validating Playwright Browser Installation")
    logger.info("=" * 60)

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            version = browser.version
            await browser.close()

        logger.info(f"✅ Playwright Chromium ready (version: {version})")
        logger.info(f"✅ PDF conversion: READY")
        logger.info(f"✅ PPTX conversion: READY")

    except Exception as e:
        logger.error(f"❌ Playwright validation failed: {e}")
        logger.error(f"💡 Run: playwright install --with-deps chromium")
        raise RuntimeError(f"Playwright not available: {e}")

    logger.info("=" * 60)


# Health check
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "v7.5 Download Service",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": ["pdf", "pptx"],
        "endpoints": {
            "health": "GET /health",
            "convert_pdf": "POST /convert/pdf",
            "convert_pptx": "POST /convert/pptx"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "playwright": "ready",
        "converters": {
            "pdf": "operational",
            "pptx": "operational"
        }
    }


# PDF Conversion Endpoint
@app.post("/convert/pdf")
async def convert_to_pdf(request: PDFConversionRequest):
    """
    Convert presentation to PDF using screenshot-based approach

    This endpoint:
    1. Navigates to the presentation URL using Playwright
    2. Waits for Reveal.js to load
    3. Captures each slide as a high-resolution screenshot
    4. Combines screenshots into a PDF
    5. Returns PDF file as download

    Why screenshot-based:
    The v7.5-main presentation uses a strict 32×18 CSS Grid system that
    conflicts with Reveal.js print-pdf mode, causing positioning and margin
    issues. Screenshot-based approach ensures 100% accurate rendering.

    The presentation URL should point to a v7.5-main viewer page.
    """
    try:
        logger.info(f"📄 PDF conversion requested: {request.presentation_url}")

        # Extract presentation ID from URL
        presentation_id = request.presentation_url.split("/p/")[-1]

        # Extract base URL (everything before /p/)
        base_url = request.presentation_url.split("/p/")[0]

        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Presentation ID: {presentation_id}")
        logger.info(f"  Slide Count: {request.slide_count}")
        logger.info(f"  Quality: {request.quality}")

        # Initialize converter
        converter = PDFConverter(base_url=base_url)

        # Generate PDF using screenshot-based approach
        pdf_bytes = await converter.generate_pdf(
            presentation_id=presentation_id,
            slide_count=request.slide_count,
            quality=request.quality
        )

        logger.info(f"✅ PDF generated: {len(pdf_bytes):,} bytes")

        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="presentation-{presentation_id}.pdf"'
            }
        )

    except Exception as e:
        logger.error(f"❌ PDF conversion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF conversion failed: {str(e)}"
        )


# PPTX Conversion Endpoint
@app.post("/convert/pptx")
async def convert_to_pptx(request: PPTXConversionRequest):
    """
    Convert presentation to PPTX

    This endpoint:
    1. Navigates to the presentation URL using Playwright
    2. Waits for Reveal.js to load
    3. Captures screenshot of each slide
    4. Creates PowerPoint with screenshots as slides
    5. Returns PPTX file as download

    The presentation URL should point to a v7.5-main viewer page.
    """
    try:
        logger.info(f"📊 PPTX conversion requested: {request.presentation_url}")

        # Extract presentation ID from URL
        presentation_id = request.presentation_url.split("/p/")[-1]

        # Extract base URL
        base_url = request.presentation_url.split("/p/")[0]

        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Presentation ID: {presentation_id}")
        logger.info(f"  Slide Count: {request.slide_count}")
        logger.info(f"  Quality: {request.quality}")

        # Initialize converter
        converter = PPTXConverter(base_url=base_url)

        # Generate PPTX
        pptx_bytes = await converter.generate_pptx(
            presentation_id=presentation_id,
            slide_count=request.slide_count,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality
        )

        logger.info(f"✅ PPTX generated: {len(pptx_bytes):,} bytes")

        # Return PPTX as streaming response
        return StreamingResponse(
            io.BytesIO(pptx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="presentation-{presentation_id}.pptx"'
            }
        )

    except Exception as e:
        logger.error(f"❌ PPTX conversion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PPTX conversion failed: {str(e)}"
        )


def run_server():
    """Start the download service server"""
    port = int(os.getenv("PORT", "8010"))

    logger.info(f"\n🌐 Starting server on http://0.0.0.0:{port}")
    logger.info(f"📍 CORS allowed origins: {allowed_origins}")
    logger.info("=" * 60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
