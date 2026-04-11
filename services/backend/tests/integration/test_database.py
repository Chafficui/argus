# =============================================================================
# tests/integration/test_database.py
# =============================================================================
# Integration tests with a real PostgreSQL database.
#
# TESTCONTAINERS:
# This library starts an actual Docker container for each test session.
# No mocking — real SQL, real constraints, real transactions.
#
# Why both unit AND integration tests?
# Unit tests (SQLite) are fast but SQLite isn't identical to Postgres.
# Some bugs only appear with real Postgres:
#   - Different NULL handling
#   - Postgres-specific constraints
#   - Async connection pool behavior
#   - Cascade deletes with foreign keys
#
# These tests are slower (~5-10s startup) but catch a different class of bugs.
# =============================================================================

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text

from app.models.models import Base, Source, Document, CrawlJob, SourceType, DocumentStatus, CrawlStatus
from app.db.database import get_db
from app.core.auth import verify_token
from httpx import AsyncClient, ASGITransport
from app.main import app


# =============================================================================
# POSTGRES CONTAINER FIXTURE
# Starts a real Postgres Docker container once per test session.
# All integration tests in this file share the same container.
# =============================================================================

@pytest.fixture(scope="session")
def postgres_container():
    """
    Start a PostgreSQL container for the test session.
    scope="session" = started once, shared across all tests in this file.
    Automatically stopped when all tests finish.
    """
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def pg_engine(postgres_container):
    """Create async SQLAlchemy engine connected to the test Postgres container."""
    # testcontainers gives us the connection URL — we just replace the driver prefix
    url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )

    engine = create_async_engine(url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine):
    """
    Provides a database session that rolls back after each test.
    This keeps tests isolated — no data leaks between tests.

    SAVEPOINT trick:
    We wrap each test in a transaction and roll it back at the end.
    This is much faster than dropping/recreating tables.
    """
    async with pg_engine.begin() as conn:
        # Create a savepoint — we'll roll back to here after the test
        await conn.execute(text("SAVEPOINT test_savepoint"))
        session_factory = async_sessionmaker(
            bind=conn, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            yield session
        # Roll back to savepoint — test data is erased
        await conn.execute(text("ROLLBACK TO SAVEPOINT test_savepoint"))


# =============================================================================
# INTEGRATION TEST CLIENT
# Uses real Postgres instead of SQLite
# =============================================================================

@pytest_asyncio.fixture
async def integration_client(pg_session, mock_user):
    """Test client backed by real PostgreSQL."""
    async def override_db():
        yield pg_session

    def override_auth():
        return mock_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[verify_token] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# TESTS
# =============================================================================

class TestSourceCRUDWithRealPostgres:

    @pytest.mark.integration
    async def test_create_and_retrieve_source(self, integration_client, make_source):
        """Create a source and verify it's actually in Postgres."""
        payload = make_source({"name": "Real DB Test"})
        create_resp = await integration_client.post("/api/sources/", json=payload)
        assert create_resp.status_code == 201
        source_id = create_resp.json()["id"]

        # Retrieve it
        get_resp = await integration_client.get(f"/api/sources/{source_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Real DB Test"

    @pytest.mark.integration
    async def test_cascade_delete_removes_documents(self, pg_session, mock_user):
        """
        When a source is deleted, all its documents should be deleted too.
        This tests the cascade="all, delete-orphan" relationship.
        SQLite doesn't enforce FK constraints by default — this needs real Postgres.
        """
        from app.api.routes.sources import get_or_create_user
        from app.core.auth import TokenData

        token = TokenData(
            user_id="cascade-test-user",
            email="cascade@test.com",
            username="cascadetest",
            roles=["user"]
        )
        user = await get_or_create_user(token, pg_session)

        # Create a source with documents
        source = Source(
            user_id=user.id,
            name="Source to delete",
            url="https://delete-me.com",
            source_type=SourceType.WEBSITE,
        )
        pg_session.add(source)
        await pg_session.flush()

        doc = Document(
            source_id=source.id,
            url="https://delete-me.com/article",
            status=DocumentStatus.EMBEDDED,
        )
        pg_session.add(doc)
        await pg_session.flush()

        doc_id = doc.id

        # Delete the source
        await pg_session.delete(source)
        await pg_session.flush()

        # Verify document is gone (cascade worked)
        result = await pg_session.execute(
            select(Document).where(Document.id == doc_id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.integration
    async def test_postgres_unique_constraint_on_keycloak_id(self, pg_session, mock_user):
        """
        Two users with the same keycloak_id should not be possible.
        Tests the unique=True constraint on User.keycloak_id.
        """
        from app.models.models import User
        from sqlalchemy.exc import IntegrityError

        user1 = User(
            keycloak_id="same-keycloak-id",
            email="user1@test.com",
            username="user1",
        )
        user2 = User(
            keycloak_id="same-keycloak-id",  # Same ID!
            email="user2@test.com",
            username="user2",
        )

        pg_session.add(user1)
        await pg_session.flush()

        pg_session.add(user2)
        with pytest.raises(IntegrityError):
            await pg_session.flush()


class TestCrawlJobTracking:

    @pytest.mark.integration
    async def test_crawl_job_lifecycle(self, pg_session, mock_user):
        """Test that crawl job status transitions work correctly."""
        from app.api.routes.sources import get_or_create_user
        from app.core.auth import TokenData
        import datetime

        token = TokenData(
            user_id="crawl-test-user",
            email="crawl@test.com",
            username="crawltest",
            roles=["user"]
        )
        user = await get_or_create_user(token, pg_session)

        source = Source(
            user_id=user.id,
            name="Crawl Test Source",
            url="https://crawl-test.com",
        )
        pg_session.add(source)
        await pg_session.flush()

        # Simulate a crawl job lifecycle
        job = CrawlJob(
            source_id=source.id,
            status=CrawlStatus.PENDING,
        )
        pg_session.add(job)
        await pg_session.flush()

        # Start the job
        job.status = CrawlStatus.RUNNING
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        await pg_session.flush()

        # Complete the job
        job.status = CrawlStatus.SUCCESS
        job.finished_at = datetime.datetime.now(datetime.timezone.utc)
        job.documents_found = 5
        job.documents_indexed = 4
        job.duration_seconds = 12.3
        await pg_session.flush()

        # Verify in DB
        result = await pg_session.execute(
            select(CrawlJob).where(CrawlJob.id == job.id)
        )
        saved_job = result.scalar_one()
        assert saved_job.status == CrawlStatus.SUCCESS
        assert saved_job.documents_found == 5
        assert saved_job.duration_seconds == 12.3
