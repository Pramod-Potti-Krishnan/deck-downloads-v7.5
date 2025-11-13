# v7.5 Presentation Download Service

Microservice for converting v7.5-main presentations to PDF and PPTX formats using Playwright.

## Overview

This standalone service handles the heavy lifting of presentation conversion:
- Accepts presentation URLs from v7.5-main
- Uses Playwright + Chromium for accurate rendering
- Converts presentations to PDF or PPTX format
- Returns downloadable files

## Architecture

```
v7.5-main (lightweight)          v7.5-downloads (this service)
    ↓                                    ↓
Creates presentation          Converts presentation to files
    ↓                                    ↓
Returns URL            ← URL →    Fetches and converts
```

## Features

- ✅ **PDF Export**: High-fidelity PDF generation using Reveal.js print-pdf mode
- ✅ **Perfect 16:9 Aspect Ratio**: True 16"×9" dimensions for presentation slides
- ✅ **Clean Output**: Automatically hides debug UI elements and controls
- ✅ **PPTX Export**: PowerPoint files with screenshot-based slides
- ✅ **Quality Control**: High/medium/low quality options
- ✅ **Orientation Support**: Landscape and portrait for PDF
- ✅ **Aspect Ratios**: 16:9 and 4:3 for PPTX

## API Endpoints

### Health Check
```
GET /
GET /health
```

Returns service status and capabilities.

### Convert to PDF
```
POST /convert/pdf
Content-Type: application/json

{
  "presentation_url": "https://v75-main.railway.app/p/abc123",
  "landscape": true,
  "print_background": true,
  "quality": "high"
}
```

Returns: PDF file download

### Convert to PPTX
```
POST /convert/pptx
Content-Type: application/json

{
  "presentation_url": "https://v75-main.railway.app/p/abc123",
  "slide_count": 7,
  "aspect_ratio": "16:9",
  "quality": "high"
}
```

Returns: PPTX file download

## Local Development

### Prerequisites
- Python 3.11+
- Playwright + Chromium

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install --with-deps chromium

# Start service
python3 main.py
```

Server will start on `http://localhost:8010`

### Test the Service

```bash
# Health check
curl http://localhost:8010/health

# Test PDF conversion (requires v7.5-main running)
curl -X POST http://localhost:8010/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/test-id",
    "quality": "high"
  }' \
  -o test.pdf

# Test PPTX conversion
curl -X POST http://localhost:8010/convert/pptx \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/test-id",
    "slide_count": 7,
    "quality": "high"
  }' \
  -o test.pptx
```

## Railway Deployment

### Build Configuration

The service uses Docker with Playwright base image:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble
# ... (Chromium pre-installed in base image)
RUN playwright install --with-deps chromium
```

### Environment Variables

- `PORT` - Port to run server on (Railway sets automatically)
- `ALLOWED_ORIGINS` - CORS origins (default: `*`)

### Deploy to Railway

1. Create new Railway project
2. Connect to GitHub repository
3. Set root directory to this folder
4. Railway auto-detects `Dockerfile`
5. Deploy!

### Resource Requirements

- **Memory**: 512MB minimum, 1GB recommended
- **CPU**: 0.5 vCPU minimum
- **Storage**: ~500MB (for Chromium browser)
- **Build Time**: 5-8 minutes (Playwright installation)

## Integration with v7.5-main

### Example: Director Integration

```python
import httpx

# 1. Create presentation via v7.5-main
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://v75-main.railway.app/api/presentations",
        json={"title": "My Deck", "slides": [...]}
    )
    presentation_id = response.json()["id"]
    presentation_url = f"https://v75-main.railway.app/p/{presentation_id}"

# 2. Convert to PDF via download service
async with httpx.AsyncClient(timeout=60.0) as client:
    pdf_response = await client.post(
        "https://v75-downloads.railway.app/convert/pdf",
        json={
            "presentation_url": presentation_url,
            "quality": "high"
        }
    )
    pdf_bytes = pdf_response.content

    # Save or return PDF
    with open("presentation.pdf", "wb") as f:
        f.write(pdf_bytes)
```

## Quality Settings

### PDF Quality
- **high**: 1920×1080 viewport, 16"×9" true 16:9 aspect ratio, best for printing
- **medium**: 1440×810 viewport, 16"×9" aspect ratio, good for screen sharing
- **low**: 960×540 viewport, 16"×9" aspect ratio, fast generation

**Note**: All PDFs use Reveal.js print-pdf mode for optimal layout and automatically hide debug UI elements.

### PPTX Quality
- **high**: 1920×1080 screenshots, ~3-5MB per deck
- **medium**: 1440×810 screenshots, ~2-3MB per deck
- **low**: 960×540 screenshots, ~1-2MB per deck

## Troubleshooting

### Playwright Installation Issues

```bash
# If Playwright fails to install browsers
playwright install --with-deps chromium

# On Linux, may need additional system packages
sudo apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### Memory Issues

If conversions fail with OOM errors:
- Increase Railway service memory to 1GB
- Reduce quality to "medium" or "low"
- Process slides in smaller batches

### Connection Timeouts

If conversions timeout:
- Increase client timeout (default: 60s)
- Check v7.5-main is accessible from download service
- Verify presentation URL is correct

## Project Structure

```
v7.5-downloads/
├── main.py              # Entry point
├── server.py            # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker build configuration
├── entrypoint.sh        # Container startup script
├── Procfile             # Railway process definition
├── railway.toml         # Railway deployment config
├── converters/          # Conversion logic
│   ├── base.py         # Playwright browser automation
│   ├── pdf_converter.py # PDF generation
│   └── pptx_converter.py # PPTX generation
└── README.md           # This file
```

## Technology Stack

- **FastAPI**: Modern Python web framework
- **Playwright**: Browser automation for rendering
- **python-pptx**: PowerPoint file generation
- **Pillow**: Image processing
- **Uvicorn**: ASGI server

## Performance

- **PDF Generation**: ~5-10 seconds for 10 slides
- **PPTX Generation**: ~10-15 seconds for 10 slides
- **Concurrent Requests**: Supports multiple simultaneous conversions
- **Caching**: No caching (stateless service)

## License

Internal use only.

## Support

For issues or questions, contact the development team.
