#!/usr/bin/env python3
"""
v7.5 Presentation Download Service
===================================

Microservice for converting v7.5-main presentations to PDF and PPTX formats.

This service:
- Receives presentation URLs from v7.5-main
- Uses Playwright to capture slides
- Converts to PDF or PPTX format
- Returns downloadable files

Port: 8010 (default)
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 v7.5 Download Service Starting...")
    logger.info("=" * 60)

    try:
        from server import run_server
        run_server()
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}", exc_info=True)
        sys.exit(1)
