# =============================================================================
# app/api/routes/search.py
# =============================================================================
# Search and RAG endpoints — the core value of Argus.
#
# POST /api/search/       → vector search across user's documents
# POST /api/search/ask    → RAG: search + LLM-generated answer
#
# Flow:
#   1. User sends natural language query
#   2. Query is embedded via Ollama nomic-embed-text
#   3. Milvus finds the closest document chunks (cosine similarity)
#   4. (optional) LLM synthesizes an answer from the top chunks
# =============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
import structlog

from app.core.auth import verify_token, TokenData
from app.db.database import get_db
from app.models.models import Source
from app.services.vector_store import vector_store
from app.services.llm import llm_service

log = structlog.get_logger()

router = APIRouter(tags=["search"])


# =============================================================================
# SCHEMAS
# =============================================================================


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    source_ids: list[str] | None = None
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    source_id: str
    text: str
    title: str
    url: str
    chunk_index: int
    score: float
    source_name: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class AskRequest(SearchRequest):
    system_prompt: str | None = None


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: list[SearchResult]


# =============================================================================
# HELPERS
# =============================================================================


async def enrich_results(
    results: list[dict],
    db: AsyncSession,
) -> list[SearchResult]:
    """Attach source names to search results by looking up the DB."""
    if not results:
        return []

    source_ids = list({r["source_id"] for r in results})
    query = select(Source.id, Source.name).where(Source.id.in_(source_ids))
    rows = (await db.execute(query)).all()
    source_names = {row.id: row.name for row in rows}

    return [
        SearchResult(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            source_id=r["source_id"],
            text=r["text"],
            title=r.get("title", ""),
            url=r.get("url", ""),
            chunk_index=r.get("chunk_index", 0),
            score=r["score"],
            source_name=source_names.get(r["source_id"]),
        )
        for r in results
    ]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """
    Semantic search across the user's indexed documents.
    Returns ranked chunks with relevance scores.
    """
    raw_results = vector_store.search(
        query=body.query,
        user_id=token.user_id,
        top_k=body.top_k,
        source_ids=body.source_ids,
    )

    # Filter below min_score
    filtered = [r for r in raw_results if r["score"] >= body.min_score]

    results = await enrich_results(filtered, db)

    log.info(
        "Search completed",
        query_preview=body.query[:50],
        raw_count=len(raw_results),
        filtered_count=len(results),
    )

    return SearchResponse(
        query=body.query,
        results=results,
        total=len(results),
    )


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """
    RAG endpoint: search for relevant chunks, then generate an answer using the LLM.
    Returns the LLM answer plus the source chunks used.
    """
    raw_results = vector_store.search(
        query=body.query,
        user_id=token.user_id,
        top_k=body.top_k,
        source_ids=body.source_ids,
    )

    filtered = [r for r in raw_results if r["score"] >= body.min_score]
    results = await enrich_results(filtered, db)

    # Generate answer from context
    answer = llm_service.answer_with_context(
        question=body.query,
        context_chunks=[r.model_dump() for r in results],
        system_prompt=body.system_prompt,
    )

    log.info(
        "RAG answer generated",
        query_preview=body.query[:50],
        chunks_used=len(results),
        answer_length=len(answer),
    )

    return AskResponse(
        query=body.query,
        answer=answer,
        sources=results,
    )
