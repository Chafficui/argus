# =============================================================================
# crawler/serp.py
# =============================================================================
# SERP (Search Engine Results Page) aggregation via SearXNG.
# SearXNG is a self-hosted, privacy-respecting meta search engine.
# We query its JSON API and return result URLs + titles for crawling.
# =============================================================================

import httpx
import structlog

log = structlog.get_logger()

MAX_RESULTS = 10


async def fetch_serp_results(query: str, searxng_url: str) -> list[dict]:
    """
    Query SearXNG and return up to 10 result URLs with titles.
    Results are then fetched individually via smart_fetch.
    """
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{searxng_url.rstrip('/')}/search",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

    results = [
        {"url": r["url"], "title": r.get("title", "")}
        for r in data.get("results", [])[:MAX_RESULTS]
        if "url" in r
    ]

    log.info("Fetched SERP results", query=query, results=len(results))
    return results
