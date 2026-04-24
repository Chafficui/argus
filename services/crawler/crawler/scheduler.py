# =============================================================================
# crawler/scheduler.py
# =============================================================================
# Polls for sources that need crawling on a short interval.
# A source is "due" if it has never been crawled (last_crawled_at is null)
# or if enough time has passed since the last crawl (based on
# crawl_interval_minutes per source).
# =============================================================================

import asyncio
from datetime import datetime, timezone

import structlog

from crawler.backend_client import BackendClient
from crawler.runner import crawl_source

log = structlog.get_logger()


def _is_due(source: dict) -> bool:
    """Check if a source needs crawling now."""
    last = source.get("last_crawled_at")
    if not last:
        return True
    last_dt = datetime.fromisoformat(last)
    interval = source.get("crawl_interval_minutes", 360) * 60
    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
    return elapsed >= interval


async def run_scheduler(client: BackendClient, interval_seconds: int, poll_seconds: int = 60) -> None:
    """
    Poll for sources that need crawling every poll_seconds.
    Each poll, only crawl sources that are actually due.
    """
    log.info("Crawler scheduler started", poll_seconds=poll_seconds)

    while True:
        try:
            sources = await client.get_active_sources()
            due = [s for s in sources if _is_due(s)]

            if due:
                log.info("Sources due for crawling", total=len(sources), due=len(due))
                for source in due:
                    try:
                        result = await crawl_source(client, source)
                        log.info(
                            "Source crawled",
                            source_id=result.source_id,
                            status=result.status,
                            ingested=result.ingested,
                            failed=result.failed,
                            duration=round(result.duration_seconds, 1),
                        )
                    except Exception as e:
                        log.error("Source crawl failed", source_id=source["id"], error=str(e))
        except Exception as e:
            log.error("Poll cycle failed", error=str(e))

        await asyncio.sleep(poll_seconds)
