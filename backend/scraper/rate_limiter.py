import asyncio
import time
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

from backend.core.config import settings


class RateLimitedClient:
    def __init__(self, delay: float | None = None):
        self.delay = delay if delay is not None else settings.scraper_delay_seconds
        self._lock = asyncio.Lock()
        self._last_request: float | None = None
        self.client = httpx.AsyncClient(timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()

    async def _wait_if_needed(self) -> None:
        if self._last_request is None:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)

    async def fetch(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> str:
        headers = {"User-Agent": settings.scraper_user_agent, **(headers or {})}

        async with self._lock:
            await self._wait_if_needed()

            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=(retry_if_exception_type(httpx.HTTPError) | retry_if_result(lambda r: r is None)),
                reraise=True,
            ):
                response = await self.client.get(url, params=params, headers=headers)
                if response.status_code >= 400:
                    raise httpx.HTTPStatusError("HTTP error", request=response.request, response=response)
                html = response.text
                if not html:
                    continue
                self._last_request = time.monotonic()
                return html

        raise httpx.HTTPError("Failed to fetch URL after retries")
