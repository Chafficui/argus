# =============================================================================
# crawler/runner.py
# =============================================================================
# The main crawl loop. Fetches all active sources from the backend, crawls
# each one based on its type (website or RSS), and sends content to
# /api/ingest/. Handles errors per-source without stopping the whole cycle.
# =============================================================================

from dataclasses import dataclass, field

import structlog

from crawler.backend_client import BackendClient
from crawler.fetcher import smart_fetch
from crawler.rss import fetch_rss_entries

log = structlog.get_logger()


@dataclass
class CrawlResult:
    source_id: str
    ingested: int = 0
    failed: int = 0


async def crawl_source(client: BackendClient, source: dict) -> CrawlResult:
    """Crawl a single source. Returns result with status + stats."""
    source_id = source["id"]
    source_type = source["source_type"]

    if source_type == "rss":
        entries = await fetch_rss_entries(source["url"])
        urls_to_fetch = [e["url"] for e in entries]
        titles = {e["url"]: e.get("title") for e in entries}
    else:  # website
        urls_to_fetch = [source["url"]]
        titles = {}

    result = CrawlResult(source_id=source_id)

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
                ingested=result.ingested,
                failed=result.failed,
            )
            results.append(result)
        except Exception as e:
            log.error("Source crawl failed", source_id=source["id"], error=str(e))

    log.info("Crawl cycle complete", sources_crawled=len(results))
    return results
