"""
Async HTTP client with retry, rate limiting, and logging.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter for async contexts."""

    def __init__(self, rps: float) -> None:
        self._interval = 1.0 / rps if rps > 0 else 0.0
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()


class AsyncHTTPClient:
    """
    Async HTTP client wrapping httpx with:
    - Automatic base-URL prefixing
    - Bearer token injection
    - Exponential-backoff retry
    - Rate limiting
    - Request/response logging
    - Response-time tracking
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retry_attempts: int = 3,
        rate_limit_rps: float = 20.0,
        proxy: Optional[str] = None,
        verify_ssl: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._rate_limiter = RateLimiter(rate_limit_rps)
        self._proxy = proxy
        self._verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None
        self._request_count = 0

    async def __aenter__(self) -> "AsyncHTTPClient":
        await self._init_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def _init_client(self) -> None:
        transport = None
        if self._proxy:
            transport = httpx.AsyncHTTPTransport(proxy=self._proxy)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            verify=self._verify_ssl,
            transport=transport,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    async def make_request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        raw_url: bool = False,
    ) -> httpx.Response:
        """
        Send an HTTP request with retry and rate limiting.

        Args:
            method: HTTP verb (GET, POST, PUT, DELETE, …)
            path: Relative path or absolute URL
            token: JWT bearer token (optional)
            params: Query parameters
            body: Request body (serialized to JSON)
            headers: Additional headers
            raw_url: If True, skip base-URL prefixing

        Returns:
            httpx.Response
        """
        if self._client is None:
            await self._init_client()

        url = path if raw_url else self._build_url(path)
        merged_headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            merged_headers["Authorization"] = f"Bearer {token}"
        if headers:
            merged_headers.update(headers)

        await self._rate_limiter.acquire()

        return await self._send_with_retry(method.upper(), url, merged_headers, params, body)

    async def _send_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict],
        body: Optional[Any],
    ) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.retry_attempts + 2):
            try:
                start = time.monotonic()
                assert self._client is not None
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body,
                )
                elapsed = (time.monotonic() - start) * 1000
                self._request_count += 1
                logger.debug(
                    "%s %s -> %d (%.0f ms, attempt %d)",
                    method, url, response.status_code, elapsed, attempt,
                )
                return response
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt <= self.retry_attempts:
                    wait = min(2 ** (attempt - 1), 8)
                    logger.warning("Request failed (attempt %d/%d): %s — retrying in %.1fs",
                                   attempt, self.retry_attempts + 1, exc, wait)
                    await asyncio.sleep(wait)
                else:
                    logger.error("Request failed after %d attempts: %s %s — %s",
                                 attempt, method, url, exc)

        raise httpx.RequestError(f"All {self.retry_attempts + 1} attempts failed") from last_exc

    async def get(self, path: str, token: Optional[str] = None, **kwargs: Any) -> httpx.Response:
        return await self.make_request("GET", path, token=token, **kwargs)

    async def post(self, path: str, token: Optional[str] = None, **kwargs: Any) -> httpx.Response:
        return await self.make_request("POST", path, token=token, **kwargs)

    async def put(self, path: str, token: Optional[str] = None, **kwargs: Any) -> httpx.Response:
        return await self.make_request("PUT", path, token=token, **kwargs)

    async def delete(self, path: str, token: Optional[str] = None, **kwargs: Any) -> httpx.Response:
        return await self.make_request("DELETE", path, token=token, **kwargs)

    @property
    def request_count(self) -> int:
        return self._request_count
