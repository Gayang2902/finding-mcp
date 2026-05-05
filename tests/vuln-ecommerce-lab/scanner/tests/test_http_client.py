"""
Unit tests for AsyncHTTPClient.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from scanner.utils.http_client import AsyncHTTPClient, RateLimiter


class TestRateLimiter:

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_first_call_immediately(self) -> None:
        limiter = RateLimiter(rps=100.0)
        import time
        t0 = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.05  # should be nearly instant

    @pytest.mark.asyncio
    async def test_zero_rps_no_wait(self) -> None:
        """RPS=0 disables rate limiting."""
        limiter = RateLimiter(rps=0.0)
        await limiter.acquire()  # should not block

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_interval(self) -> None:
        """Two rapid calls at 10 RPS should take ~100ms apart."""
        import time
        limiter = RateLimiter(rps=10.0)
        await limiter.acquire()
        t0 = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.08  # at least 80ms (some tolerance)


class TestAsyncHTTPClient:

    def test_build_url_relative_path(self) -> None:
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        assert client._build_url("/orders") == "http://localhost:8080/api/orders"
        assert client._build_url("orders") == "http://localhost:8080/api/orders"

    def test_build_url_absolute_passthrough(self) -> None:
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        assert client._build_url("http://other.host/path") == "http://other.host/path"

    @pytest.mark.asyncio
    async def test_make_request_injects_bearer_token(self) -> None:
        """Bearer token is added to Authorization header."""
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        await client._init_client()

        captured_headers = {}

        async def fake_request(**kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, content=b"{}")

        client._client.request = fake_request

        await client.make_request("GET", "/test", token="my-jwt-token")

        assert captured_headers.get("Authorization") == "Bearer my-jwt-token"
        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_no_token_no_auth_header(self) -> None:
        """No Authorization header when token is None."""
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        await client._init_client()

        captured_headers = {}

        async def fake_request(**kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, content=b"{}")

        client._client.request = fake_request

        await client.make_request("GET", "/test", token=None)

        assert "Authorization" not in captured_headers
        await client.close()

    @pytest.mark.asyncio
    async def test_request_count_increments(self) -> None:
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        await client._init_client()

        async def fake_request(**kwargs):
            return httpx.Response(200, content=b"{}")

        client._client.request = fake_request

        await client.make_request("GET", "/a")
        await client.make_request("GET", "/b")

        assert client.request_count == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self) -> None:
        """Client retries on ConnectError up to retry_attempts times."""
        client = AsyncHTTPClient(
            base_url="http://localhost:8080/api",
            retry_attempts=2,
            rate_limit_rps=0,
        )
        await client._init_client()

        call_count = 0

        async def fake_request(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("refused")
            return httpx.Response(200, content=b"{}")

        client._client.request = fake_request

        resp = await client.make_request("GET", "/retry-test")

        assert resp.status_code == 200
        assert call_count == 3  # failed twice, succeeded on 3rd
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_after_all_retries_exhausted(self) -> None:
        """Raises RequestError when all retry attempts fail."""
        client = AsyncHTTPClient(
            base_url="http://localhost:8080/api",
            retry_attempts=1,
            rate_limit_rps=0,
        )
        await client._init_client()

        async def always_fail(**kwargs):
            raise httpx.ConnectError("always fails")

        client._client.request = always_fail

        with pytest.raises(httpx.RequestError):
            await client.make_request("GET", "/fail")

        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Client can be used as async context manager."""
        async with AsyncHTTPClient(base_url="http://localhost:8080/api") as client:
            assert client._client is not None
        assert client._client is None  # closed after exit

    @pytest.mark.asyncio
    async def test_convenience_methods(self) -> None:
        """get/post/put/delete are thin wrappers around make_request."""
        client = AsyncHTTPClient(base_url="http://localhost:8080/api")
        await client._init_client()

        calls = []

        async def fake_request(**kwargs):
            calls.append(kwargs.get("method"))
            return httpx.Response(200, content=b"{}")

        client._client.request = fake_request

        await client.get("/a")
        await client.post("/b")
        await client.put("/c")
        await client.delete("/d")

        assert calls == ["GET", "POST", "PUT", "DELETE"]
        await client.close()
