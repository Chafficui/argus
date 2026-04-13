# =============================================================================
# crawler/config.py
# =============================================================================
# Configuration for the crawler service.
# Reads from environment variables with sensible dev defaults.
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class CrawlerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # The backend API URL — crawler sends fetched documents here for processing
    backend_url: str = "http://localhost:8000"

    # Concurrency limits
    max_concurrent_pages: int = 5

    # Request timeout in milliseconds
    request_timeout_ms: int = 30000

    # How often to poll for sources that need crawling (seconds)
    poll_interval_seconds: int = 60

    # Logging
    log_level: str = "info"


@lru_cache()
def get_settings() -> CrawlerSettings:
    return CrawlerSettings()
