"""
Unit tests for ParameterTamperingAgent.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from scanner.agents.parameter_tampering_agent import ParameterTamperingAgent
from scanner.config.settings import Settings
from scanner.config.test_users import TestUser
from scanner.models.scan_context import ScanContext
from scanner.models.vulnerability import Severity, VulnerabilityType


def _make_response(status: int, body: Any) -> httpx.Response:
    content = json.dumps(body).encode()
    return httpx.Response(status_code=status, content=content)


def _make_context() -> ScanContext:
    ctx = ScanContext(target_url="http://localhost:8080/api")
    customer = TestUser(alias="customer1", email="c1@test.com", password="pw", role="customer", token="tok1", user_id=10)
    admin = TestUser(alias="admin", email="admin@test.com", password="pw", role="admin", token="admtok", user_id=1)
    ctx.authenticated_users = {"customer1": customer, "admin": admin}
    ctx.resource_ids = {
        "product_ids": [1, 2],
        "order_ids": [101],
        "address_ids": [201],
        "payment_ids": [301],
    }
    return ctx


def _make_agent(ctx: ScanContext) -> ParameterTamperingAgent:
    http = MagicMock()
    llm = AsyncMock()
    llm.analyze_json = AsyncMock(return_value={
        "tampering_detected": True,
        "confidence": 0.9,
        "server_accepted_value": True,
        "severity": "CRITICAL",
    })
    settings = Settings()
    settings.enable_llm_analysis = False
    settings.verify_findings = False
    return ParameterTamperingAgent(http, llm, ctx, settings)


class TestParameterTamperingAgent:

    @pytest.mark.asyncio
    async def test_detects_price_injection_when_server_accepts(self) -> None:
        """Vulnerability reported when server returns 201 with tampered price reflected."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        # Normal response
        resp_normal = _make_response(201, {"id": 1, "productId": 1, "quantity": 1, "price": 29.99})
        # Tampered response — server echoes back the low price
        resp_tampered = _make_response(201, {"id": 2, "productId": 1, "quantity": 1, "price": 0.01})

        agent._http.post = AsyncMock(side_effect=[resp_normal, resp_tampered])

        findings = await agent._test_cart_price_injection(ctx.authenticated_users["customer1"])

        assert len(findings) == 1
        assert findings[0].type == VulnerabilityType.PARAMETER_TAMPERING
        assert findings[0].severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_no_finding_when_price_not_reflected(self) -> None:
        """No vulnerability when server uses server-side price."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp_normal = _make_response(201, {"id": 1, "price": 29.99})
        # Server ignored client price — uses real price
        resp_tampered = _make_response(201, {"id": 2, "price": 29.99})

        agent._http.post = AsyncMock(side_effect=[resp_normal, resp_tampered])

        findings = await agent._test_cart_price_injection(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_detects_role_elevation_when_role_changed(self) -> None:
        """Vulnerability reported when server accepts role=ADMIN in update."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp_with_admin = _make_response(200, {"id": 10, "role": "ADMIN", "email": "c1@test.com"})
        agent._http.make_request = AsyncMock(return_value=resp_with_admin)

        customer = ctx.authenticated_users["customer1"]
        findings = await agent._test_role_elevation(customer)

        assert len(findings) >= 1
        assert any(v.type == VulnerabilityType.PARAMETER_TAMPERING for v in findings)
        assert all(v.severity == Severity.CRITICAL for v in findings)

    @pytest.mark.asyncio
    async def test_no_role_elevation_when_role_unchanged(self) -> None:
        """No vulnerability when server ignores role field."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        # Server keeps original customer role
        resp = _make_response(200, {"id": 10, "role": "CUSTOMER", "email": "c1@test.com"})
        agent._http.make_request = AsyncMock(return_value=resp)

        findings = await agent._test_role_elevation(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_detects_negative_quantity(self) -> None:
        """Vulnerability when negative quantity is accepted."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(201, {"id": 99, "quantity": -1, "productId": 1})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_negative_quantity(ctx.authenticated_users["customer1"])

        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM

    @pytest.mark.asyncio
    async def test_no_negative_quantity_finding_on_rejection(self) -> None:
        """No vulnerability when server rejects negative quantity."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(400, {"error": "Quantity must be positive"})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_negative_quantity(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_zero_payment_detection(self) -> None:
        """Vulnerability when zero payment is accepted."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(200, {"id": 999, "orderId": 101, "amount": 0, "status": "COMPLETED"})
        agent._http.post = AsyncMock(return_value=resp)

        customer = ctx.authenticated_users["customer1"]
        findings = await agent._test_payment_amount_tampering(customer)

        assert len(findings) >= 1

    @pytest.mark.asyncio
    async def test_skips_when_no_product_ids_fallback(self) -> None:
        """Uses fallback product ID 1 when no product IDs collected."""
        ctx = _make_context()
        ctx.resource_ids["product_ids"] = []
        agent = _make_agent(ctx)

        resp_normal = _make_response(201, {"id": 1, "price": 5.99})
        resp_tampered = _make_response(201, {"id": 2, "price": 5.99})
        agent._http.post = AsyncMock(side_effect=[resp_normal, resp_tampered])

        # Should not raise — should use fallback product_id=1
        findings = await agent._test_cart_price_injection(ctx.authenticated_users["customer1"])
        # No injection detected (price not reflected as tampered)
        assert isinstance(findings, list)
