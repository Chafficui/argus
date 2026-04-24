import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from crawler.scheduler import run_scheduler


class TestRunScheduler:

    @pytest.mark.unit
    async def test_polls_and_crawls_due_sources(self):
        """Scheduler should poll for sources, find due ones, and crawl them."""
        client = AsyncMock()
        client.get_active_sources = AsyncMock(return_value=[
            {"id": "s1", "source_type": "rss", "url": "https://example.com/rss", "last_crawled_at": None, "crawl_interval_minutes": 360},
        ])

        crawled_ids = []

        async def mock_crawl(c, source):
            from crawler.runner import CrawlResult
            crawled_ids.append(source["id"])
            return CrawlResult(source_id=source["id"], ingested=1)

        async def mock_sleep(seconds):
            raise asyncio.CancelledError()

        with patch("crawler.scheduler.crawl_source", side_effect=mock_crawl), \
             patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=60, poll_seconds=30)

        assert crawled_ids == ["s1"]

    @pytest.mark.unit
    async def test_skips_recently_crawled_sources(self):
        """Sources crawled recently should not be crawled again."""
        from datetime import datetime, timezone
        client = AsyncMock()
        client.get_active_sources = AsyncMock(return_value=[
            {"id": "s1", "source_type": "rss", "url": "https://example.com/rss",
             "last_crawled_at": datetime.now(timezone.utc).isoformat(), "crawl_interval_minutes": 360},
        ])

        crawled_ids = []

        async def mock_crawl(c, source):
            from crawler.runner import CrawlResult
            crawled_ids.append(source["id"])
            return CrawlResult(source_id=source["id"])

        async def mock_sleep(seconds):
            raise asyncio.CancelledError()

        with patch("crawler.scheduler.crawl_source", side_effect=mock_crawl), \
             patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=60, poll_seconds=30)

        assert crawled_ids == []

    @pytest.mark.unit
    async def test_continues_after_poll_error(self):
        """If polling fails, the scheduler should log and continue."""
        client = AsyncMock()

        poll_count = 0

        async def failing_then_ok():
            nonlocal poll_count
            poll_count += 1
            if poll_count == 1:
                raise Exception("network down")
            return []

        client.get_active_sources = AsyncMock(side_effect=failing_then_ok)

        async def mock_sleep(seconds):
            if poll_count >= 2:
                raise asyncio.CancelledError()

        with patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=1, poll_seconds=1)

        assert poll_count == 2
