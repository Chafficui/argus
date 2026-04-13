#!/usr/bin/env python3
"""
ingest_test_doc.py — end-to-end pipeline test with a real document.

Fetches a public webpage, creates Source + Document rows in Postgres,
runs the full processing pipeline (chunk → embed → Milvus), then
performs a vector search to verify everything works.

Prerequisites:
    docker compose -f docker-compose.dev.yml up -d
    docker exec argus-ollama ollama pull nomic-embed-text
    cp .env.dev .env

Usage:
    cd services/backend
    python scripts/ingest_test_doc.py
"""

import asyncio
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.db.database import init_db, AsyncSessionLocal
from app.models.models import User, Source, Document, SourceType, DocumentStatus
from app.services.processor import processor
from app.services.storage import storage_service
from app.services.vector_store import vector_store

# Hardcoded test user — no Keycloak needed for this script
TEST_USER_KEYCLOAK_ID = "test-user-00000000-0000-0000-0000-000000000000"
TEST_USER_EMAIL = "test@argus.dev"
TEST_USER_NAME = "test-ingest"

TARGET_URL = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"

settings = get_settings()


async def get_or_create_user(db) -> User:
    """Find existing test user or create a new one."""
    result = await db.execute(
        select(User).where(User.keycloak_id == TEST_USER_KEYCLOAK_ID)
    )
    user = result.scalar_one_or_none()
    if user:
        print(f"  Found existing test user: {user.id}")
        return user

    user = User(
        keycloak_id=TEST_USER_KEYCLOAK_ID,
        email=TEST_USER_EMAIL,
        username=TEST_USER_NAME,
    )
    db.add(user)
    await db.flush()
    print(f"  Created test user: {user.id}")
    return user


async def get_or_create_source(db, user: User) -> Source:
    """Find existing test source or create a new one."""
    result = await db.execute(
        select(Source).where(Source.url == TARGET_URL, Source.user_id == user.id)
    )
    source = result.scalar_one_or_none()
    if source:
        print(f"  Found existing source: {source.id}")
        return source

    source = Source(
        user_id=user.id,
        name="Wikipedia — Retrieval-Augmented Generation",
        url=TARGET_URL,
        source_type=SourceType.WEBSITE,
    )
    db.add(source)
    await db.flush()
    print(f"  Created source: {source.id}")
    return source


async def get_or_create_document(db, source: Source) -> Document:
    """Find existing test document or create a new one."""
    result = await db.execute(
        select(Document).where(Document.source_id == source.id, Document.url == TARGET_URL)
    )
    doc = result.scalar_one_or_none()
    if doc:
        # Reset status so we re-process
        doc.status = DocumentStatus.RAW
        doc.content_hash = None
        await db.flush()
        print(f"  Found existing document (reset to RAW): {doc.id}")
        return doc

    doc = Document(
        source_id=source.id,
        url=TARGET_URL,
        title="Retrieval-Augmented Generation",
    )
    db.add(doc)
    await db.flush()
    print(f"  Created document: {doc.id}")
    return doc


async def main():
    print("=" * 70)
    print("Argus — End-to-End Ingest Test")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: Initialize services
    # ------------------------------------------------------------------
    print("\n[1/5] Initializing services...")
    await init_db()
    await storage_service.ensure_buckets()
    vector_store.connect()
    print("  Postgres, MinIO, Milvus connected.")

    # ------------------------------------------------------------------
    # Step 2: Fetch the real webpage
    # ------------------------------------------------------------------
    print(f"\n[2/5] Fetching {TARGET_URL}...")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(TARGET_URL)
        response.raise_for_status()
    html_content = response.content
    print(f"  Fetched {len(html_content):,} bytes ({response.status_code})")

    # ------------------------------------------------------------------
    # Step 3: Create DB records
    # ------------------------------------------------------------------
    print("\n[3/5] Creating database records...")
    async with AsyncSessionLocal() as db:
        try:
            user = await get_or_create_user(db)
            source = await get_or_create_source(db, user)
            document = await get_or_create_document(db, source)
            user_id = user.id

            # ----------------------------------------------------------
            # Step 4: Run the full processing pipeline
            # ----------------------------------------------------------
            print(f"\n[4/5] Processing document through pipeline...")
            success = await processor.process_document(
                db=db,
                document=document,
                html_content=html_content,
                user_id=user_id,
            )

            if not success:
                print("\n  FAILED: Pipeline returned False. Check logs above.")
                await db.rollback()
                sys.exit(1)

            await db.commit()

            # Refresh to get updated fields
            await db.refresh(document)

            chunk_ids = document.milvus_chunk_ids.split(",") if document.milvus_chunk_ids else []
            print(f"  Status:      {document.status.value}")
            print(f"  Title:       {document.title}")
            print(f"  Word count:  {document.word_count:,}")
            print(f"  Chunks:      {len(chunk_ids)}")
            print(f"  Chunk IDs:   {chunk_ids[:3]}{'...' if len(chunk_ids) > 3 else ''}")

        except Exception:
            await db.rollback()
            raise

    # ------------------------------------------------------------------
    # Step 5: Search to verify indexing worked
    # ------------------------------------------------------------------
    print(f"\n[5/5] Searching for 'What is retrieval augmented generation?'...")
    results = vector_store.search(
        query="What is retrieval augmented generation?",
        user_id=user_id,
        top_k=3,
    )

    if not results:
        print("\n  FAILED: No search results returned.")
        sys.exit(1)

    print(f"  Found {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        snippet = r["text"][:120].replace("\n", " ")
        print(f"  [{i}] score={r['score']:.4f}")
        print(f"      {snippet}...")
        print()

    print("=" * 70)
    print("SUCCESS — document ingested and searchable end-to-end!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
