# v7.5 Download Service - API Documentation

**Version**: 1.0.0
**Base URL**: `http://localhost:8010` (local) or `https://your-railway-url.railway.app` (production)
**Content-Type**: `application/json`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Convert to PDF](#convert-to-pdf)
   - [Convert to PPTX](#convert-to-pptx)
4. [Request Models](#request-models)
5. [Response Formats](#response-formats)
6. [Error Handling](#error-handling)
7. [Quality Settings](#quality-settings)
8. [Examples](#examples)
9. [Rate Limits](#rate-limits)
10. [Integration Guide](#integration-guide)

---

## Overview

The v7.5 Download Service is a microservice for converting v7.5-main presentations to PDF and PPTX formats. It uses Playwright + Chromium for high-fidelity rendering and python-pptx for PowerPoint generation.

### Key Features

- ✅ **PDF Export**: Browser-based PDF generation with perfect styling
- ✅ **PPTX Export**: Screenshot-based PowerPoint files
- ✅ **Quality Control**: High, medium, and low quality options
- ✅ **Orientation Support**: Landscape and portrait for PDFs
- ✅ **Aspect Ratios**: 16:9 and 4:3 for PPTX
- ✅ **RESTful API**: Simple HTTP POST requests
- ✅ **Streaming Responses**: Efficient file downloads

### Architecture

```
Client/Director
    ↓
    ├─→ v7.5-main: Create presentation
    │   ← Returns: {id, url}
    ↓
    └─→ v7.5-downloads: Convert to PDF/PPTX
        ← Returns: File download
```

---

## Authentication

**Current Version**: No authentication required

For production deployments, consider adding:
- API key authentication (`X-API-Key` header)
- OAuth 2.0 for user-specific operations
- Rate limiting per API key

---

## Endpoints

### Health Check

#### Get Service Status

```http
GET /
```

Returns service information and available endpoints.

**Response**: `200 OK`

```json
{
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
```

---

#### Get Health Status

```http
GET /health
```

Returns detailed health status including Playwright readiness.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "playwright": "ready",
  "converters": {
    "pdf": "operational",
    "pptx": "operational"
  }
}
```

**Example**:

```bash
curl http://localhost:8010/health
```

---

### Convert to PDF

```http
POST /convert/pdf
```

Converts a v7.5-main presentation to PDF format.

#### Request Body

```json
{
  "presentation_url": "string (required)",
  "landscape": "boolean (optional, default: true)",
  "print_background": "boolean (optional, default: true)",
  "quality": "string (optional, default: 'high')"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `presentation_url` | string | Yes | - | Full URL to presentation viewer (e.g., `https://v75-main.railway.app/p/{id}`) |
| `landscape` | boolean | No | `true` | Use landscape orientation (true) or portrait (false) |
| `print_background` | boolean | No | `true` | Include background graphics and colors |
| `quality` | string | No | `"high"` | Quality level: `"high"`, `"medium"`, or `"low"` |

#### Response

**Success**: `200 OK`

- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="presentation-{id}.pdf"`
- **Body**: Binary PDF file

**Error**: `500 Internal Server Error`

```json
{
  "detail": "PDF conversion failed: {error message}"
}
```

#### Quality Settings

| Quality | Resolution | File Size | Use Case |
|---------|-----------|-----------|----------|
| `high` | 1920×1080 | ~500KB-2MB | Final deliverables, printing |
| `medium` | 1440×810 | ~300KB-1MB | Quick reviews, email sharing |
| `low` | 960×540 | ~150KB-500KB | Draft versions, fast downloads |

#### Example

```bash
# High quality, landscape PDF
curl -X POST http://localhost:8010/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/abc123",
    "landscape": true,
    "print_background": true,
    "quality": "high"
  }' \
  -o presentation.pdf

# Portrait, medium quality
curl -X POST http://localhost:8010/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "https://v75-main.railway.app/p/abc123",
    "landscape": false,
    "quality": "medium"
  }' \
  -o presentation-portrait.pdf
```

---

### Convert to PPTX

```http
POST /convert/pptx
```

Converts a v7.5-main presentation to PowerPoint (PPTX) format.

#### Request Body

```json
{
  "presentation_url": "string (required)",
  "slide_count": "integer (required)",
  "aspect_ratio": "string (optional, default: '16:9')",
  "quality": "string (optional, default: 'high')"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `presentation_url` | string | Yes | - | Full URL to presentation viewer |
| `slide_count` | integer | Yes | - | Number of slides in the presentation (must be > 0) |
| `aspect_ratio` | string | No | `"16:9"` | Slide aspect ratio: `"16:9"` or `"4:3"` |
| `quality` | string | No | `"high"` | Image quality: `"high"`, `"medium"`, or `"low"` |

#### Response

**Success**: `200 OK`

- **Content-Type**: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- **Content-Disposition**: `attachment; filename="presentation-{id}.pptx"`
- **Body**: Binary PPTX file

**Error**: `500 Internal Server Error`

```json
{
  "detail": "PPTX conversion failed: {error message}"
}
```

#### Quality Settings

| Quality | Resolution | File Size (7 slides) | Use Case |
|---------|-----------|---------------------|----------|
| `high` | 1920×1080 | ~3-5MB | Final deliverables |
| `medium` | 1440×810 | ~2-3MB | Email-friendly |
| `low` | 960×540 | ~1-2MB | Quick sharing |

#### Aspect Ratio Options

- **`16:9`**: Widescreen (10" × 5.625") - Standard for modern presentations
- **`4:3`**: Traditional (10" × 7.5") - Legacy format

#### Example

```bash
# High quality, 16:9 PPTX
curl -X POST http://localhost:8010/convert/pptx \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/abc123",
    "slide_count": 7,
    "aspect_ratio": "16:9",
    "quality": "high"
  }' \
  -o presentation.pptx

# 4:3 aspect ratio, medium quality
curl -X POST http://localhost:8010/convert/pptx \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "https://v75-main.railway.app/p/abc123",
    "slide_count": 10,
    "aspect_ratio": "4:3",
    "quality": "medium"
  }' \
  -o presentation-4x3.pptx
```

---

## Request Models

### PDFConversionRequest

```json
{
  "presentation_url": "string",
  "landscape": true,
  "print_background": true,
  "quality": "high"
}
```

**Validation**:
- `presentation_url`: Must be a valid URL string
- `landscape`: Boolean value
- `print_background`: Boolean value
- `quality`: Must be one of: `"high"`, `"medium"`, `"low"`

### PPTXConversionRequest

```json
{
  "presentation_url": "string",
  "slide_count": 7,
  "aspect_ratio": "16:9",
  "quality": "high"
}
```

**Validation**:
- `presentation_url`: Must be a valid URL string
- `slide_count`: Must be an integer > 0
- `aspect_ratio`: Must be one of: `"16:9"`, `"4:3"`
- `quality`: Must be one of: `"high"`, `"medium"`, `"low"`

---

## Response Formats

### Success Responses

#### File Download (PDF/PPTX)

**Status Code**: `200 OK`

**Headers**:
```
Content-Type: application/pdf
  OR
Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation

Content-Disposition: attachment; filename="presentation-{id}.pdf"
  OR
Content-Disposition: attachment; filename="presentation-{id}.pptx"
```

**Body**: Binary file content (streamed)

#### Health Check

**Status Code**: `200 OK`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "status": "healthy",
  "playwright": "ready",
  "converters": {
    "pdf": "operational",
    "pptx": "operational"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|------------|---------|---------------|
| `200` | Success | Request completed successfully |
| `422` | Validation Error | Invalid request parameters |
| `500` | Internal Server Error | Conversion failed, Playwright error |
| `503` | Service Unavailable | Playwright not installed or unavailable |

### Common Errors

#### Invalid Presentation URL

**Status**: `500 Internal Server Error`

```json
{
  "detail": "PDF conversion failed: Failed to load presentation: abc123"
}
```

**Cause**: Presentation URL is inaccessible or presentation doesn't exist

**Solution**: Verify the presentation exists and URL is correct

#### Playwright Not Available

**Status**: `500 Internal Server Error`

```json
{
  "detail": "PDF conversion failed: Browser not found"
}
```

**Cause**: Chromium browser not installed

**Solution**: Run `playwright install --with-deps chromium`

#### Invalid Quality Setting

**Status**: `422 Validation Error`

```json
{
  "detail": [
    {
      "loc": ["body", "quality"],
      "msg": "value is not a valid enumeration member; permitted: 'high', 'medium', 'low'",
      "type": "type_error.enum"
    }
  ]
}
```

**Cause**: Quality parameter must be one of the allowed values

**Solution**: Use `"high"`, `"medium"`, or `"low"`

#### Missing Required Field

**Status**: `422 Validation Error`

```json
{
  "detail": [
    {
      "loc": ["body", "slide_count"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Cause**: Required field missing from request

**Solution**: Include all required fields in request body

---

## Quality Settings

### PDF Quality Comparison

| Quality | Viewport | PDF Dimensions | File Size | Generation Time |
|---------|----------|----------------|-----------|-----------------|
| High | 1920×1080 | 16"×9" (true 16:9) | ~500KB-2MB | ~8-12 seconds |
| Medium | 1440×810 | 16"×9" (true 16:9) | ~300KB-1MB | ~5-8 seconds |
| Low | 960×540 | 16"×9" (true 16:9) | ~150KB-500KB | ~3-5 seconds |

**Note**: All PDFs are generated using Reveal.js print-pdf mode for optimal layout. Debug UI elements (badges, controls) are automatically hidden.

### PPTX Quality Comparison

| Quality | Screenshot Resolution | File Size (per slide) | Generation Time |
|---------|---------------------|---------------------|-----------------|
| High | 1920×1080 | ~400-700KB | ~2 seconds |
| Medium | 1440×810 | ~250-400KB | ~1.5 seconds |
| Low | 960×540 | ~150-250KB | ~1 second |

**Note**: PPTX files use screenshot-based slides, so text is not editable in PowerPoint.

---

## Examples

### Example 1: Python with httpx

```python
import httpx
import asyncio

async def convert_presentation():
    # Service URLs
    download_service = "http://localhost:8010"
    presentation_url = "http://localhost:8504/p/abc123"

    # Convert to PDF
    async with httpx.AsyncClient(timeout=60.0) as client:
        pdf_response = await client.post(
            f"{download_service}/convert/pdf",
            json={
                "presentation_url": presentation_url,
                "landscape": True,
                "print_background": True,
                "quality": "high"
            }
        )

        if pdf_response.status_code == 200:
            with open("output.pdf", "wb") as f:
                f.write(pdf_response.content)
            print(f"PDF saved: {len(pdf_response.content)} bytes")
        else:
            print(f"Error: {pdf_response.json()}")

    # Convert to PPTX
    async with httpx.AsyncClient(timeout=60.0) as client:
        pptx_response = await client.post(
            f"{download_service}/convert/pptx",
            json={
                "presentation_url": presentation_url,
                "slide_count": 7,
                "aspect_ratio": "16:9",
                "quality": "high"
            }
        )

        if pptx_response.status_code == 200:
            with open("output.pptx", "wb") as f:
                f.write(pptx_response.content)
            print(f"PPTX saved: {len(pptx_response.content)} bytes")
        else:
            print(f"Error: {pptx_response.json()}")

# Run
asyncio.run(convert_presentation())
```

### Example 2: JavaScript with fetch

```javascript
async function convertPresentation() {
  const downloadService = 'http://localhost:8010';
  const presentationUrl = 'http://localhost:8504/p/abc123';

  try {
    // Convert to PDF
    const pdfResponse = await fetch(`${downloadService}/convert/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        presentation_url: presentationUrl,
        landscape: true,
        print_background: true,
        quality: 'high'
      })
    });

    if (pdfResponse.ok) {
      const pdfBlob = await pdfResponse.blob();
      const url = window.URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'presentation.pdf';
      a.click();
      console.log('PDF downloaded');
    } else {
      const error = await pdfResponse.json();
      console.error('PDF error:', error);
    }

    // Convert to PPTX
    const pptxResponse = await fetch(`${downloadService}/convert/pptx`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        presentation_url: presentationUrl,
        slide_count: 7,
        aspect_ratio: '16:9',
        quality: 'high'
      })
    });

    if (pptxResponse.ok) {
      const pptxBlob = await pptxResponse.blob();
      const url = window.URL.createObjectURL(pptxBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'presentation.pptx';
      a.click();
      console.log('PPTX downloaded');
    } else {
      const error = await pptxResponse.json();
      console.error('PPTX error:', error);
    }

  } catch (error) {
    console.error('Request failed:', error);
  }
}

// Call the function
convertPresentation();
```

### Example 3: curl Commands

```bash
# Get health status
curl http://localhost:8010/health

# Download PDF (high quality, landscape)
curl -X POST http://localhost:8010/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/abc123",
    "landscape": true,
    "print_background": true,
    "quality": "high"
  }' \
  -o presentation.pdf

# Download PPTX (16:9, high quality)
curl -X POST http://localhost:8010/convert/pptx \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/abc123",
    "slide_count": 7,
    "aspect_ratio": "16:9",
    "quality": "high"
  }' \
  -o presentation.pptx

# Medium quality PDF (smaller file size)
curl -X POST http://localhost:8010/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_url": "http://localhost:8504/p/abc123",
    "quality": "medium"
  }' \
  -o presentation-medium.pdf
```

---

## Rate Limits

**Current Version**: No rate limiting

For production deployments, consider:
- **Rate Limit**: 100 requests per minute per IP
- **Concurrent Conversions**: 10 simultaneous conversions
- **File Size Limits**: Max 50MB per output file
- **Timeout**: 60 seconds per conversion

---

## Integration Guide

### Complete Workflow

```python
import httpx

async def create_and_download_presentation():
    """
    Complete workflow: Create presentation → Download PDF/PPTX
    """

    # Step 1: Create presentation via v7.5-main
    v75_main = "https://v75-main.railway.app"
    download_service = "https://v75-downloads.railway.app"

    async with httpx.AsyncClient() as client:
        # Create presentation
        create_response = await client.post(
            f"{v75_main}/api/presentations",
            json={
                "title": "My Presentation",
                "slides": [
                    {
                        "layout": "L29",
                        "content": {
                            "hero_content": "<div>Slide 1</div>"
                        }
                    },
                    # ... more slides
                ]
            }
        )

        presentation_data = create_response.json()
        presentation_id = presentation_data["id"]
        presentation_url = f"{v75_main}/p/{presentation_id}"

        print(f"Created presentation: {presentation_id}")
        print(f"View URL: {presentation_url}")

    # Step 2: Convert to PDF
    async with httpx.AsyncClient(timeout=60.0) as client:
        pdf_response = await client.post(
            f"{download_service}/convert/pdf",
            json={
                "presentation_url": presentation_url,
                "quality": "high"
            }
        )

        if pdf_response.status_code == 200:
            pdf_bytes = pdf_response.content
            print(f"PDF generated: {len(pdf_bytes)} bytes")
        else:
            print(f"PDF error: {pdf_response.json()}")

    # Step 3: Convert to PPTX
    slide_count = len(slides)
    async with httpx.AsyncClient(timeout=60.0) as client:
        pptx_response = await client.post(
            f"{download_service}/convert/pptx",
            json={
                "presentation_url": presentation_url,
                "slide_count": slide_count,
                "quality": "high"
            }
        )

        if pptx_response.status_code == 200:
            pptx_bytes = pptx_response.content
            print(f"PPTX generated: {len(pptx_bytes)} bytes")
        else:
            print(f"PPTX error: {pptx_response.json()}")

    return {
        "presentation_id": presentation_id,
        "presentation_url": presentation_url,
        "pdf_bytes": pdf_bytes,
        "pptx_bytes": pptx_bytes
    }
```

### Error Handling Best Practices

```python
async def safe_convert_to_pdf(presentation_url, max_retries=3):
    """
    Convert with retry logic and error handling
    """
    download_service = "https://v75-downloads.railway.app"

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{download_service}/convert/pdf",
                    json={
                        "presentation_url": presentation_url,
                        "quality": "high"
                    }
                )

                if response.status_code == 200:
                    return response.content
                else:
                    error = response.json()
                    print(f"Attempt {attempt + 1} failed: {error}")

        except httpx.TimeoutException:
            print(f"Attempt {attempt + 1} timed out")
        except httpx.RequestError as e:
            print(f"Attempt {attempt + 1} request error: {e}")

        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    raise Exception("PDF conversion failed after all retries")
```

---

## Performance

### Typical Response Times

| Operation | Slides | Quality | Time |
|-----------|--------|---------|------|
| PDF Generation | 5 | High | ~8s |
| PDF Generation | 10 | High | ~12s |
| PDF Generation | 20 | High | ~20s |
| PPTX Generation | 5 | High | ~10s |
| PPTX Generation | 10 | High | ~18s |
| PPTX Generation | 20 | High | ~35s |

**Note**: Times include browser launch, page navigation, rendering, and conversion.

### Optimization Tips

1. **Use Medium Quality** for faster conversions when high fidelity isn't critical
2. **Parallel Requests**: PDF and PPTX conversions can run in parallel
3. **Connection Pooling**: Reuse HTTP connections for multiple conversions
4. **Timeout Settings**: Set appropriate timeouts (60s recommended for 20+ slides)

---

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/Pramod-Potti-Krishnan/deck-downloads-v7.5/issues
- **Documentation**: See README.md

---

## Changelog

### Version 1.0.0 (2025-11-10)

- Initial release
- PDF conversion with quality control
- PPTX conversion with aspect ratio support
- Playwright-based rendering
- RESTful API
- Health check endpoints
- Comprehensive error handling

---

## License

Internal use only.

---

**Last Updated**: 2025-11-10
