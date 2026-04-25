#!/usr/bin/env python3
# =============================================================================
# crawler/main.py
# =============================================================================
# Entry point for the Argus crawler service.
# Polls the backend for active sources, crawls their content, and sends it
# back to the backend for processing.
#
# Usage:
#   python -m crawler.main
# =============================================================================

import asyncio
import signal

import structlog

from crawler.backend_client import BackendClient
from crawler.config import get_settings
from crawler.logging_config import configure_logging
from crawler.scheduler import run_scheduler

settings = get_settings()
configure_logging(environment="production", log_level=settings.log_level)
log = structlog.get_logger()

# Graceful shutdown flag
_shutdown = False


def handle_signal(signum, frame):
    global _shutdown
    log.info("Shutdown signal received", signal=signum)
    _shutdown = True


async def async_main():
    settings = get_settings()
    log.info(
        "Argus Crawler starting",
        backend_url=settings.backend_url,
        crawl_interval_seconds=settings.crawl_interval_seconds,
    )

    client = BackendClient(
        base_url=settings.backend_url,
        api_token=settings.api_token,
        keycloak_url=settings.keycloak_url,
        keycloak_client_id=settings.keycloak_client_id,
        keycloak_client_secret=settings.keycloak_client_secret,
    )
    try:
        await run_scheduler(
            client,
            interval_seconds=settings.crawl_interval_seconds,
            poll_seconds=settings.poll_interval_seconds,
        )
    finally:
        await client.close()


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
