"""Tests for custom Prometheus metrics and structured logging."""

import json

import pytest
from unittest.mock import MagicMock
from prometheus_client import REGISTRY


def _get_counter_value(metric_name, labels=None):
    """Read the current value of a Prometheus counter/gauge."""
    # For counters, the sample name includes _total suffix
    # For gauges, the sample name matches the metric name
    target_names = {metric_name, f"{metric_name}_total"}
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name in target_names:
                if labels is None:
                    return sample.value
                if all(sample.labels.get(k) == v for k, v in labels.items()):
                    return sample.value
    return None


@pytest.fixture
def mock_llm(mocker):
    """Mock the LLM service for /ask endpoint."""
    mock = MagicMock()
    mock.answer_with_context.return_value = "The answer based on context."
    mocker.patch("app.api.routes.search.llm_service", mock)
    return mock


class TestRagMetrics:

    @pytest.mark.unit
    async def test_rag_query_increments_counter(self, client, mock_vector_store, mock_llm):
        mock_vector_store.search.return_value = [
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "source_id": "s1",
                "text": "test chunk",
                "title": "Test",
                "url": "https://example.com",
                "chunk_index": 0,
                "score": 0.9,
            }
        ]

        before = _get_counter_value("argus_rag_queries_total", {"status": "success"}) or 0

        response = await client.post("/api/search/ask", json={
            "query": "What is the EU AI Act?",
        })
        assert response.status_code == 200

        after = _get_counter_value("argus_rag_queries_total", {"status": "success"}) or 0
        assert after == before + 1


class TestCrawlMetrics:

    @pytest.mark.unit
    async def test_crawl_job_report_increments_counter(
        self, client, make_source, mock_vector_store, mock_storage
    ):
        source = (await client.post("/api/sources/", json=make_source())).json()

        before = _get_counter_value(
            "argus_crawl_jobs_total", {"status": "success", "source_type": "website"}
        ) or 0

        response = await client.post("/api/ingest/crawl-job", json={
            "source_id": source["id"],
            "status": "success",
            "documents_found": 3,
            "documents_indexed": 2,
            "duration_seconds": 5.0,
        })
        assert response.status_code == 201

        after = _get_counter_value(
            "argus_crawl_jobs_total", {"status": "success", "source_type": "website"}
        ) or 0
        assert after == before + 1


class TestSourceGauge:

    @pytest.mark.unit
    async def test_active_sources_gauge_increments_on_create(self, client, make_source):
        from app.services.metrics import active_sources_gauge

        before = active_sources_gauge._value.get()

        response = await client.post("/api/sources/", json=make_source())
        assert response.status_code == 201

        after = active_sources_gauge._value.get()
        assert after == before + 1


class TestMetricsEndpoint:

    @pytest.mark.unit
    async def test_metrics_endpoint_contains_argus_metrics(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200

        body = response.text
        assert "argus_rag_queries_total" in body
        assert "argus_crawl_jobs_total" in body
        assert "argus_documents_indexed_total" in body
        assert "argus_active_sources_total" in body


class TestLoggingConfig:

    @pytest.mark.unit
    def test_logging_outputs_json_in_production(self, capsys):
        from app.core.logging import configure_logging
        import structlog

        configure_logging(environment="production", log_level="info")
        logger = structlog.get_logger()
        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["event"] == "test_event"
        assert parsed["key"] == "value"
        assert "timestamp" in parsed
        assert "level" in parsed

        # Restore development logging so other tests aren't affected
        configure_logging(environment="development", log_level="warning")
