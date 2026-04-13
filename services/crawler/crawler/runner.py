# =============================================================================
# crawler/runner.py
# =============================================================================
# The main crawl loop. Fetches all active sources from the backend, crawls
# each one based on its type (website, RSS, or SERP), and sends content to
# /api/ingest/. Handles errors per-source without stopping the whole cycle.
# Reports CrawlJob results to the backend for audit and monitoring.
# =============================================================================

import time
from dataclasses import dataclass

import structlog

from crawler.backend_client import BackendClient
from crawler.config import get_settings
from crawler.fetcher import smart_fetch
from crawler.rss import fetch_rss_entries
from crawler.serp import fetch_serp_results

log = structlog.get_logger()


@dataclass
class CrawlResult:
    source_id: str
    status: str = "success"
    ingested: int = 0
    failed: int = 0
    error_message: str | None = None
    duration_seconds: float = 0.0


async def crawl_source(client: BackendClient, source: dict) -> CrawlResult:
    """Crawl a single source. Returns result with status + stats."""
    source_id = source["id"]
    source_type = source["source_type"]
    start = time.monotonic()
    result = CrawlResult(source_id=source_id)

    try:
        if source_type == "rss":
            entries = await fetch_rss_entries(source["url"])
            urls_to_fetch = [e["url"] for e in entries]
            titles = {e["url"]: e.get("title") for e in entries}
        elif source_type == "serp":
            settings = get_settings()
            entries = await fetch_serp_results(
                query=source["search_query"],
                searxng_url=settings.searxng_url,
            )
            urls_to_fetch = [e["url"] for e in entries]
            titles = {e["url"]: e.get("title") for e in entries}
        else:  # website
            urls_to_fetch = [source["url"]]
            titles = {}

        for url in urls_to_fetch:
            try:
                html = await smart_fetch(url)
                await client.ingest(
                    source_id=source_id,
                    url=url,
                    html=html,
                    title=titles.get(url),
                )
                result.ingested += 1
            except Exception as e:
                log.warning("Failed to fetch/ingest URL", url=url, error=str(e))
                result.failed += 1

    except Exception as e:
        result.status = "failed"
        result.error_message = str(e)
        log.error("Source crawl error", source_id=source_id, error=str(e))

    result.duration_seconds = time.monotonic() - start

    # Report crawl job and update last_crawled regardless of success/failure
    await client.report_crawl_job(
        source_id=source_id,
        crawl_status=result.status,
        documents_found=result.ingested + result.failed,
        documents_indexed=result.ingested,
        duration_seconds=result.duration_seconds,
        error_message=result.error_message,
    )
    await client.update_last_crawled(source_id)

    return result


async def run_crawl_cycle(client: BackendClient) -> list[CrawlResult]:
    """Fetch all active sources and crawl each one."""
    sources = await client.get_active_sources()
    log.info("Starting crawl cycle", source_count=len(sources))

    results = []
    for source in sources:
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
            results.append(result)
        except Exception as e:
            log.error("Source crawl failed", source_id=source["id"], error=str(e))

    log.info("Crawl cycle complete", sources_crawled=len(results))
    return results
