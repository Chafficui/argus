# =============================================================================
# tests/conftest.py
# =============================================================================
# Fixtures shared across all tests.
#
# WHAT IS A FIXTURE?
# A fixture is a reusable piece of test setup/teardown.
# Instead of copy-pasting "create a DB connection" in every test,
# you define it once here and inject it via function arguments.
#
# Example:
#   def test_something(db_session, test_client):
#                       ^^         ^^^^^^^^^^^
#                       fixtures are injected automatically by pytest
#
# SCOPE:
#   scope="function" → created/destroyed for each test (default, safest)
#   scope="session"  → created once for the entire test run (faster, shared state)
#   scope="module"   → created once per test file
# =============================================================================

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock
from faker import Faker

from app.main import app
from app.db.database import get_db
from app.core.auth import verify_token
from app.core.config import get_settings
from app.models.models import Base

fake = Faker("en_US")  # English locale for realistic test data


# =============================================================================
# SETTINGS OVERRIDE
# We override settings for tests so they don't accidentally hit production DBs
# =============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for test environment."""
    settings = get_settings()
    settings.environment = "test"
    settings.log_level = "warning"  # Less noise in test output
    return settings


# =============================================================================
# IN-MEMORY DATABASE (for unit tests)
# SQLite in-memory DB — no Docker needed, blazing fast.
# Not identical to Postgres, but good enough for unit tests.
# Integration tests use real Postgres via testcontainers.
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def in_memory_db():
    """
    Creates a fresh in-memory SQLite database for each test.
    Tables are created, test runs, then everything is thrown away.
    Perfect for unit tests — no state leaks between tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# =============================================================================
# MOCK AUTH
# We don't want tests to actually call Keycloak.
# This fixture replaces the auth dependency with a fake user.
# =============================================================================

@pytest.fixture
def mock_user():
    """A fake authenticated user for testing protected endpoints."""
    from app.core.auth import TokenData
    return TokenData(
        user_id="test-keycloak-id-123",
        email="felix@codai.app",
        username="felix",
        roles=["user"],
    )

@pytest.fixture
def mock_admin_user():
    """A fake admin user."""
    from app.core.auth import TokenData
    return TokenData(
        user_id="admin-keycloak-id-456",
        email="admin@codai.app",
        username="admin",
        roles=["user", "admin"],
    )


# =============================================================================
# TEST CLIENT
# httpx AsyncClient that talks directly to the FastAPI app (no real HTTP server needed)
# =============================================================================

@pytest_asyncio.fixture
async def client(in_memory_db, mock_user):
    """
    A test HTTP client with:
    - In-memory SQLite database (no Postgres needed)
    - Mocked auth (no Keycloak needed)
    - Mocked vector store (no Milvus needed)
    - Mocked storage (no MinIO needed)

    Perfect for unit-testing API endpoints.
    """
    # Override the DB dependency — use our test DB instead of real Postgres
    async def override_get_db():
        yield in_memory_db

    # Override auth — skip JWT validation, return our fake user
    def override_verify_token():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_token] = override_verify_token

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clean up overrides after test
    app.dependency_overrides.clear()


# =============================================================================
# MOCK EXTERNAL SERVICES
# These replace Milvus, MinIO, and Ollama with fakes for unit tests.
# Integration tests use the real services via testcontainers.
# =============================================================================

@pytest.fixture
def mock_vector_store(mocker):
    """
    Replaces the Milvus vector store with a mock.
    Records calls so we can assert they happened correctly.
    """
    mock = MagicMock()
    mock.insert_chunks.return_value = ["chunk-id-1", "chunk-id-2"]
    mock.search.return_value = [
        {
            "chunk_id": "chunk-id-1",
            "document_id": "doc-id-1",
            "source_id": "source-id-1",
            "text": "The EU AI Act requires conformity assessments for high-risk AI systems.",
            "title": "EU AI Act Summary",
            "url": "https://example.com/eu-ai-act",
            "chunk_index": 0,
            "score": 0.92,
        }
    ]
    mock.delete_by_document.return_value = None
    mock.delete_by_source.return_value = None

    mocker.patch("app.services.processor.vector_store", mock)
    mocker.patch("app.api.routes.search.vector_store", mock)
    mocker.patch("app.api.routes.sources.vector_store", mock)
    return mock


@pytest.fixture
def mock_storage(mocker):
    """Replaces MinIO with a mock."""
    mock = MagicMock()
    mock.store_raw_document.return_value = ("sources/test/doc.html", "abc123hash")
    mock.retrieve_raw_document.return_value = b"<html><body><p>Test content</p></body></html>"
    mock.store_chunks.return_value = "chunks/doc.json"
    mock.ensure_buckets = AsyncMock(return_value=None)

    mocker.patch("app.services.processor.storage_service", mock)
    return mock


# =============================================================================
# TEST DATA FACTORIES
# Functions that create realistic test data
# =============================================================================

@pytest.fixture
def make_source():
    """Factory for creating test Source dicts."""
    def _make(overrides=None):
        data = {
            "name": fake.company() + " Blog",
            "url": fake.url(),
            "source_type": "website",
            "crawl_interval_minutes": 360,
        }
        if overrides:
            data.update(overrides)
        return data
    return _make


@pytest.fixture
def sample_html():
    """A realistic HTML page for testing the chunker."""
    return b"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EU AI Act: What You Need to Know</title>
        <meta name="description" content="A comprehensive overview of the EU AI Act">
    </head>
    <body>
        <nav>Home | About | Contact</nav>
        <main>
            <article>
                <h1>EU AI Act: What You Need to Know</h1>
                <p>The European Union's Artificial Intelligence Act represents a landmark
                regulatory framework for AI systems. It categorizes AI applications into
                different risk levels and imposes corresponding requirements.</p>

                <h2>Risk Categories</h2>
                <p>The Act defines four risk categories: unacceptable risk, high risk,
                limited risk, and minimal risk. High-risk AI systems require conformity
                assessments before deployment.</p>

                <h2>Foundation Models</h2>
                <p>General-purpose AI models, such as large language models, face specific
                obligations around transparency and capability evaluations. Models above
                certain compute thresholds face additional systemic risk requirements.</p>
            </article>
        </main>
        <footer>Copyright 2026</footer>
    </body>
    </html>
    """
