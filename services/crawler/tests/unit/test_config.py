import pytest
from unittest.mock import patch


class TestCrawlerConfig:

    @pytest.mark.unit
    def test_default_settings(self):
        from crawler.config import CrawlerSettings

        settings = CrawlerSettings()
        assert settings.backend_url == "http://localhost:8000"
        assert settings.max_concurrent_pages == 5
        assert settings.request_timeout_ms == 30000
        assert settings.poll_interval_seconds == 60
        assert settings.log_level == "info"

    @pytest.mark.unit
    def test_settings_from_env(self):
        from crawler.config import CrawlerSettings

        with patch.dict("os.environ", {"BACKEND_URL": "http://backend:9000", "MAX_CONCURRENT_PAGES": "10"}):
            settings = CrawlerSettings()
            assert settings.backend_url == "http://backend:9000"
            assert settings.max_concurrent_pages == 10

    @pytest.mark.unit
    def test_get_settings_returns_instance(self):
        from crawler.config import get_settings, CrawlerSettings

        settings = get_settings()
        assert isinstance(settings, CrawlerSettings)
