"""
Unit tests for IDORAgent.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from scanner.agents.idor_agent import IDORAgent
from scanner.config.settings import Settings
from scanner.config.test_users import TestUser
from scanner.models.scan_context import ScanContext
from scanner.models.vulnerability import Severity, VulnerabilityType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_response(status: int, body: Any) -> httpx.Response:
    """Create a mock httpx.Response."""
    import json
    content = json.dumps(body).encode()
    resp = httpx.Response(status_code=status, content=content)
    return resp


def _make_context(users: dict) -> ScanContext:
    ctx = ScanContext(target_url="http://localhost:8080/api")
    ctx.authenticated_users = users
    ctx.resource_ids = {
        "order_ids": [101, 102],
        "address_ids": [201, 202],
        "payment_ids": [301],
        "review_ids": [401],
        "notification_ids": [501],
        "cart_item_ids": [601],
        "user_ids": [1, 2],
    }
    return ctx


def _make_users() -> dict:
    u1 = TestUser(alias="customer1", email="c1@test.com", password="pw", role="customer", token="tok1", user_id=1)
    u2 = TestUser(alias="customer2", email="c2@test.com", password="pw", role="customer", token="tok2", user_id=2)
    return {"customer1": u1, "customer2": u2}


def _make_agent(ctx: ScanContext) -> IDORAgent:
    http_client = MagicMock()
    llm_client = AsyncMock()
    llm_client.analyze_json = AsyncMock(return_value={
        "is_idor": True,
        "confidence": 0.9,
        "sensitive_data_exposed": ["email"],
        "impact": "Test impact",
        "severity": "HIGH",
        "explanation": "Test",
    })
    settings = Settings()
    settings.enable_llm_analysis = False  # avoid real LLM calls in tests
    settings.verify_findings = False
    return IDORAgent(http_client, llm_client, ctx, settings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIDORDetection:
    """Test core IDOR detection logic."""

    @pytest.mark.asyncio
    async def test_idor_detected_when_user_b_gets_200(self) -> None:
        """IDOR is reported when user B successfully accesses user A's resource."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        resp_a = _make_response(200, {"id": 101, "userId": 1, "items": [], "total": 50.0})
        resp_b = _make_response(200, {"id": 101, "userId": 1, "items": [], "total": 50.0})  # same data

        agent._http.make_request = AsyncMock(side_effect=[resp_a, resp_b])

        vuln = await agent._cross_user_test(
            method="GET",
            path="/orders/101",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="order #101",
            expected_behavior="403",
        )

        assert vuln is not None
        assert vuln.type == VulnerabilityType.IDOR
        assert vuln.endpoint == "/orders/101"
        assert vuln.method == "GET"

    @pytest.mark.asyncio
    async def test_no_idor_when_user_b_gets_403(self) -> None:
        """No IDOR reported when user B correctly receives 403."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        resp_a = _make_response(200, {"id": 101, "userId": 1})
        resp_b = _make_response(403, {"error": "Forbidden"})

        agent._http.make_request = AsyncMock(side_effect=[resp_a, resp_b])

        vuln = await agent._cross_user_test(
            method="GET",
            path="/orders/101",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="order #101",
            expected_behavior="403",
        )

        assert vuln is None

    @pytest.mark.asyncio
    async def test_no_idor_when_user_b_gets_404(self) -> None:
        """No IDOR reported when user B receives 404."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        resp_a = _make_response(200, {"id": 101})
        resp_b = _make_response(404, {"error": "Not Found"})

        agent._http.make_request = AsyncMock(side_effect=[resp_a, resp_b])

        vuln = await agent._cross_user_test(
            method="GET",
            path="/orders/101",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="order #101",
            expected_behavior="404",
        )

        assert vuln is None

    @pytest.mark.asyncio
    async def test_idor_severity_high_for_sensitive_data(self) -> None:
        """IDOR on payment endpoint should be HIGH or CRITICAL."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        payment_body = {"id": 301, "userId": 1, "amount": 99.99, "creditCard": "****1234"}
        resp_a = _make_response(200, payment_body)
        resp_b = _make_response(200, payment_body)

        agent._http.make_request = AsyncMock(side_effect=[resp_a, resp_b])

        vuln = await agent._cross_user_test(
            method="GET",
            path="/payments/301",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="payment #301",
            expected_behavior="403",
            severity_override=Severity.HIGH,
        )

        assert vuln is not None
        assert vuln.severity in (Severity.HIGH, Severity.CRITICAL)

    @pytest.mark.asyncio
    async def test_skips_when_only_one_customer(self) -> None:
        """Agent skips IDOR tests when fewer than 2 customer users exist."""
        users = {"customer1": _make_users()["customer1"]}
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        findings = await agent.analyze()

        assert findings == []

    @pytest.mark.asyncio
    async def test_idor_write_method_is_high_severity(self) -> None:
        """PUT/DELETE IDOR should default to HIGH severity."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        resp_a = _make_response(200, {"id": 201})
        resp_b = _make_response(200, {"id": 201})

        agent._http.make_request = AsyncMock(side_effect=[resp_a, resp_b])

        vuln = await agent._cross_user_test(
            method="PUT",
            path="/addresses/201",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="address #201",
            expected_behavior="403",
            request_body={"street": "HACKED"},
        )

        assert vuln is not None
        assert vuln.severity in (Severity.HIGH, Severity.CRITICAL)

    @pytest.mark.asyncio
    async def test_network_error_returns_none(self) -> None:
        """Network errors should not raise — return None gracefully."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        agent._http.make_request = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        vuln = await agent._cross_user_test(
            method="GET",
            path="/orders/101",
            user_a=users["customer1"],
            user_b=users["customer2"],
            resource_desc="order #101",
            expected_behavior="403",
        )

        assert vuln is None

    def test_vulnerability_has_required_fields(self) -> None:
        """Created vulnerabilities must have all required fields populated."""
        users = _make_users()
        ctx = _make_context(users)
        agent = _make_agent(ctx)

        from scanner.models.vulnerability import Evidence
        evidence = Evidence(
            request_method="GET",
            request_url="http://localhost:8080/api/orders/101",
            response_status=200,
            expected_behavior="403",
            actual_behavior="200",
        )
        vuln = agent._create_vulnerability(
            vuln_type=VulnerabilityType.IDOR,
            severity=Severity.HIGH,
            title="Test IDOR",
            endpoint="/orders/101",
            method="GET",
            evidence=evidence,
            confidence=0.9,
        )

        assert vuln.id
        assert vuln.type == VulnerabilityType.IDOR
        assert vuln.agent_name == "idor_agent"
        assert vuln.cwe_id is None  # not set in this call
        assert 0 <= vuln.confidence <= 1
