import base64
import time

import httpx
import structlog

log = structlog.get_logger()


class BackendClient:
    """HTTP client for communicating with the Argus backend API."""

    def __init__(
        self,
        base_url: str,
        api_token: str = "",
        keycloak_url: str = "",
        keycloak_client_id: str = "",
        keycloak_client_secret: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self._keycloak_token_url = (
            f"{keycloak_url}/protocol/openid-connect/token" if keycloak_url else ""
        )
        self._client_id = keycloak_client_id
        self._client_secret = keycloak_client_secret
        self._static_token = api_token
        self._access_token: str = ""
        self._token_expires_at: float = 0
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def _get_token(self) -> str:
        if not self._keycloak_token_url:
            return self._static_token

        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        response = await self.client.post(
            self._keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 300)
        log.info("Obtained service account token", expires_in=data.get("expires_in"))
        return self._access_token

    async def _headers(self) -> dict[str, str]:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def get_active_sources(self) -> list[dict]:
        response = await self.client.get("/api/sources/", headers=await self._headers())
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
        payload = {
            "source_id": source_id,
            "url": url,
            "html_content": base64.b64encode(html).decode(),
        }
        if title:
            payload["title"] = title

        response = await self.client.post(
            "/api/ingest/", json=payload, headers=await self._headers()
        )
        response.raise_for_status()
        data = response.json()
        log.info("Ingested document", document_id=data["document_id"], url=url)
        return data["document_id"]

    async def update_last_crawled(self, source_id: str) -> None:
        response = await self.client.patch(
            f"/api/sources/{source_id}/last-crawled", headers=await self._headers()
        )
        response.raise_for_status()
        log.info("Updated last_crawled_at", source_id=source_id)

    async def report_crawl_job(
        self,
        source_id: str,
        crawl_status: str,
        documents_found: int,
        documents_indexed: int,
        duration_seconds: float,
        error_message: str | None = None,
    ) -> str | None:
        payload = {
            "source_id": source_id,
            "status": crawl_status,
            "documents_found": documents_found,
            "documents_indexed": documents_indexed,
            "duration_seconds": round(duration_seconds, 2),
        }
        if error_message:
            payload["error_message"] = error_message

        try:
            response = await self.client.post(
                "/api/ingest/crawl-job", json=payload, headers=await self._headers()
            )
            response.raise_for_status()
            data = response.json()
            log.info(
                "Reported crawl job",
                crawl_job_id=data["crawl_job_id"],
                source_id=source_id,
            )
            return data["crawl_job_id"]
        except Exception as e:
            log.warning("Failed to report crawl job", source_id=source_id, error=str(e))
            return None

    async def close(self) -> None:
        await self.client.aclose()
