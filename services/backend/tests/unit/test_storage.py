import pytest
from unittest.mock import MagicMock, patch
from minio.error import S3Error


@pytest.fixture
def mock_minio_client():
    return MagicMock()


@pytest.fixture
def storage(mock_minio_client):
    with patch("app.services.storage.get_settings") as mock_settings, \
         patch("app.services.storage.Minio", return_value=mock_minio_client):
        settings = MagicMock()
        settings.minio_endpoint = "localhost:9000"
        settings.minio_access_key = "test-key"
        settings.minio_secret_key = "test-secret"
        settings.minio_secure = False
        settings.minio_bucket_raw = "raw-bucket"
        settings.minio_bucket_processed = "processed-bucket"
        mock_settings.return_value = settings

        from app.services.storage import StorageService
        svc = StorageService()

    return svc


class TestEnsureBuckets:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_creates_missing_buckets(self, storage, mock_minio_client):
        mock_minio_client.bucket_exists.return_value = False

        await storage.ensure_buckets()

        assert mock_minio_client.make_bucket.call_count == 2
        mock_minio_client.make_bucket.assert_any_call("raw-bucket")
        mock_minio_client.make_bucket.assert_any_call("processed-bucket")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_existing_buckets(self, storage, mock_minio_client):
        mock_minio_client.bucket_exists.return_value = True

        await storage.ensure_buckets()

        mock_minio_client.make_bucket.assert_not_called()


class TestStoreRawDocument:

    @pytest.mark.unit
    def test_stores_document_and_returns_path_and_hash(self, storage, mock_minio_client):
        content = b"<html><body>Hello</body></html>"

        path, content_hash = storage.store_raw_document(
            source_id="src-1",
            document_id="doc-1",
            content=content,
        )

        assert path == "sources/src-1/doc-1"
        assert len(content_hash) == 64  # SHA-256 hex digest
        mock_minio_client.put_object.assert_called_once()

    @pytest.mark.unit
    def test_content_hash_is_deterministic(self, storage, mock_minio_client):
        content = b"same content"

        _, hash1 = storage.store_raw_document("s1", "d1", content)
        _, hash2 = storage.store_raw_document("s1", "d2", content)

        assert hash1 == hash2

    @pytest.mark.unit
    def test_different_content_produces_different_hash(self, storage, mock_minio_client):
        _, hash1 = storage.store_raw_document("s1", "d1", b"content A")
        _, hash2 = storage.store_raw_document("s1", "d2", b"content B")

        assert hash1 != hash2

    @pytest.mark.unit
    def test_raises_on_s3_error(self, storage, mock_minio_client):
        mock_minio_client.put_object.side_effect = S3Error(
            "PutObject", "raw-bucket", "", "", "", ""
        )

        with pytest.raises(S3Error):
            storage.store_raw_document("s1", "d1", b"data")


class TestRetrieveRawDocument:

    @pytest.mark.unit
    def test_retrieves_content(self, storage, mock_minio_client):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>content</html>"
        mock_minio_client.get_object.return_value = mock_response

        result = storage.retrieve_raw_document("sources/src-1/doc-1")

        assert result == b"<html>content</html>"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    @pytest.mark.unit
    def test_raises_on_s3_error(self, storage, mock_minio_client):
        mock_minio_client.get_object.side_effect = S3Error(
            "GetObject", "raw-bucket", "", "", "", ""
        )

        with pytest.raises(S3Error):
            storage.retrieve_raw_document("sources/src-1/doc-1")


class TestStoreChunks:

    @pytest.mark.unit
    def test_stores_chunks_as_json(self, storage, mock_minio_client):
        chunks = [
            {"id": "c1", "text": "chunk one"},
            {"id": "c2", "text": "chunk two"},
        ]

        path = storage.store_chunks("doc-1", chunks)

        assert path == "chunks/doc-1.json"
        mock_minio_client.put_object.assert_called_once()
        call_kwargs = mock_minio_client.put_object.call_args
        assert call_kwargs[1]["content_type"] == "application/json"


class TestDeleteDocument:

    @pytest.mark.unit
    def test_deletes_raw_and_chunks(self, storage, mock_minio_client):
        storage.delete_document("src-1", "doc-1")

        assert mock_minio_client.remove_object.call_count == 2
        mock_minio_client.remove_object.assert_any_call("raw-bucket", "sources/src-1/doc-1")
        mock_minio_client.remove_object.assert_any_call("processed-bucket", "chunks/doc-1.json")

    @pytest.mark.unit
    def test_ignores_s3_error_on_delete(self, storage, mock_minio_client):
        mock_minio_client.remove_object.side_effect = S3Error(
            "RemoveObject", "raw-bucket", "", "", "", ""
        )

        # Should not raise
        storage.delete_document("src-1", "doc-1")
