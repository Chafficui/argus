import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from crawler.scheduler import run_scheduler


class TestRunScheduler:

    @pytest.mark.unit
    async def test_runs_cycle_then_sleeps(self):
        """Scheduler should run one crawl cycle and then sleep."""
        client = AsyncMock()

        call_order = []

        async def mock_crawl_cycle(c):
            call_order.append("crawl")

        async def mock_sleep(seconds):
            call_order.append(f"sleep({int(seconds)})")
            # Break the infinite loop after first sleep
            raise asyncio.CancelledError()

        with patch("crawler.scheduler.run_crawl_cycle", side_effect=mock_crawl_cycle), \
             patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=60)

        assert call_order[0] == "crawl"
        assert call_order[1].startswith("sleep(")

    @pytest.mark.unit
    async def test_sleeps_remaining_time_after_cycle(self):
        """If a cycle takes 10s and interval is 60s, sleep should be ~50s."""
        client = AsyncMock()

        sleep_value = None

        async def mock_crawl_cycle(c):
            pass  # instant — elapsed ≈ 0

        async def mock_sleep(seconds):
            nonlocal sleep_value
            sleep_value = seconds
            raise asyncio.CancelledError()

        with patch("crawler.scheduler.run_crawl_cycle", side_effect=mock_crawl_cycle), \
             patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=60)

        # Cycle was instant, so sleep should be close to the full interval
        assert sleep_value is not None
        assert 59 <= sleep_value <= 60

    @pytest.mark.unit
    async def test_continues_after_crawl_cycle_error(self):
        """If a crawl cycle raises, the scheduler should log and continue."""
        client = AsyncMock()

        cycle_count = 0

        async def failing_then_ok(c):
            nonlocal cycle_count
            cycle_count += 1
            if cycle_count == 1:
                raise Exception("network down")
            # Second call succeeds

        async def mock_sleep(seconds):
            if cycle_count >= 2:
                raise asyncio.CancelledError()

        with patch("crawler.scheduler.run_crawl_cycle", side_effect=failing_then_ok), \
             patch("crawler.scheduler.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(asyncio.CancelledError):
                await run_scheduler(client, interval_seconds=1)

        assert cycle_count == 2
