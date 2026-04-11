import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestHealthEndpoints:

    @pytest.mark.unit
    async def test_health_returns_ok(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.unit
    async def test_health_ready_all_ok(self):
        """When all deps respond, returns 200."""
        mock_session = AsyncMock()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_session
        mock_cm.__aexit__.return_value = False

        mock_factory = MagicMock(return_value=mock_cm)

        mock_collection = MagicMock()
        mock_collection.num_entities = 100

        mock_vs = MagicMock()
        mock_vs.collection = mock_collection

        mock_httpx_response = MagicMock()
        mock_httpx_response.raise_for_status = MagicMock()

        with patch("app.main.AsyncSessionLocal", mock_factory), \
             patch("app.main.vector_store", mock_vs), \
             patch("app.main.httpx.get", return_value=mock_httpx_response):

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["postgres"] == "ok"
        assert data["dependencies"]["milvus"] == "ok"
        assert data["dependencies"]["ollama"] == "ok"

    @pytest.mark.unit
    async def test_health_ready_returns_503_when_dep_fails(self):
        """When a dependency is down, returns 503."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("connection refused")

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_session
        mock_cm.__aexit__.return_value = False

        mock_factory = MagicMock(return_value=mock_cm)

        mock_vs = MagicMock()
        mock_vs.collection = None  # Not connected

        with patch("app.main.AsyncSessionLocal", mock_factory), \
             patch("app.main.vector_store", mock_vs), \
             patch("app.main.httpx.get", side_effect=Exception("ollama down")):

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        detail = data["detail"]
        assert "not ready" in detail["status"]
        assert "error" in detail["dependencies"]["postgres"]
        assert "error" in detail["dependencies"]["milvus"]
        assert "error" in detail["dependencies"]["ollama"]
