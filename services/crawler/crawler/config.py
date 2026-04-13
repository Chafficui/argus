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

    # Auth token for backend API — in dev any string works with bypass active,
    # in prod this is a Keycloak service account token
    api_token: str = "dev"

    # Concurrency limits
    max_concurrent_pages: int = 5

    # Request timeout in milliseconds
    request_timeout_ms: int = 30000

    # How often to run a full crawl cycle (seconds). Default: 6 hours.
    crawl_interval_seconds: int = 21600

    # How often to poll for sources that need crawling (seconds)
    poll_interval_seconds: int = 60

    # SearXNG URL for SERP source type
    searxng_url: str = "http://localhost:8080"

    # Logging
    log_level: str = "info"


@lru_cache()
def get_settings() -> CrawlerSettings:
    return CrawlerSettings()
