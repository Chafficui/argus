import pytest
from unittest.mock import patch, MagicMock


class TestCrawlerMain:

    @pytest.mark.unit
    def test_main_runs_without_error(self):
        """The main function should run and log the scaffold message."""
        from crawler.main import main

        main()

    @pytest.mark.unit
    def test_handle_signal_sets_shutdown_flag(self):
        from crawler.main import handle_signal, _shutdown
        import crawler.main

        assert crawler.main._shutdown is False
        handle_signal(2, None)  # SIGINT
        assert crawler.main._shutdown is True
        # Reset for other tests
        crawler.main._shutdown = False
