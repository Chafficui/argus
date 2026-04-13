# =============================================================================
# app/db/database.py
# =============================================================================
# Database connection setup.
#
# WHY ASYNC?
# A normal (sync) database call blocks the entire thread while waiting for DB:
#   result = db.execute(query)  ← Python does nothing for 20ms
#
# An async call releases the thread while waiting:
#   result = await db.execute(query)  ← Python handles other requests during those 20ms
#
# For a web server handling 100 concurrent users, this is a huge difference.
# FastAPI is built for async — we use asyncpg as the async PostgreSQL driver.
#
# CONNECTION POOL:
# Opening a new DB connection is expensive (~50ms).
# A connection pool keeps N connections open and reuses them.
# When a request needs the DB, it borrows a connection from the pool.
# When done, it returns it. Much faster than opening a new one each time.
# =============================================================================

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_settings
from app.models.models import Base
import structlog

log = structlog.get_logger()


def get_engine():
    settings = get_settings()

    return create_async_engine(
        settings.postgres_url,
        # Pool settings:
        pool_size=10,  # Keep 10 connections open permanently
        max_overflow=20,  # Allow up to 20 extra connections during spikes
        pool_pre_ping=True,  # Check connection health before handing it to a request
        # (prevents "broken pipe" errors if Postgres restarted)
        echo=settings.environment == "development",  # Log all SQL in dev mode
    )


engine = get_engine()

# AsyncSessionLocal is a factory — calling it creates a new session
# Each HTTP request gets its own session (its own "conversation" with the DB)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (avoids extra queries)
)


async def get_db():
    """
    FastAPI dependency — provides a database session to route handlers.

    Usage in routes:
        @router.get("/sources")
        async def list_sources(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Source))
            ...

    The 'async with' and 'finally' ensure the session is always closed,
    even if an exception occurs mid-request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit if everything went well
        except Exception:
            await session.rollback()  # Roll back on any error
            raise
        # Session is automatically closed when 'async with' exits


async def init_db():
    """
    Creates all tables on startup if they don't exist yet.
    In production you'd use Alembic migrations instead (more controlled).
    For dev, this is convenient.
    """
    log.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ready")
