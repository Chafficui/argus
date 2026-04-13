#!/usr/bin/env python3
# =============================================================================
# crawler/main.py
# =============================================================================
# Entry point for the Argus crawler service.
# Polls the backend for sources due for crawling, fetches their content,
# and sends it back to the backend for processing.
#
# Usage:
#   python -m crawler.main
# =============================================================================

import signal
import sys
import structlog

from crawler.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# Graceful shutdown flag
_shutdown = False


def handle_signal(signum, frame):
    global _shutdown
    log.info("Shutdown signal received", signal=signum)
    _shutdown = True


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log.info(
        "Argus crawler starting",
        backend_url=settings.backend_url,
        poll_interval=settings.poll_interval_seconds,
        max_concurrent=settings.max_concurrent_pages,
    )

    # TODO: implement crawl loop
    # 1. GET /api/sources/?needs_crawl=true from backend
    # 2. For each source, fetch content (Playwright for JS, httpx for static)
    # 3. POST fetched HTML back to backend for processing
    # 4. Sleep for poll_interval_seconds

    log.info("Crawler scaffold ready — crawl loop not yet implemented")


if __name__ == "__main__":
    main()
