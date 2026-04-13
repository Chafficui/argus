# =============================================================================
# app/services/processor.py
# =============================================================================
# The document processing pipeline — orchestrates everything.
#
# FULL FLOW:
#
#   Raw HTML (from crawler)
#       │
#       ▼
#   1. Store in MinIO (raw backup, source of truth)
#       │
#       ▼
#   2. Extract text + metadata (BeautifulSoup)
#       │
#       ▼
#   3. Chunk text (RecursiveCharacterTextSplitter)
#       │
#       ▼
#   4. Embed chunks (Ollama nomic-embed-text)
#       │
#       ▼
#   5. Insert chunks into Milvus (now searchable)
#       │
#       ▼
#   6. Update document status in PostgreSQL (EMBEDDED)
#       │
#       ▼
#   Ready for RAG search!
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.models import Document, DocumentStatus
from app.services.storage import storage_service
from app.services.vector_store import vector_store
from app.services.chunker import chunker

log = structlog.get_logger()


class DocumentProcessor:
    """
    Orchestrates the full document processing pipeline.
    Called by the crawler after fetching a page, and by the API for manual re-processing.
    """

    async def process_document(
        self,
        db: AsyncSession,
        document: Document,
        html_content: bytes,
        user_id: str,
    ) -> bool:
        """
        Runs the full processing pipeline for a single document.

        Returns True on success, False on failure.
        Updates the document's status in PostgreSQL throughout.
        """
        doc_id = document.id
        log.info("Processing document", document_id=doc_id, url=document.url)

        try:
            # ----------------------------------------------------------------
            # STEP 1: Store raw HTML in MinIO
            # ----------------------------------------------------------------
            minio_path, content_hash = storage_service.store_raw_document(
                source_id=document.source_id,
                document_id=doc_id,
                content=html_content,
                content_type="text/html",
            )

            # Check if content has changed since last crawl
            # If hash is the same → skip re-processing (save compute)
            if (
                document.content_hash == content_hash
                and document.status == DocumentStatus.EMBEDDED
            ):
                log.info(
                    "Document unchanged, skipping re-processing", document_id=doc_id
                )
                return True

            # Update document with storage info
            document.minio_path = minio_path
            document.content_hash = content_hash
            document.status = DocumentStatus.RAW
            await db.flush()

            # ----------------------------------------------------------------
            # STEP 2 + 3: Extract text and chunk it
            # ----------------------------------------------------------------
            chunks, metadata = chunker.chunk_html_document(
                html=html_content,
                document_id=doc_id,
                source_id=document.source_id,
                user_id=user_id,
                url=document.url,
            )

            if not chunks:
                log.warning("No chunks extracted from document", document_id=doc_id)
                document.status = DocumentStatus.FAILED
                await db.flush()
                return False

            # Update document metadata from extracted HTML
            document.title = metadata.get("title") or document.title
            document.word_count = sum(len(c["text"].split()) for c in chunks)
            document.status = DocumentStatus.CHUNKED

            # Store chunks as JSON in MinIO (for debugging / reprocessing)
            storage_service.store_chunks(doc_id, chunks)

            await db.flush()

            # ----------------------------------------------------------------
            # STEP 4 + 5: Embed and insert into Milvus
            # ----------------------------------------------------------------
            # Delete old chunks if this is a re-processing
            vector_store.delete_by_document(doc_id)

            # Insert new chunks (embed + store in one call)
            chunk_ids = vector_store.insert_chunks(chunks)

            # ----------------------------------------------------------------
            # STEP 6: Update document status to EMBEDDED
            # ----------------------------------------------------------------
            document.milvus_chunk_ids = ",".join(chunk_ids)
            document.status = DocumentStatus.EMBEDDED
            await db.flush()

            log.info(
                "Document processed successfully",
                document_id=doc_id,
                chunks=len(chunks),
                words=document.word_count,
            )
            return True

        except Exception as e:
            log.error(
                "Document processing failed",
                document_id=doc_id,
                error=str(e),
                exc_info=True,
            )
            document.status = DocumentStatus.FAILED
            await db.flush()
            return False

    async def reprocess_document(
        self, db: AsyncSession, document_id: str, user_id: str
    ) -> bool:
        """
        Re-processes a document from its stored raw HTML.
        Useful if the embedding model changes or chunking strategy is updated.
        Called from the API when a user requests manual reprocessing.
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if document is None or document.minio_path is None:
            log.error(
                "Document not found or has no stored content", document_id=document_id
            )
            return False

        # Retrieve the raw HTML from MinIO
        html_content = storage_service.retrieve_raw_document(document.minio_path)

        return await self.process_document(db, document, html_content, user_id)


# Singleton
processor = DocumentProcessor()
