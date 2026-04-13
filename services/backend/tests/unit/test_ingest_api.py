import base64

import pytest


class TestIngestEndpoint:

    @pytest.mark.unit
    async def test_ingest_returns_202(self, client, make_source, mock_vector_store, mock_storage):
        # Create a source first
        source = (await client.post("/api/sources/", json=make_source())).json()

        payload = {
            "source_id": source["id"],
            "url": "https://example.com/article",
            "html_content": base64.b64encode(b"<html><body>Test</body></html>").decode(),
            "title": "Test Article",
        }
        response = await client.post("/api/ingest/", json=payload)
        assert response.status_code == 202

        data = response.json()
        assert "document_id" in data
        assert data["status"] == "processing"

    @pytest.mark.unit
    async def test_ingest_invalid_base64_returns_400(self, client, make_source, mock_vector_store, mock_storage):
        source = (await client.post("/api/sources/", json=make_source())).json()

        payload = {
            "source_id": source["id"],
            "url": "https://example.com/article",
            "html_content": "not-valid-base64!!!",
        }
        response = await client.post("/api/ingest/", json=payload)
        assert response.status_code == 400
        assert "base64" in response.json()["detail"]

    @pytest.mark.unit
    async def test_ingest_nonexistent_source_returns_404(self, client, mock_vector_store, mock_storage):
        payload = {
            "source_id": "nonexistent-source-id",
            "url": "https://example.com/article",
            "html_content": base64.b64encode(b"<html></html>").decode(),
        }
        response = await client.post("/api/ingest/", json=payload)
        assert response.status_code == 404

    @pytest.mark.unit
    async def test_ingest_without_title(self, client, make_source, mock_vector_store, mock_storage):
        source = (await client.post("/api/sources/", json=make_source())).json()

        payload = {
            "source_id": source["id"],
            "url": "https://example.com/article",
            "html_content": base64.b64encode(b"<html><body>No title</body></html>").decode(),
        }
        response = await client.post("/api/ingest/", json=payload)
        assert response.status_code == 202


class TestUpdateLastCrawled:

    @pytest.mark.unit
    async def test_patch_returns_200(self, client, make_source, mock_vector_store):
        source = (await client.post("/api/sources/", json=make_source())).json()

        response = await client.patch(f"/api/sources/{source['id']}/last-crawled")
        assert response.status_code == 200

        data = response.json()
        assert data["last_crawled_at"] is not None

    @pytest.mark.unit
    async def test_patch_nonexistent_source_returns_404(self, client, mock_vector_store):
        response = await client.patch("/api/sources/nonexistent/last-crawled")
        assert response.status_code == 404
