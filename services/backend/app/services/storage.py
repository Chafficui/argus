# =============================================================================
# app/services/storage.py
# =============================================================================
# MinIO service — object storage for raw crawled documents.
#
# WHAT IS OBJECT STORAGE?
# Think of it like a hard drive in the cloud (or in our case, on-premise).
# Instead of a file system with folders, everything is a flat "object" with a key.
#
# Structure:
#   Bucket: argus-raw-docs
#     └── sources/source-uuid/doc-uuid.html   ← raw HTML from crawler
#     └── sources/source-uuid/doc-uuid.pdf    ← raw PDF
#
#   Bucket: argus-processed
#     └── chunks/doc-uuid.json                ← chunked text ready for embedding
#
# WHY NOT JUST USE POSTGRES FOR THIS?
# Postgres is great for structured data (rows, columns, queries).
# But storing 10,000 HTML files (each 50-200KB) in Postgres would be slow and wasteful.
# Object storage is optimized for large blobs — cheap, fast, scalable.
# This is the same pattern AWS S3 uses. MinIO is the on-premise equivalent.
# =============================================================================

from minio import Minio
from minio.error import S3Error
import io
import json
import hashlib
import structlog
from app.core.config import get_settings

log = structlog.get_logger()


class StorageService:
    """
    Wraps the MinIO client with Argus-specific methods.
    All document storage goes through this class.
    """

    def __init__(self):
        settings = get_settings()
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket_raw = settings.minio_bucket_raw
        self._bucket_processed = settings.minio_bucket_processed

    async def ensure_buckets(self):
        """
        Creates buckets if they don't exist yet.
        Called once on startup — idempotent (safe to call multiple times).
        Like mkdir -p for object storage.
        """
        for bucket in [self._bucket_raw, self._bucket_processed]:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
                log.info("Created MinIO bucket", bucket=bucket)
            else:
                log.info("MinIO bucket already exists", bucket=bucket)

    def store_raw_document(
        self,
        source_id: str,
        document_id: str,
        content: bytes,
        content_type: str = "text/html",
    ) -> tuple[str, str]:
        """
        Stores a raw crawled document in MinIO.

        Returns:
            (minio_path, content_hash)
            minio_path: the key to retrieve it later
            content_hash: SHA-256 of the content (to detect changes on re-crawl)
        """
        # Generate a content hash — if the page hasn't changed since last crawl,
        # we skip re-processing (saves compute time and Milvus storage)
        content_hash = hashlib.sha256(content).hexdigest()

        # Build the object key — like a file path, but flat
        minio_path = f"sources/{source_id}/{document_id}"

        # Convert bytes to a file-like object (MinIO expects a stream)
        content_stream = io.BytesIO(content)
        content_length = len(content)

        try:
            self._client.put_object(
                bucket_name=self._bucket_raw,
                object_name=minio_path,
                data=content_stream,
                length=content_length,
                content_type=content_type,
                # Metadata stored alongside the object — queryable without downloading content
                metadata={
                    "source-id": source_id,
                    "document-id": document_id,
                    "content-hash": content_hash,
                },
            )
            log.info(
                "Stored raw document",
                path=minio_path,
                size_kb=content_length // 1024,
            )
            return minio_path, content_hash

        except S3Error as e:
            log.error(
                "Failed to store document in MinIO", error=str(e), path=minio_path
            )
            raise

    def retrieve_raw_document(self, minio_path: str) -> bytes:
        """
        Retrieves a raw document from MinIO by its path.
        Used by the processing pipeline when embedding documents.
        """
        try:
            response = self._client.get_object(self._bucket_raw, minio_path)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except S3Error as e:
            log.error(
                "Failed to retrieve document from MinIO", error=str(e), path=minio_path
            )
            raise

    def store_chunks(self, document_id: str, chunks: list[dict]) -> str:
        """
        Stores processed text chunks as JSON in the processed bucket.

        Each chunk looks like:
        {
            "id": "chunk-uuid",
            "document_id": "doc-uuid",
            "text": "The actual text content of this chunk...",
            "chunk_index": 0,
            "metadata": { "title": "...", "url": "...", "published_at": "..." }
        }
        """
        minio_path = f"chunks/{document_id}.json"
        content = json.dumps(chunks, ensure_ascii=False, indent=2).encode("utf-8")
        content_stream = io.BytesIO(content)

        self._client.put_object(
            bucket_name=self._bucket_processed,
            object_name=minio_path,
            data=content_stream,
            length=len(content),
            content_type="application/json",
        )

        log.info("Stored chunks", document_id=document_id, chunk_count=len(chunks))
        return minio_path

    def delete_document(self, source_id: str, document_id: str):
        """Deletes a document and its chunks from MinIO."""
        raw_path = f"sources/{source_id}/{document_id}"
        chunk_path = f"chunks/{document_id}.json"

        for bucket, path in [
            (self._bucket_raw, raw_path),
            (self._bucket_processed, chunk_path),
        ]:
            try:
                self._client.remove_object(bucket, path)
            except S3Error:
                pass  # Ignore if already deleted


# Singleton instance — created once, reused across all requests
storage_service = StorageService()
