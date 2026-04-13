import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawler.serp import fetch_serp_results


class TestFetchSerpResults:

    @pytest.mark.unit
    async def test_parses_searxng_response(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"url": "https://example.com/1", "title": "Result 1"},
                {"url": "https://example.com/2", "title": "Result 2"},
                {"url": "https://example.com/3", "title": "Result 3"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.serp.httpx.AsyncClient", return_value=mock_client):
            results = await fetch_serp_results("test query", "http://localhost:8080")

        assert len(results) == 3
        assert results[0] == {"url": "https://example.com/1", "title": "Result 1"}
        assert results[2] == {"url": "https://example.com/3", "title": "Result 3"}

    @pytest.mark.unit
    async def test_limits_to_10_results(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"url": f"https://example.com/{i}", "title": f"Result {i}"}
                for i in range(15)
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.serp.httpx.AsyncClient", return_value=mock_client):
            results = await fetch_serp_results("test query", "http://localhost:8080")

        assert len(results) == 10

    @pytest.mark.unit
    async def test_skips_entries_without_url(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"url": "https://example.com/1", "title": "Good"},
                {"title": "No URL"},  # missing "url" key
                {"url": "https://example.com/3", "title": "Also Good"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.serp.httpx.AsyncClient", return_value=mock_client):
            results = await fetch_serp_results("test query", "http://localhost:8080")

        assert len(results) == 2

    @pytest.mark.unit
    async def test_passes_query_params(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.serp.httpx.AsyncClient", return_value=mock_client):
            await fetch_serp_results("EU AI Act", "http://searxng:8080")

        call_kwargs = mock_client.get.call_args
        assert call_kwargs[0][0] == "http://searxng:8080/search"
        assert call_kwargs[1]["params"]["q"] == "EU AI Act"
        assert call_kwargs[1]["params"]["format"] == "json"
