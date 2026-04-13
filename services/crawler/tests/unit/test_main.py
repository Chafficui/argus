import pytest
from unittest.mock import patch, AsyncMock


class TestCrawlerMain:

    @pytest.mark.unit
    def test_handle_signal_sets_shutdown_flag(self):
        from crawler.main import handle_signal
        import crawler.main

        assert crawler.main._shutdown is False
        handle_signal(2, None)  # SIGINT
        assert crawler.main._shutdown is True
        # Reset for other tests
        crawler.main._shutdown = False

    @pytest.mark.unit
    async def test_async_main_starts_scheduler(self):
        """async_main should create a BackendClient and call run_scheduler."""
        with patch("crawler.main.run_scheduler", AsyncMock()) as mock_sched, \
             patch("crawler.main.BackendClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            await __import__("crawler.main", fromlist=["async_main"]).async_main()

            mock_client_cls.assert_called_once()
            mock_sched.assert_called_once()
            mock_client.close.assert_called_once()

    @pytest.mark.unit
    async def test_async_main_closes_client_on_error(self):
        """Client should be closed even if the scheduler raises."""
        with patch("crawler.main.run_scheduler", AsyncMock(side_effect=Exception("boom"))), \
             patch("crawler.main.BackendClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception, match="boom"):
                await __import__("crawler.main", fromlist=["async_main"]).async_main()

            mock_client.close.assert_called_once()
