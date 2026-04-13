# =============================================================================
# app/api/routes/ingest.py
# =============================================================================
# The HTTP endpoint the crawler calls after fetching a page.
# Decouples the crawler from the database — the crawler never touches
# Postgres or Milvus directly.
#
# POST /api/ingest/           → accepts HTML, creates Document, triggers processing
# POST /api/ingest/crawl-job  → records a CrawlJob audit entry from the crawler
# =============================================================================

import base64
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
import structlog

from app.core.auth import verify_token, TokenData
from app.db.database import get_db
from app.models.models import Source, Document, DocumentStatus, CrawlJob, CrawlStatus
from app.services.processor import processor

log = structlog.get_logger()

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    source_id: str
    url: str
    html_content: str  # base64-encoded HTML bytes
    title: str | None = None


class IngestResponse(BaseModel):
    document_id: str
    status: str


@router.post("/", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    body: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """
    Accept a fetched page from the crawler and queue it for processing.
    Returns 202 immediately — processing happens in the background.
    """
    # Verify source exists and belongs to this user
    from app.api.routes.sources import get_or_create_user

    user = await get_or_create_user(token, db)

    result = await db.execute(
        select(Source).where(
            and_(Source.id == body.source_id, Source.user_id == user.id)
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found or does not belong to this user",
        )

    # Decode base64 HTML
    try:
        html_bytes = base64.b64decode(body.html_content)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="html_content must be valid base64",
        )

    # Create Document record
    doc = Document(
        source_id=body.source_id,
        url=body.url,
        title=body.title,
        status=DocumentStatus.RAW,
    )
    db.add(doc)
    # Commit now so the background task (which opens its own session) can see the document
    await db.commit()

    doc_id = doc.id

    log.info(
        "Ingesting document",
        document_id=doc_id,
        source_id=body.source_id,
        url=body.url,
    )

    # Process in background — the response returns immediately
    background_tasks.add_task(
        _process_in_background, doc_id, html_bytes, user.keycloak_id
    )

    return IngestResponse(document_id=doc_id, status="processing")


async def _process_in_background(
    document_id: str, html_bytes: bytes, user_id: str
) -> None:
    """Run the processing pipeline in a background task with its own DB session."""
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document is None:
                log.error("Document not found for processing", document_id=document_id)
                return

            success = await processor.process_document(
                db=db, document=document, html_content=html_bytes, user_id=user_id
            )
            await db.commit()

            if success:
                log.info("Background processing completed", document_id=document_id)
            else:
                log.warning("Background processing failed", document_id=document_id)
        except Exception as e:
            await db.rollback()
            log.error(
                "Background processing error",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )


# =============================================================================
# CRAWL JOB REPORTING
# =============================================================================


class CrawlJobReport(BaseModel):
    source_id: str
    status: str  # "success" or "failed"
    documents_found: int
    documents_indexed: int
    duration_seconds: float
    error_message: str | None = None


class CrawlJobResponse(BaseModel):
    crawl_job_id: str


@router.post("/crawl-job", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def report_crawl_job(
    body: CrawlJobReport,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Record the result of a crawl run. Called by the crawler after each source."""
    from app.api.routes.sources import get_or_create_user

    user = await get_or_create_user(token, db)

    # Verify source belongs to user
    result = await db.execute(
        select(Source).where(
            and_(Source.id == body.source_id, Source.user_id == user.id)
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found or does not belong to this user",
        )

    crawl_status = CrawlStatus.SUCCESS if body.status == "success" else CrawlStatus.FAILED
    now = datetime.now(timezone.utc)

    job = CrawlJob(
        source_id=body.source_id,
        status=crawl_status,
        started_at=now,
        finished_at=now,
        documents_found=body.documents_found,
        documents_indexed=body.documents_indexed,
        duration_seconds=body.duration_seconds,
        error_message=body.error_message,
    )
    db.add(job)
    await db.flush()

    log.info(
        "CrawlJob recorded",
        crawl_job_id=job.id,
        source_id=body.source_id,
        status=body.status,
        documents_indexed=body.documents_indexed,
    )

    return CrawlJobResponse(crawl_job_id=job.id)
