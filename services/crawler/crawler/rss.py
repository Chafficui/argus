# =============================================================================
# crawler/rss.py
# =============================================================================
# RSS/Atom feed parser — extracts article URLs from feed XML.
#
# Each entry URL gets passed to smart_fetch() to get the full article HTML.
# We don't use the RSS summary text because it's usually truncated or
# stripped of formatting — the full page is much better for RAG.
# =============================================================================

import feedparser
import structlog

log = structlog.get_logger()

MAX_ENTRIES = 20


async def fetch_rss_entries(feed_url: str) -> list[dict]:
    """
    Parse an RSS/Atom feed and return up to 20 entries.
    feedparser is synchronous but fast enough — no need for async.
    """
    feed = feedparser.parse(feed_url)

    if feed.bozo and not feed.entries:
        log.warning("Failed to parse feed", url=feed_url, error=str(feed.bozo_exception))
        return []

    entries = [
        {
            "url": entry.link,
            "title": entry.get("title", ""),
            "published_at": entry.get("published", None),
        }
        for entry in feed.entries[:MAX_ENTRIES]
        if hasattr(entry, "link") and entry.link
    ]

    log.info("Parsed RSS feed", url=feed_url, entries=len(entries))
    return entries
