import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from crawler.fetcher import fetch_with_httpx, smart_fetch, USER_AGENT


class TestFetchWithHttpx:

    @pytest.mark.unit
    async def test_returns_bytes(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_with_httpx("https://example.com")

        assert isinstance(result, bytes)
        assert result == b"<html><body>Hello</body></html>"

    @pytest.mark.unit
    async def test_sends_user_agent(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.fetcher.httpx.AsyncClient", return_value=mock_client) as mock_cls:
            await fetch_with_httpx("https://example.com")

        # Verify User-Agent was passed in client construction
        call_kwargs = mock_cls.call_args
        assert call_kwargs[1]["headers"]["User-Agent"] == USER_AGENT

    @pytest.mark.unit
    async def test_retries_on_failure(self):
        """Should retry up to 3 times on transport errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html>OK</html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.TransportError("connection reset"),
                httpx.TransportError("timeout"),
                mock_response,
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("crawler.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_with_httpx("https://example.com")

        assert result == b"<html>OK</html>"
        assert mock_client.get.call_count == 3


class TestFetchWithPlaywright:

    @pytest.mark.unit
    async def test_returns_bytes(self):
        """Playwright fetch should return UTF-8 encoded bytes of page content."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Rendered JS</body></html>")
        mock_page.goto = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()

        mock_pw_instance = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw_ctx = AsyncMock()
        mock_pw_ctx.__aenter__ = AsyncMock(return_value=mock_pw_instance)
        mock_pw_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_async_pw = MagicMock(return_value=mock_pw_ctx)

        with patch("playwright.async_api.async_playwright", mock_async_pw):
            from crawler.fetcher import fetch_with_playwright
            result = await fetch_with_playwright("https://example.com")

        assert isinstance(result, bytes)
        assert b"Rendered JS" in result

    @pytest.mark.unit
    async def test_closes_browser_on_success(self):
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.goto = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        mock_pw_instance = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw_ctx = AsyncMock()
        mock_pw_ctx.__aenter__ = AsyncMock(return_value=mock_pw_instance)
        mock_pw_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_async_pw = MagicMock(return_value=mock_pw_ctx)

        with patch("playwright.async_api.async_playwright", mock_async_pw):
            from crawler.fetcher import fetch_with_playwright
            await fetch_with_playwright("https://example.com")

        mock_browser.close.assert_called_once()


class TestSmartFetch:

    @pytest.mark.unit
    async def test_uses_httpx_for_normal_pages(self):
        """When httpx returns a large enough response, Playwright is not called."""
        large_content = b"<html>" + b"x" * 5000 + b"</html>"

        with patch("crawler.fetcher.fetch_with_httpx", AsyncMock(return_value=large_content)) as mock_httpx, \
             patch("crawler.fetcher.fetch_with_playwright", AsyncMock()) as mock_pw:
            result = await smart_fetch("https://example.com")

        assert result == large_content
        mock_httpx.assert_called_once_with("https://example.com")
        mock_pw.assert_not_called()

    @pytest.mark.unit
    async def test_falls_back_to_playwright_for_short_response(self):
        """When httpx response is too short, fall back to Playwright."""
        short_content = b"<html>tiny</html>"
        pw_content = b"<html>" + b"full content " * 200 + b"</html>"

        with patch("crawler.fetcher.fetch_with_httpx", AsyncMock(return_value=short_content)), \
             patch("crawler.fetcher.fetch_with_playwright", AsyncMock(return_value=pw_content)) as mock_pw:
            result = await smart_fetch("https://example.com")

        assert result == pw_content
        mock_pw.assert_called_once_with("https://example.com")

    @pytest.mark.unit
    async def test_falls_back_to_playwright_on_httpx_error(self):
        """When httpx fails entirely, fall back to Playwright."""
        pw_content = b"<html>from playwright</html>"

        with patch("crawler.fetcher.fetch_with_httpx", AsyncMock(side_effect=Exception("connection failed"))), \
             patch("crawler.fetcher.fetch_with_playwright", AsyncMock(return_value=pw_content)) as mock_pw:
            result = await smart_fetch("https://example.com")

        assert result == pw_content
        mock_pw.assert_called_once()
