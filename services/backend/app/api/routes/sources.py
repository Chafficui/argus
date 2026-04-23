# =============================================================================
# app/api/routes/sources.py
# =============================================================================
# REST API endpoints for managing monitored sources.
#
# REST = Representational State Transfer — a convention for HTTP APIs:
#   GET    /sources       → list all sources
#   POST   /sources       → create a new source
#   GET    /sources/{id}  → get one source
#   PUT    /sources/{id}  → update a source
#   DELETE /sources/{id}  → delete a source
#
# Each endpoint:
#   1. Validates auth (via Depends(verify_token))
#   2. Validates input (via Pydantic schemas)
#   3. Queries the database
#   4. Returns a response
# =============================================================================

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, HttpUrl
import structlog

from app.core.auth import verify_token, TokenData
from app.db.database import get_db
from app.models.models import Source, User, SourceType, CrawlJob, CrawlStatus, Document
from app.core.config import get_settings
from app.services.vector_store import vector_store
from app.services.metrics import active_sources_gauge

log = structlog.get_logger()

# APIRouter groups related endpoints together.
# In main.py we mount this with: app.include_router(sources_router, prefix="/api/sources")
router = APIRouter(tags=["sources"])


# =============================================================================
# PYDANTIC SCHEMAS
# These define the shape of request bodies and response payloads.
# Pydantic automatically validates types and required fields.
# If a client sends wrong data → 422 Unprocessable Entity (automatic, no code needed)
# =============================================================================


class SourceCreate(BaseModel):
    """Schema for creating a new source — what the client sends."""

    name: str
    url: HttpUrl  # Pydantic validates this is a valid URL
    source_type: SourceType = SourceType.WEBSITE
    search_query: str | None = None
    crawl_interval_hours: int = 6


class SourceUpdate(BaseModel):
    """Schema for updating — all fields optional (PATCH semantics)."""

    name: str | None = None
    is_active: bool | None = None
    crawl_interval_hours: int | None = None


class SourceResponse(BaseModel):
    """Schema for responses — what we send back to the client."""

    id: str
    name: str
    url: str
    source_type: SourceType
    search_query: str | None = None
    is_active: bool
    crawl_interval_hours: int
    last_crawled_at: datetime | None
    created_at: datetime
    document_count: int = 0

    # This tells Pydantic to read from SQLAlchemy model attributes
    model_config = {"from_attributes": True}


# =============================================================================
# HELPER: get or create user
# On first request, we sync the Keycloak user into our database.
# =============================================================================


async def get_or_create_user(token: TokenData, db: AsyncSession) -> User:
    """
    Looks up the user by their Keycloak ID.
    If they don't exist in our DB yet (first login), creates them.
    This pattern is called "upsert on first login".
    """
    result = await db.execute(select(User).where(User.keycloak_id == token.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        log.info("Creating new user from Keycloak token", keycloak_id=token.user_id)
        user = User(
            keycloak_id=token.user_id,
            email=token.email,
            username=token.username,
        )
        db.add(user)
        await db.flush()  # flush assigns the ID without committing the transaction

    return user


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),  # ← requires valid JWT
):
    """List all sources for the authenticated user."""
    user = await get_or_create_user(token, db)

    # Subquery to count documents per source
    doc_count_sub = (
        select(Document.source_id, func.count(Document.id).label("document_count"))
        .group_by(Document.source_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Source,
            func.coalesce(doc_count_sub.c.document_count, 0).label("document_count"),
        )
        .outerjoin(doc_count_sub, Source.id == doc_count_sub.c.source_id)
        .where(Source.user_id == user.id)
        .order_by(Source.created_at.desc())
    )
    rows = result.all()

    sources = []
    for source, doc_count in rows:
        resp = SourceResponse.model_validate(source)
        resp.document_count = doc_count
        sources.append(resp)

    log.info("Listed sources", user_id=user.id, count=len(sources))
    return sources


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Create a new monitored source."""
    settings = get_settings()
    user = await get_or_create_user(token, db)

    # Check user hasn't exceeded their source limit
    result = await db.execute(
        select(Source).where(
            and_(Source.user_id == user.id, Source.is_active.is_(True))
        )
    )
    existing = result.scalars().all()

    if len(existing) >= settings.max_sources_per_user:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum of {settings.max_sources_per_user} sources reached",
        )

    # Validate: SERP sources need a search_query
    if body.source_type == SourceType.SERP and not body.search_query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="search_query is required for SERP sources",
        )

    source = Source(
        user_id=user.id,
        name=body.name,
        url=str(body.url),
        source_type=body.source_type,
        search_query=body.search_query,
        crawl_interval_hours=body.crawl_interval_hours,
    )
    db.add(source)
    await db.flush()

    active_sources_gauge.inc()
    log.info("Created source", source_id=source.id, url=source.url, user_id=user.id)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Get a single source by ID."""
    user = await get_or_create_user(token, db)

    result = await db.execute(
        select(Source).where(and_(Source.id == source_id, Source.user_id == user.id))
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    body: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Update a source."""
    user = await get_or_create_user(token, db)

    result = await db.execute(
        select(Source).where(and_(Source.id == source_id, Source.user_id == user.id))
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # Only update fields that were actually provided
    # model_dump(exclude_unset=True) returns only the fields the client sent
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    log.info(
        "Updated source",
        source_id=source_id,
        changes=body.model_dump(exclude_unset=True),
    )
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Delete a source and all its documents."""
    user = await get_or_create_user(token, db)

    result = await db.execute(
        select(Source).where(and_(Source.id == source_id, Source.user_id == user.id))
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # Remove vectors from Milvus before deleting DB records
    vector_store.delete_by_source(source_id)

    await db.delete(
        source
    )  # cascade="all, delete-orphan" in the model handles related records
    active_sources_gauge.dec()
    log.info("Deleted source", source_id=source_id, user_id=user.id)


@router.patch("/{source_id}/last-crawled", response_model=SourceResponse)
async def update_last_crawled(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Update the last_crawled_at timestamp for a source. Called by the crawler after a crawl run."""
    user = await get_or_create_user(token, db)

    result = await db.execute(
        select(Source).where(and_(Source.id == source_id, Source.user_id == user.id))
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    source.last_crawled_at = datetime.now(timezone.utc)
    log.info("Updated last_crawled_at", source_id=source_id)
    return source


# =============================================================================
# CRAWL HISTORY
# =============================================================================


class CrawlJobResponse(BaseModel):
    id: str
    source_id: str
    status: CrawlStatus
    started_at: datetime | None
    finished_at: datetime | None
    documents_found: int
    documents_indexed: int
    duration_seconds: float | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{source_id}/crawl-jobs", response_model=list[CrawlJobResponse])
async def get_crawl_jobs(
    source_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Return the most recent crawl jobs for a source."""
    user = await get_or_create_user(token, db)

    # Verify source belongs to user
    result = await db.execute(
        select(Source).where(and_(Source.id == source_id, Source.user_id == user.id))
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.source_id == source_id)
        .order_by(CrawlJob.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()

    log.info("Listed crawl jobs", source_id=source_id, count=len(jobs))
    return jobs
