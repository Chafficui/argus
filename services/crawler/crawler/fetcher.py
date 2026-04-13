# =============================================================================
# crawler/fetcher.py
# =============================================================================
# Page fetching with httpx (fast) and Playwright (JS-rendered) fallback.
#
# smart_fetch(url) is the main entry point:
#   1. Try httpx first (fast, lightweight)
#   2. If response is suspiciously short (<1000 bytes), fall back to Playwright
#      (the page probably requires JavaScript to render content)
# =============================================================================

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = structlog.get_logger()

USER_AGENT = (
    "Mozilla/5.0 (compatible; ArgusBot/0.1; +https://github.com/argus)"
)

# Minimum response size before we suspect JS-rendered content
MIN_CONTENT_LENGTH = 1000


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
    reraise=True,
)
async def fetch_with_httpx(url: str) -> bytes:
    """
    Fetch a page using async httpx.
    Retries 3 times with exponential backoff on transport/HTTP errors.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        log.info(
            "Fetched with httpx",
            url=url,
            status=response.status_code,
            size=len(response.content),
        )
        return response.content


async def fetch_with_playwright(url: str) -> bytes:
    """
    Fetch a page using headless Chromium via Playwright.
    Waits for network idle — handles JS-rendered SPAs.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=USER_AGENT)
            await page.goto(url, wait_until="networkidle", timeout=45000)
            content = await page.content()
            html_bytes = content.encode("utf-8")
            log.info(
                "Fetched with Playwright",
                url=url,
                size=len(html_bytes),
            )
            return html_bytes
        finally:
            await browser.close()


async def smart_fetch(url: str) -> bytes:
    """
    Fetch a page intelligently:
    - Try httpx first (fast)
    - If response is too short, fall back to Playwright (JS rendering)
    """
    try:
        content = await fetch_with_httpx(url)
        if len(content) >= MIN_CONTENT_LENGTH:
            return content
        log.info(
            "httpx response too short, falling back to Playwright",
            url=url,
            size=len(content),
        )
    except Exception as e:
        log.warning(
            "httpx fetch failed, falling back to Playwright",
            url=url,
            error=str(e),
        )

    return await fetch_with_playwright(url)
