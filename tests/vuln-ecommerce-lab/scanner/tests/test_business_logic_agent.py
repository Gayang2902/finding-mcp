"""
Unit tests for BusinessLogicAgent.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from scanner.agents.business_logic_agent import BusinessLogicAgent
from scanner.config.settings import Settings
from scanner.config.test_users import TestUser
from scanner.models.scan_context import ScanContext
from scanner.models.vulnerability import Severity, VulnerabilityType


def _make_response(status: int, body: Any) -> httpx.Response:
    return httpx.Response(status_code=status, content=json.dumps(body).encode())


def _make_context() -> ScanContext:
    ctx = ScanContext(target_url="http://localhost:8080/api")
    customer = TestUser(alias="customer1", email="c1@test.com", password="pw", role="customer", token="tok", user_id=5)
    ctx.authenticated_users = {"customer1": customer}
    ctx.resource_ids = {
        "product_ids": [1, 2, 3],
        "order_ids": [101, 102, 103],
        "coupon_codes": ["SAVE10"],
        "payment_ids": [301],
        "address_ids": [201],
    }
    return ctx


def _make_agent(ctx: ScanContext) -> BusinessLogicAgent:
    http = MagicMock()
    llm = AsyncMock()
    llm.analyze_json = AsyncMock(return_value={"rule_violated": True, "confidence": 0.9, "severity": "HIGH"})
    settings = Settings()
    settings.enable_llm_analysis = False
    settings.verify_findings = False
    return BusinessLogicAgent(http, llm, ctx, settings)


class TestBusinessLogicAgent:

    @pytest.mark.asyncio
    async def test_detects_coupon_reuse(self) -> None:
        """Vulnerability when same coupon applies to two orders."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp_ok = _make_response(200, {"discount": 10, "orderId": 101})
        agent._http.post = AsyncMock(return_value=resp_ok)

        customer = ctx.authenticated_users["customer1"]
        findings = await agent._test_coupon_reuse(customer)

        assert len(findings) == 1
        assert findings[0].type == VulnerabilityType.BUSINESS_LOGIC_FLAW
        assert findings[0].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_no_coupon_reuse_finding_when_rejected(self) -> None:
        """No vulnerability when second coupon application is rejected."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp_ok = _make_response(200, {"discount": 10})
        resp_err = _make_response(400, {"error": "Coupon already used"})
        agent._http.post = AsyncMock(side_effect=[resp_ok, resp_err])

        findings = await agent._test_coupon_reuse(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_detects_zero_payment(self) -> None:
        """Vulnerability when zero-amount payment is accepted."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(200, {"id": 999, "status": "COMPLETED", "amount": 0})
        agent._http.post = AsyncMock(return_value=resp)

        customer = ctx.authenticated_users["customer1"]
        findings = await agent._test_zero_price_payment(customer)

        assert len(findings) == 1
        assert findings[0].severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_no_zero_payment_finding_when_rejected(self) -> None:
        """No vulnerability when zero payment is rejected."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(400, {"error": "Payment amount must be greater than 0"})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_zero_price_payment(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_detects_negative_cart_quantity(self) -> None:
        """Vulnerability when negative cart quantity is accepted."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(201, {"id": 5, "quantity": -5, "productId": 1})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_negative_quantity_in_cart(ctx.authenticated_users["customer1"])

        assert len(findings) == 1
        assert findings[0].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detects_overstock_quantity(self) -> None:
        """Vulnerability when quantity > stock is accepted."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(201, {"id": 5, "quantity": 999999, "productId": 1})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_order_with_overstock_quantity(ctx.authenticated_users["customer1"])

        assert len(findings) == 1
        assert findings[0].type == VulnerabilityType.BUSINESS_LOGIC_FLAW

    @pytest.mark.asyncio
    async def test_detects_duplicate_review(self) -> None:
        """Vulnerability when same product can be reviewed twice."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(201, {"id": 99, "rating": 5})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_duplicate_review(ctx.authenticated_users["customer1"])

        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM

    @pytest.mark.asyncio
    async def test_no_duplicate_review_when_rejected(self) -> None:
        """No vulnerability when second review is rejected."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp_ok = _make_response(201, {"id": 99, "rating": 5})
        resp_err = _make_response(409, {"error": "Already reviewed"})
        agent._http.post = AsyncMock(side_effect=[resp_ok, resp_err])

        findings = await agent._test_duplicate_review(ctx.authenticated_users["customer1"])

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_skips_without_authenticated_customer(self) -> None:
        """Agent should handle missing customer gracefully."""
        ctx = ScanContext(target_url="http://localhost:8080/api")
        ctx.authenticated_users = {}
        agent = _make_agent(ctx)

        findings = await agent.analyze()

        assert findings == []

    @pytest.mark.asyncio
    async def test_finding_has_cwe(self) -> None:
        """Business logic findings should include CWE-840."""
        ctx = _make_context()
        agent = _make_agent(ctx)

        resp = _make_response(200, {"id": 999, "status": "COMPLETED", "amount": 0})
        agent._http.post = AsyncMock(return_value=resp)

        findings = await agent._test_zero_price_payment(ctx.authenticated_users["customer1"])

        assert findings[0].cwe_id == "CWE-840"
