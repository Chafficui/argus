import pytest
from unittest.mock import patch, MagicMock

from crawler.rss import fetch_rss_entries


def _make_entry(link=None, title="Test Article", published="2026-01-15"):
    """Helper to create a mock feedparser entry."""
    entry = MagicMock()
    if link is not None:
        entry.link = link
    else:
        # Remove the link attribute entirely
        del entry.link
    entry.get = lambda k, default=None: {
        "title": title,
        "published": published,
    }.get(k, default)
    return entry


def _make_feed(entries, bozo=False, bozo_exception=None):
    """Helper to create a mock feedparser result."""
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = bozo
    feed.bozo_exception = bozo_exception
    return feed


class TestFetchRssEntries:

    @pytest.mark.unit
    async def test_parse_valid_feed_returns_entries(self):
        entries = [
            _make_entry(link=f"https://example.com/article-{i}", title=f"Article {i}")
            for i in range(3)
        ]
        mock_feed = _make_feed(entries)

        with patch("crawler.rss.feedparser.parse", return_value=mock_feed):
            result = await fetch_rss_entries("https://example.com/feed.xml")

        assert len(result) == 3
        assert result[0]["url"] == "https://example.com/article-0"
        assert result[0]["title"] == "Article 0"
        assert "published_at" in result[0]

    @pytest.mark.unit
    async def test_skips_entries_without_link(self):
        entries = [
            _make_entry(link="https://example.com/has-link"),
            _make_entry(link=None),  # No link — should be skipped
            _make_entry(link="https://example.com/also-has-link"),
        ]
        mock_feed = _make_feed(entries)

        with patch("crawler.rss.feedparser.parse", return_value=mock_feed):
            result = await fetch_rss_entries("https://example.com/feed.xml")

        assert len(result) == 2
        urls = [r["url"] for r in result]
        assert "https://example.com/has-link" in urls
        assert "https://example.com/also-has-link" in urls

    @pytest.mark.unit
    async def test_limits_to_20_entries(self):
        entries = [
            _make_entry(link=f"https://example.com/article-{i}")
            for i in range(30)
        ]
        mock_feed = _make_feed(entries)

        with patch("crawler.rss.feedparser.parse", return_value=mock_feed):
            result = await fetch_rss_entries("https://example.com/feed.xml")

        assert len(result) == 20

    @pytest.mark.unit
    async def test_empty_feed_returns_empty_list(self):
        mock_feed = _make_feed([])

        with patch("crawler.rss.feedparser.parse", return_value=mock_feed):
            result = await fetch_rss_entries("https://example.com/feed.xml")

        assert result == []

    @pytest.mark.unit
    async def test_bozo_feed_with_no_entries_returns_empty(self):
        mock_feed = _make_feed([], bozo=True, bozo_exception=Exception("malformed XML"))

        with patch("crawler.rss.feedparser.parse", return_value=mock_feed):
            result = await fetch_rss_entries("https://example.com/bad-feed.xml")

        assert result == []
