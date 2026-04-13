# =============================================================================
# app/core/config.py
# =============================================================================
# This file defines ALL configuration for the backend.
#
# pydantic-settings automatically reads values from environment variables.
# So if you set POSTGRES_HOST=myserver in the environment (or K8s values.yaml),
# it's available as settings.postgres_host in Python code — no manual os.getenv().
#
# Priority (highest to lowest):
#   1. Environment variables (from K8s Secret / values.yaml)
#   2. .env file (for local development)
#   3. Default values defined here
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Tell pydantic-settings to also read from a .env file if it exists
    # (useful for local dev without K8s)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    app_name: str = "Argus"
    app_version: str = "0.1.0"
    log_level: str = "info"

    # In production this should be "production" — some features behave differently
    environment: str = "development"

    # Secret key for signing internal tokens (NOT the Keycloak secret)
    # Must be at least 32 characters. Generate with: openssl rand -hex 32
    secret_key: str = "dev-secret-key-change-in-prod-minimum-32-chars"

    # -------------------------------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------------------------------
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "argus"
    postgres_user: str = "argus"
    postgres_password: str = "argus-dev-password"

    @property
    def postgres_url(self) -> str:
        # asyncpg uses postgresql+asyncpg:// prefix
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # -------------------------------------------------------------------------
    # Milvus (Vector Database)
    # -------------------------------------------------------------------------
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "argus_documents"

    # Embedding dimension — depends on which embedding model you use.
    # nomic-embed-text (via Ollama) produces 768-dimensional vectors.
    # text-embedding-3-small (OpenAI) produces 1536-dimensional vectors.
    embedding_dimension: int = 768

    # -------------------------------------------------------------------------
    # MinIO (Object Storage)
    # -------------------------------------------------------------------------
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "argus-minio"
    minio_secret_key: str = "argus-minio-secret"
    minio_secure: bool = False  # Set True in prod (HTTPS)
    minio_bucket_raw: str = "argus-raw-docs"
    minio_bucket_processed: str = "argus-processed"

    # -------------------------------------------------------------------------
    # Ollama (Local LLM)
    # -------------------------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    # -------------------------------------------------------------------------
    # Keycloak (Auth / IAM)
    # -------------------------------------------------------------------------
    keycloak_url: str = "http://localhost:8080/realms/argus"

    @property
    def keycloak_jwks_url(self) -> str:
        # JWKS = JSON Web Key Set — the public keys Keycloak uses to sign tokens.
        # Our backend fetches these to verify that a JWT was really issued by Keycloak.
        # This is the standard OIDC endpoint — always at /.well-known/jwks.json
        return f"{self.keycloak_url}/protocol/openid-connect/certs"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_url}/protocol/openid-connect/token"

    # The "audience" claim in the JWT — must match what Keycloak is configured to issue
    keycloak_audience: str = "argus-backend"

    # -------------------------------------------------------------------------
    # Dev auth bypass
    # -------------------------------------------------------------------------
    # When True AND environment=="development", skip JWT validation entirely.
    # NEVER enable in production — the double check prevents accidental use.
    dev_auth_bypass: bool = False

    # -------------------------------------------------------------------------
    # Crawler
    # -------------------------------------------------------------------------
    max_sources_per_user: int = 50
    crawl_timeout_seconds: int = 30


# lru_cache means this function is only called ONCE — settings are a singleton.
# Every part of the app that calls get_settings() gets the same object.
@lru_cache()
def get_settings() -> Settings:
    return Settings()
