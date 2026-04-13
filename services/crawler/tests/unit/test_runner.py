import pytest
from unittest.mock import AsyncMock, patch

from crawler.runner import crawl_source, run_crawl_cycle, CrawlResult


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.ingest = AsyncMock(return_value="doc-id-1")
    client.update_last_crawled = AsyncMock()
    client.report_crawl_job = AsyncMock()
    client.get_active_sources = AsyncMock(return_value=[])
    return client


def make_source(source_type="website", **overrides):
    data = {
        "id": "src-1",
        "name": "Test Source",
        "url": "https://example.com",
        "source_type": source_type,
        "is_active": True,
    }
    data.update(overrides)
    return data


class TestCrawlSource:

    @pytest.mark.unit
    async def test_crawl_website_source_fetches_and_ingests(self, mock_client):
        source = make_source(source_type="website", url="https://example.com/page")

        with patch("crawler.runner.smart_fetch", AsyncMock(return_value=b"<html>page</html>")):
            result = await crawl_source(mock_client, source)

        assert result.ingested == 1
        assert result.failed == 0
        mock_client.ingest.assert_called_once_with(
            source_id="src-1",
            url="https://example.com/page",
            html=b"<html>page</html>",
            title=None,
        )
        mock_client.update_last_crawled.assert_called_once_with("src-1")

    @pytest.mark.unit
    async def test_crawl_rss_source_ingests_each_entry(self, mock_client):
        source = make_source(source_type="rss", url="https://example.com/feed.xml")

        rss_entries = [
            {"url": "https://example.com/1", "title": "Article 1"},
            {"url": "https://example.com/2", "title": "Article 2"},
            {"url": "https://example.com/3", "title": "Article 3"},
        ]

        with patch("crawler.runner.fetch_rss_entries", AsyncMock(return_value=rss_entries)), \
             patch("crawler.runner.smart_fetch", AsyncMock(return_value=b"<html></html>")):
            result = await crawl_source(mock_client, source)

        assert result.ingested == 3
        assert result.failed == 0
        assert mock_client.ingest.call_count == 3

    @pytest.mark.unit
    async def test_updates_last_crawled_even_with_failures(self, mock_client):
        """update_last_crawled should be called even when some URLs fail."""
        source = make_source(source_type="rss", url="https://example.com/feed.xml")

        rss_entries = [
            {"url": "https://example.com/1", "title": "Good"},
            {"url": "https://example.com/2", "title": "Bad"},
        ]

        async def flaky_fetch(url):
            if "2" in url:
                raise Exception("connection reset")
            return b"<html>ok</html>"

        with patch("crawler.runner.fetch_rss_entries", AsyncMock(return_value=rss_entries)), \
             patch("crawler.runner.smart_fetch", side_effect=flaky_fetch):
            result = await crawl_source(mock_client, source)

        assert result.ingested == 1
        assert result.failed == 1
        mock_client.update_last_crawled.assert_called_once_with("src-1")

    @pytest.mark.unit
    async def test_continues_on_single_url_failure(self, mock_client):
        """If one URL fails, the rest should still be attempted."""
        source = make_source(source_type="rss", url="https://example.com/feed.xml")

        rss_entries = [
            {"url": "https://example.com/fail", "title": "Fails"},
            {"url": "https://example.com/ok", "title": "Works"},
        ]

        call_order = []

        async def tracking_fetch(url):
            call_order.append(url)
            if "fail" in url:
                raise Exception("timeout")
            return b"<html>ok</html>"

        with patch("crawler.runner.fetch_rss_entries", AsyncMock(return_value=rss_entries)), \
             patch("crawler.runner.smart_fetch", side_effect=tracking_fetch):
            result = await crawl_source(mock_client, source)

        assert len(call_order) == 2
        assert result.ingested == 1
        assert result.failed == 1

    @pytest.mark.unit
    async def test_rss_passes_titles_to_ingest(self, mock_client):
        """RSS entry titles should be forwarded to the ingest call."""
        source = make_source(source_type="rss", url="https://example.com/feed.xml")

        rss_entries = [
            {"url": "https://example.com/1", "title": "My Article Title"},
        ]

        with patch("crawler.runner.fetch_rss_entries", AsyncMock(return_value=rss_entries)), \
             patch("crawler.runner.smart_fetch", AsyncMock(return_value=b"<html></html>")):
            await crawl_source(mock_client, source)

        mock_client.ingest.assert_called_once_with(
            source_id="src-1",
            url="https://example.com/1",
            html=b"<html></html>",
            title="My Article Title",
        )

    @pytest.mark.unit
    async def test_reports_crawl_job_on_success(self, mock_client):
        """report_crawl_job should be called with status='success' after clean crawl."""
        source = make_source(source_type="website", url="https://example.com/page")

        with patch("crawler.runner.smart_fetch", AsyncMock(return_value=b"<html></html>")):
            result = await crawl_source(mock_client, source)

        assert result.status == "success"
        mock_client.report_crawl_job.assert_called_once_with(
            source_id="src-1",
            crawl_status="success",
            documents_found=1,
            documents_indexed=1,
            duration_seconds=result.duration_seconds,
            error_message=None,
        )

    @pytest.mark.unit
    async def test_reports_crawl_job_on_failure(self, mock_client):
        """report_crawl_job should be called with status='failed' when source crawl fails."""
        source = make_source(source_type="website", url="https://example.com/page")

        with patch("crawler.runner.smart_fetch", AsyncMock(side_effect=Exception("connection reset"))):
            result = await crawl_source(mock_client, source)

        assert result.status == "success"  # Individual URL failures don't set source status to failed
        assert result.failed == 1
        mock_client.report_crawl_job.assert_called_once()
        call_kwargs = mock_client.report_crawl_job.call_args[1]
        assert call_kwargs["documents_found"] == 1
        assert call_kwargs["documents_indexed"] == 0

    @pytest.mark.unit
    async def test_reports_failed_status_on_source_level_error(self, mock_client):
        """report_crawl_job should have status='failed' when the source itself errors."""
        source = make_source(source_type="rss", url="https://example.com/feed.xml")

        with patch("crawler.runner.fetch_rss_entries", AsyncMock(side_effect=Exception("DNS resolution failed"))):
            result = await crawl_source(mock_client, source)

        assert result.status == "failed"
        assert result.error_message == "DNS resolution failed"
        mock_client.report_crawl_job.assert_called_once()
        call_kwargs = mock_client.report_crawl_job.call_args[1]
        assert call_kwargs["crawl_status"] == "failed"
        assert call_kwargs["error_message"] == "DNS resolution failed"

    @pytest.mark.unit
    async def test_crawl_serp_source_fetches_results(self, mock_client):
        """SERP source type should call fetch_serp_results and ingest each result."""
        source = make_source(
            source_type="serp",
            search_query="EU AI Act news",
            url="https://google.com/search",
        )

        serp_entries = [
            {"url": "https://example.com/1", "title": "AI Act Result 1"},
            {"url": "https://example.com/2", "title": "AI Act Result 2"},
            {"url": "https://example.com/3", "title": "AI Act Result 3"},
        ]

        with patch("crawler.runner.fetch_serp_results", AsyncMock(return_value=serp_entries)) as mock_serp, \
             patch("crawler.runner.smart_fetch", AsyncMock(return_value=b"<html>content</html>")):
            result = await crawl_source(mock_client, source)

        mock_serp.assert_called_once_with(
            query="EU AI Act news",
            searxng_url=mock_serp.call_args[1]["searxng_url"],  # from settings
        )
        assert result.ingested == 3
        assert result.failed == 0
        assert mock_client.ingest.call_count == 3


class TestRunCrawlCycle:

    @pytest.mark.unit
    async def test_processes_all_sources(self, mock_client):
        sources = [
            make_source(id="src-1", url="https://a.com"),
            make_source(id="src-2", url="https://b.com"),
            make_source(id="src-3", url="https://c.com"),
        ]
        mock_client.get_active_sources = AsyncMock(return_value=sources)

        with patch("crawler.runner.crawl_source", AsyncMock(return_value=CrawlResult(source_id="x", ingested=1))) as mock_crawl:
            results = await run_crawl_cycle(mock_client)

        assert mock_crawl.call_count == 3
        assert len(results) == 3

    @pytest.mark.unit
    async def test_continues_if_one_source_fails(self, mock_client):
        sources = [
            make_source(id="src-1", url="https://a.com"),
            make_source(id="src-2", url="https://b.com"),
            make_source(id="src-3", url="https://c.com"),
        ]
        mock_client.get_active_sources = AsyncMock(return_value=sources)

        call_count = 0

        async def flaky_crawl(client, source):
            nonlocal call_count
            call_count += 1
            if source["id"] == "src-1":
                raise Exception("source-1 exploded")
            return CrawlResult(source_id=source["id"], ingested=1)

        with patch("crawler.runner.crawl_source", side_effect=flaky_crawl):
            results = await run_crawl_cycle(mock_client)

        assert call_count == 3
        assert len(results) == 2  # src-1 failed, src-2 and src-3 succeeded

    @pytest.mark.unit
    async def test_empty_sources_returns_empty(self, mock_client):
        mock_client.get_active_sources = AsyncMock(return_value=[])

        results = await run_crawl_cycle(mock_client)

        assert results == []
