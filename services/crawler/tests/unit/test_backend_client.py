import base64

import pytest
from unittest.mock import AsyncMock, MagicMock

from crawler.backend_client import BackendClient


@pytest.fixture
def client():
    """Create a BackendClient with a mocked httpx client (static token mode)."""
    bc = BackendClient(base_url="http://localhost:8000", api_token="test-token")
    bc.client = AsyncMock()
    return bc


class TestGetActiveSources:

    @pytest.mark.unit
    async def test_returns_list(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "src-1", "name": "Blog", "is_active": True},
            {"id": "src-2", "name": "News", "is_active": True},
        ]
        mock_response.raise_for_status = MagicMock()
        client.client.get = AsyncMock(return_value=mock_response)

        result = await client.get_active_sources()

        assert len(result) == 2
        assert result[0]["id"] == "src-1"
        client.client.get.assert_called_once()

    @pytest.mark.unit
    async def test_filters_inactive_sources(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "src-1", "name": "Active", "is_active": True},
            {"id": "src-2", "name": "Inactive", "is_active": False},
        ]
        mock_response.raise_for_status = MagicMock()
        client.client.get = AsyncMock(return_value=mock_response)

        result = await client.get_active_sources()

        assert len(result) == 1
        assert result[0]["id"] == "src-1"


class TestIngest:

    @pytest.mark.unit
    async def test_base64_encodes_html(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"document_id": "doc-1", "status": "processing"}
        mock_response.raise_for_status = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        html = b"<html><body>Test</body></html>"
        await client.ingest(source_id="src-1", url="https://example.com", html=html)

        call_kwargs = client.client.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["html_content"] == base64.b64encode(html).decode()

    @pytest.mark.unit
    async def test_sends_auth_header(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"document_id": "doc-1", "status": "processing"}
        mock_response.raise_for_status = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        await client.ingest(source_id="src-1", url="https://example.com", html=b"<html></html>")

        call_kwargs = client.client.post.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.unit
    async def test_returns_document_id(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"document_id": "doc-42", "status": "processing"}
        mock_response.raise_for_status = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        doc_id = await client.ingest(
            source_id="src-1", url="https://example.com", html=b"<html></html>"
        )

        assert doc_id == "doc-42"


class TestClose:

    @pytest.mark.unit
    async def test_close_calls_aclose(self, client):
        client.client.aclose = AsyncMock()
        await client.close()
        client.client.aclose.assert_called_once()


class TestUpdateLastCrawled:

    @pytest.mark.unit
    async def test_calls_patch(self, client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        client.client.patch = AsyncMock(return_value=mock_response)

        await client.update_last_crawled("src-1")

        call_args = client.client.patch.call_args
        assert call_args[0][0] == "/api/sources/src-1/last-crawled"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"


class TestReportCrawlJob:

    @pytest.mark.unit
    async def test_posts_crawl_job_report(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"crawl_job_id": "cj-1"}
        mock_response.raise_for_status = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.report_crawl_job(
            source_id="src-1",
            crawl_status="success",
            documents_found=5,
            documents_indexed=4,
            duration_seconds=12.345,
        )

        assert result == "cj-1"
        call_kwargs = client.client.post.call_args
        assert call_kwargs[0][0] == "/api/ingest/crawl-job"
        payload = call_kwargs[1]["json"]
        assert payload["source_id"] == "src-1"
        assert payload["status"] == "success"
        assert payload["documents_found"] == 5
        assert payload["documents_indexed"] == 4
        assert payload["duration_seconds"] == 12.35

    @pytest.mark.unit
    async def test_includes_error_message_when_provided(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"crawl_job_id": "cj-2"}
        mock_response.raise_for_status = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        await client.report_crawl_job(
            source_id="src-1",
            crawl_status="failed",
            documents_found=0,
            documents_indexed=0,
            duration_seconds=1.0,
            error_message="Connection refused",
        )

        payload = client.client.post.call_args[1]["json"]
        assert payload["error_message"] == "Connection refused"

    @pytest.mark.unit
    async def test_returns_none_on_error(self, client):
        client.client.post = AsyncMock(side_effect=Exception("network error"))

        result = await client.report_crawl_job(
            source_id="src-1",
            crawl_status="success",
            documents_found=1,
            documents_indexed=1,
            duration_seconds=2.0,
        )

        assert result is None
