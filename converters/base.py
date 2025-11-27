"""
Base converter class with shared screenshot capture logic.

This module provides the foundation for PDF and PPTX converters,
including browser automation with Playwright for capturing slide screenshots.
"""

import asyncio
import logging
import os
from typing import List, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, ViewportSize

logger = logging.getLogger(__name__)


class BaseConverter:
    """Base class for presentation converters with shared screenshot capture."""

    # Standard presentation dimensions
    SLIDE_WIDTH = 1920
    SLIDE_HEIGHT = 1080

    def __init__(self, base_url: str = None):
        """
        Initialize the base converter.

        Args:
            base_url: Base URL where the presentation server is running.
                     If None, will use http://localhost:{PORT} from environment.
        """
        if base_url is None:
            port = os.getenv("PORT", "8009")
            base_url = f"http://localhost:{port}"
        self.base_url = base_url
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def _init_browser(self) -> None:
        """Initialize Playwright browser and page."""
        if self._browser is not None:
            return

        logger.info("Initializing Playwright browser...")
        playwright = await async_playwright().start()

        # Launch browser in headless mode
        self._browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process']
        )

        # Create browser context with presentation viewport
        context = await self._browser.new_context(
            viewport=ViewportSize(
                width=self.SLIDE_WIDTH,
                height=self.SLIDE_HEIGHT
            ),
            device_scale_factor=2  # High DPI for better quality
        )

        self._page = await context.new_page()
        logger.info("Browser initialized successfully")

    async def _close_browser(self) -> None:
        """Close Playwright browser and cleanup."""
        if self._browser:
            logger.info("Closing browser...")
            await self._browser.close()
            self._browser = None
            self._page = None

    async def capture_slide_screenshots(
        self,
        presentation_id: str,
        slide_count: Optional[int] = None
    ) -> List[bytes]:
        """
        Capture screenshots of all slides in a presentation.

        Args:
            presentation_id: The UUID of the presentation
            slide_count: Number of slides in the presentation

        Returns:
            List of screenshot bytes (PNG format) for each slide

        Raises:
            ValueError: If presentation cannot be loaded
            RuntimeError: If screenshot capture fails
        """
        await self._init_browser()

        screenshots = []
        url = f"{self.base_url}/p/{presentation_id}"

        try:
            logger.info(f"Navigating to presentation: {url}")

            # Navigate to presentation viewer
            response = await self._page.goto(url, wait_until='networkidle')

            if not response or response.status != 200:
                raise ValueError(f"Failed to load presentation: {presentation_id}")

            # Wait for Reveal.js to initialize
            await self._page.wait_for_selector('.reveal.ready', timeout=10000)
            logger.info("Reveal.js initialized")

            # Inject CSS to hide UI elements for clean screenshots
            await self._page.add_style_tag(content="""
                #help-text,
                #toggle-edit-mode,
                #edit-controls,
                #edit-notification,
                .edit-shortcuts,
                #toggle-review-mode,
                #selection-indicator,
                #regeneration-panel,
                .reveal .controls,
                .reveal .progress,
                .reveal .slide-number,
                .grid-overlay {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                }
                
                /* Ensure background is white */
                body, .reveal {
                    background-color: white !important;
                }
            """)
            logger.info("Injected CSS to hide UI elements")

            # If slide_count is missing, fetch it from Reveal.js
            if slide_count is None:
                logger.info("Slide count not provided, detecting from presentation...")
                slide_count = await self._page.evaluate("Reveal.getTotalSlides()")
                logger.info(f"Detected {slide_count} slides")

            # Capture each slide
            for slide_index in range(slide_count):
                logger.info(f"Capturing slide {slide_index + 1}/{slide_count}")

                # Navigate to specific slide using Reveal.js API
                await self._page.evaluate(f"Reveal.slide({slide_index}, 0)")

                # Wait for slide transition to complete
                await asyncio.sleep(0.5)

                # Wait for any images or content to load
                await self._page.wait_for_load_state('networkidle', timeout=5000)

                # Capture screenshot of the full viewport
                # We use full_page=False to capture exactly the viewport size (1920x1080)
                screenshot = await self._page.screenshot(
                    type='png',
                    full_page=False,
                    scale='device'  # Use device scale factor (2x for high DPI)
                )

                screenshots.append(screenshot)
                logger.info(f"Slide {slide_index + 1} captured ({len(screenshot)} bytes)")

            logger.info(f"Successfully captured {len(screenshots)} slides")
            return screenshots

        except Exception as e:
            logger.error(f"Error capturing screenshots: {e}", exc_info=True)
            raise RuntimeError(f"Screenshot capture failed: {e}") from e

        finally:
            await self._close_browser()

    async def _wait_for_reveal_ready(self, timeout: int = 10000) -> None:
        """
        Wait for Reveal.js to be fully initialized and ready.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        await self._page.wait_for_function(
            "typeof Reveal !== 'undefined' && Reveal.isReady()",
            timeout=timeout
        )

    def _get_slide_dimensions(self) -> tuple[int, int]:
        """
        Get the standard slide dimensions.

        Returns:
            Tuple of (width, height) in pixels
        """
        return (self.SLIDE_WIDTH, self.SLIDE_HEIGHT)
