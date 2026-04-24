# =============================================================================
# tests/unit/test_sources_api.py
# =============================================================================
# Tests for the /api/sources endpoints.
#
# These use the test client fixture from conftest.py which:
# - Replaces PostgreSQL with in-memory SQLite
# - Bypasses Keycloak auth (returns mock_user)
# - Doesn't need MinIO or Milvus
#
# This lets us test the API logic in isolation, very fast.
# =============================================================================

import pytest


class TestListSources:

    @pytest.mark.unit
    async def test_returns_empty_list_for_new_user(self, client):
        response = await client.get("/api/sources/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.unit
    async def test_returns_only_own_sources(self, client, make_source):
        # Create a source
        await client.post("/api/sources/", json=make_source())

        response = await client.get("/api/sources/")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestCreateSource:

    @pytest.mark.unit
    async def test_creates_source_successfully(self, client, make_source):
        payload = make_source({"name": "Test Blog", "url": "https://test.example.com"})
        response = await client.post("/api/sources/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Blog"
        assert data["url"].rstrip("/") == "https://test.example.com"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.unit
    async def test_rejects_invalid_url(self, client, make_source):
        payload = make_source({"url": "not-a-valid-url"})
        response = await client.post("/api/sources/", json=payload)

        # Pydantic validation fails → 422 Unprocessable Entity
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_serp_source_requires_search_query(self, client, make_source):
        payload = make_source({
            "source_type": "serp",
            "search_query": None,  # Missing!
        })
        response = await client.post("/api/sources/", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_serp_source_with_query_succeeds(self, client, make_source):
        payload = make_source({
            "source_type": "serp",
            "search_query": "EU AI Act news",
            "url": "https://google.com/search",
        })
        response = await client.post("/api/sources/", json=payload)
        assert response.status_code == 201

    @pytest.mark.unit
    async def test_default_crawl_interval_is_360_minutes(self, client, make_source):
        payload = make_source()
        del payload["crawl_interval_minutes"]  # Don't send this field
        response = await client.post("/api/sources/", json=payload)

        assert response.status_code == 201
        assert response.json()["crawl_interval_minutes"] == 360

    @pytest.mark.unit
    async def test_source_limit_is_enforced(self, client, make_source):
        """Users can't create more than max_sources_per_user sources."""
        from app.core.config import get_settings
        settings = get_settings()
        limit = settings.max_sources_per_user

        # Create up to the limit
        for i in range(limit):
            r = await client.post("/api/sources/", json=make_source({
                "url": f"https://example{i}.com"
            }))
            assert r.status_code == 201

        # One more should fail
        r = await client.post("/api/sources/", json=make_source({
            "url": "https://one-too-many.com"
        }))
        assert r.status_code == 429  # Too Many Requests


class TestGetSource:

    @pytest.mark.unit
    async def test_get_existing_source(self, client, make_source):
        created = (await client.post("/api/sources/", json=make_source())).json()
        source_id = created["id"]

        response = await client.get(f"/api/sources/{source_id}")
        assert response.status_code == 200
        assert response.json()["id"] == source_id

    @pytest.mark.unit
    async def test_get_nonexistent_source_returns_404(self, client):
        response = await client.get("/api/sources/does-not-exist")
        assert response.status_code == 404


class TestUpdateSource:

    @pytest.mark.unit
    async def test_update_name(self, client, make_source):
        created = (await client.post("/api/sources/", json=make_source())).json()
        source_id = created["id"]

        response = await client.put(
            f"/api/sources/{source_id}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.unit
    async def test_deactivate_source(self, client, make_source):
        created = (await client.post("/api/sources/", json=make_source())).json()
        source_id = created["id"]

        response = await client.put(
            f"/api/sources/{source_id}",
            json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    @pytest.mark.unit
    async def test_partial_update_preserves_other_fields(self, client, make_source):
        """Updating name should not change crawl_interval_minutes."""
        created = (await client.post("/api/sources/", json=make_source({
            "name": "Original",
            "crawl_interval_minutes": 720,
        }))).json()

        response = await client.put(
            f"/api/sources/{created['id']}",
            json={"name": "New Name"}
        )
        data = response.json()
        assert data["name"] == "New Name"
        assert data["crawl_interval_minutes"] == 720  # Unchanged


class TestDeleteSource:

    @pytest.mark.unit
    async def test_delete_existing_source(self, client, make_source, mock_vector_store):
        created = (await client.post("/api/sources/", json=make_source())).json()
        source_id = created["id"]

        response = await client.delete(f"/api/sources/{source_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/sources/{source_id}")
        assert get_response.status_code == 404

    @pytest.mark.unit
    async def test_delete_nonexistent_source_returns_404(self, client):
        response = await client.delete("/api/sources/ghost-source")
        assert response.status_code == 404


class TestGetCrawlJobs:

    @pytest.mark.unit
    async def test_returns_crawl_jobs_for_source(self, client, make_source, mock_vector_store, mock_storage):
        source = (await client.post("/api/sources/", json=make_source())).json()

        # Create a crawl job via the ingest endpoint
        await client.post("/api/ingest/crawl-job", json={
            "source_id": source["id"],
            "status": "success",
            "documents_found": 3,
            "documents_indexed": 2,
            "duration_seconds": 5.0,
        })

        response = await client.get(f"/api/sources/{source['id']}/crawl-jobs")
        assert response.status_code == 200

        jobs = response.json()
        assert len(jobs) == 1
        assert jobs[0]["source_id"] == source["id"]
        assert jobs[0]["status"] == "success"
        assert jobs[0]["documents_found"] == 3
        assert jobs[0]["documents_indexed"] == 2
        assert jobs[0]["duration_seconds"] == 5.0

    @pytest.mark.unit
    async def test_returns_empty_for_no_jobs(self, client, make_source, mock_vector_store):
        source = (await client.post("/api/sources/", json=make_source())).json()

        response = await client.get(f"/api/sources/{source['id']}/crawl-jobs")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.unit
    async def test_nonexistent_source_returns_404(self, client, mock_vector_store):
        response = await client.get("/api/sources/nonexistent/crawl-jobs")
        assert response.status_code == 404
