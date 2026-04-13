# =============================================================================
# crawler/backend_client.py
# =============================================================================
# All HTTP calls from the crawler to the backend go through this class.
# Keeps the runner and fetcher clean — they never touch httpx directly.
# =============================================================================

import base64

import httpx
import structlog

log = structlog.get_logger()


class BackendClient:
    """HTTP client for communicating with the Argus backend API."""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=30.0,
        )

    async def get_active_sources(self) -> list[dict]:
        """Fetch all active sources from GET /api/sources/."""
        response = await self.client.get("/api/sources/")
        response.raise_for_status()
        sources = response.json()
        return [s for s in sources if s.get("is_active", True)]

    async def ingest(
        self,
        source_id: str,
        url: str,
        html: bytes,
        title: str | None = None,
    ) -> str:
        """
        Send fetched HTML to POST /api/ingest/.
        Returns the document_id assigned by the backend.
        """
        payload = {
            "source_id": source_id,
            "url": url,
            "html_content": base64.b64encode(html).decode(),
        }
        if title:
            payload["title"] = title

        response = await self.client.post("/api/ingest/", json=payload)
        response.raise_for_status()
        data = response.json()
        log.info("Ingested document", document_id=data["document_id"], url=url)
        return data["document_id"]

    async def update_last_crawled(self, source_id: str) -> None:
        """Update the last_crawled_at timestamp via PATCH."""
        response = await self.client.patch(
            f"/api/sources/{source_id}/last-crawled"
        )
        response.raise_for_status()
        log.info("Updated last_crawled_at", source_id=source_id)

    async def close(self) -> None:
        """Always close the httpx client when done."""
        await self.client.aclose()
