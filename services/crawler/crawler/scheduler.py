# =============================================================================
# crawler/scheduler.py
# =============================================================================
# Runs the crawl cycle on a configurable interval.
# Uses a simple async sleep loop — no heavyweight scheduler library needed.
#
# Interval starts AFTER the previous cycle completes, not wall-clock.
# This prevents overlap if a cycle takes longer than the interval.
# =============================================================================

import asyncio
import time

import structlog

from crawler.backend_client import BackendClient
from crawler.runner import run_crawl_cycle

log = structlog.get_logger()


async def run_scheduler(client: BackendClient, interval_seconds: int) -> None:
    """
    Run crawl cycles on a fixed interval.
    Loops forever until the process is killed or an unrecoverable error occurs.
    """
    log.info("Crawler scheduler started", interval_seconds=interval_seconds)

    while True:
        start = time.monotonic()
        try:
            await run_crawl_cycle(client)
        except Exception as e:
            log.error("Crawl cycle failed", error=str(e))

        elapsed = time.monotonic() - start
        sleep_for = max(0, interval_seconds - elapsed)
        log.info(
            "Next crawl cycle scheduled",
            elapsed_seconds=round(elapsed, 1),
            next_in_seconds=round(sleep_for),
        )
        await asyncio.sleep(sleep_for)
