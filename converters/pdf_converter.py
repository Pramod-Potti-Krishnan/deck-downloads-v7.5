"""
PDF converter using Playwright's built-in PDF generation.

This module provides functionality to convert presentations to PDF format
using Playwright's native PDF export capabilities.
"""

import logging
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright
from .base import BaseConverter

logger = logging.getLogger(__name__)


class PDFConverter(BaseConverter):
    """Convert presentations to PDF format using Playwright."""

    async def generate_pdf(
        self,
        presentation_id: str,
        output_path: Optional[Path] = None,
        landscape: bool = True,
        print_background: bool = True,
        quality: str = "high"
    ) -> bytes:
        """
        Generate a PDF from a presentation.

        This method uses Playwright's built-in PDF generation to create
        a multi-page PDF directly from the presentation HTML using
        Reveal.js print-pdf mode for optimal rendering.

        Args:
            presentation_id: The UUID of the presentation
            output_path: Optional file path to save the PDF
            landscape: Whether to use landscape orientation (default: True)
            print_background: Include background graphics (default: True)
            quality: Quality setting - 'high', 'medium', or 'low'

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If presentation cannot be loaded
            RuntimeError: If PDF generation fails
        """
        logger.info(f"Generating PDF for presentation: {presentation_id}")

        # Initialize browser with appropriate settings
        playwright = await async_playwright().start()

        try:
            # Launch browser
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--disable-web-security']
            )

            # Create page with proper 16:9 viewport for presentations
            # Using higher resolution for better quality
            viewport_width = 1920 if quality == "high" else 1440 if quality == "medium" else 960
            viewport_height = 1080 if quality == "high" else 810 if quality == "medium" else 540

            page = await browser.new_page(
                viewport={'width': viewport_width, 'height': viewport_height}
            )

            # Build presentation URL with print-pdf parameter for Reveal.js
            # This enables Reveal.js print mode which layouts all slides for PDF
            url = f"{self.base_url}/p/{presentation_id}?print-pdf"
            logger.info(f"Navigating to: {url} (print-pdf mode)")

            # Navigate to presentation
            response = await page.goto(url, wait_until='networkidle', timeout=30000)

            if not response or response.status != 200:
                raise ValueError(f"Failed to load presentation: {presentation_id}")

            # Wait for Reveal.js to initialize
            await page.wait_for_selector('.reveal.ready', timeout=15000)
            logger.info("Reveal.js initialized successfully")

            # Inject CSS to hide debug UI elements
            await page.add_style_tag(content="""
                /* Hide all debug UI elements */
                .debug-badge,
                .reveal-controls,
                .reveal-progress,
                [class*='debug'],
                footer.controls,
                .controls-help,
                button[aria-label*='help'],
                button[aria-label*='overlay'],
                .badge,
                [style*='v7.5-main'] {
                    display: none !important;
                    visibility: hidden !important;
                }

                /* Ensure clean print output */
                @media print {
                    .debug-badge,
                    .reveal-controls,
                    .reveal-progress,
                    footer.controls {
                        display: none !important;
                    }
                }
            """)

            # Additional wait for any dynamic content and CSS to apply
            await page.wait_for_timeout(2000)

            # Set PDF dimensions based on quality
            scale = self._get_scale_factor(quality)

            # PDF options for true 16:9 aspect ratio
            pdf_options = {
                "landscape": landscape,
                "print_background": print_background,
                "scale": scale,
                "prefer_css_page_size": True,
                "margin": {
                    "top": "0px",
                    "right": "0px",
                    "bottom": "0px",
                    "left": "0px"
                }
            }

            # Set proper 16:9 dimensions (true aspect ratio)
            if landscape:
                # True 16:9 aspect ratio for presentation slides
                pdf_options["width"] = "16in"   # 16:9 ratio
                pdf_options["height"] = "9in"   # 16:9 ratio
            else:
                # Portrait mode (9:16)
                pdf_options["width"] = "9in"
                pdf_options["height"] = "16in"

            # Save to file if path provided
            if output_path:
                pdf_options["path"] = str(output_path)

            # Generate PDF
            logger.info(f"Generating PDF with quality: {quality}, landscape: {landscape}, dimensions: 16:9")
            pdf_bytes = await page.pdf(**pdf_options)

            logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes)")

            # Close browser
            await browser.close()
            await playwright.stop()

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            if 'browser' in locals():
                await browser.close()
            if 'playwright' in locals():
                await playwright.stop()
            raise RuntimeError(f"PDF generation failed: {e}") from e

    def _get_scale_factor(self, quality: str) -> float:
        """
        Get scale factor based on quality setting.

        Args:
            quality: Quality level - 'high', 'medium', or 'low'

        Returns:
            Scale factor for PDF generation
        """
        quality_map = {
            "high": 1.0,
            "medium": 0.85,
            "low": 0.7
        }
        return quality_map.get(quality, 1.0)

    async def generate_pdf_from_screenshots(
        self,
        presentation_id: str,
        slide_count: int,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Alternative method: Generate PDF from individual slide screenshots.

        This method captures each slide as a screenshot and combines them
        into a PDF. Useful if the direct PDF generation has issues with
        Reveal.js transitions.

        Args:
            presentation_id: The UUID of the presentation
            slide_count: Number of slides in the presentation
            output_path: Optional file path to save the PDF

        Returns:
            PDF file as bytes
        """
        from PIL import Image
        import io

        logger.info(f"Generating PDF from screenshots for: {presentation_id}")

        # Capture screenshots
        screenshots = await self.capture_slide_screenshots(presentation_id, slide_count)

        # Convert screenshots to images
        images = []
        for screenshot_bytes in screenshots:
            img = Image.open(io.BytesIO(screenshot_bytes))
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            images.append(img)

        # Save as PDF
        if images:
            pdf_buffer = io.BytesIO()

            # Save first image and append rest
            images[0].save(
                pdf_buffer,
                format='PDF',
                save_all=True,
                append_images=images[1:] if len(images) > 1 else [],
                resolution=100.0
            )

            pdf_bytes = pdf_buffer.getvalue()

            # Save to file if path provided
            if output_path:
                output_path.write_bytes(pdf_bytes)
                logger.info(f"PDF saved to: {output_path}")

            logger.info(f"PDF generated from {len(images)} screenshots ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        raise RuntimeError("No screenshots captured for PDF generation")
