"""
Business Logic Agent — detects flaws in application business rules.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.llm_prompts import analyze_rule_violation, generate_attack_scenarios
from scanner.models.vulnerability import Severity, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)

CWE_BUSINESS_LOGIC = "CWE-840"


class BusinessLogicAgent(BaseAnalysisAgent):
    """
    Tests business rule enforcement:
    - Coupon abuse (reuse, multiple, expired)
    - Order/quantity edge cases
    - Payment manipulation
    - Review constraints
    - Cart edge cases
    """

    name = "business_logic_agent"
    description = "Detects business logic vulnerabilities and rule enforcement failures"
    vuln_types = [VulnerabilityType.BUSINESS_LOGIC_FLAW]

    async def analyze(self) -> List[Vulnerability]:
        self._log("Starting business logic analysis")
        findings: List[Vulnerability] = []

        customer = self._ctx.get_user("customer1") or self._ctx.get_user_by_role("customer")
        if not customer or not customer.token:
            self._log("No authenticated customer — skipping business logic tests")
            return findings

        customer2 = self._ctx.get_user("customer2")

        findings += await self._test_coupon_reuse(customer)
        findings += await self._test_multiple_coupons(customer)
        findings += await self._test_expired_coupon(customer)
        findings += await self._test_zero_price_payment(customer)
        findings += await self._test_order_with_overstock_quantity(customer)
        findings += await self._test_negative_quantity_in_cart(customer)
        findings += await self._test_empty_cart_checkout(customer)
        findings += await self._test_cancel_delivered_order(customer)
        findings += await self._test_duplicate_review(customer)
        findings += await self._test_review_without_purchase(customer)
        findings += await self._test_refund_exceeds_payment(customer)

        self._log("Business logic analysis complete: %d findings", len(findings))
        for v in findings:
            self._log_finding(v)
            self._ctx.add_finding(v)

        return findings

    # ------------------------------------------------------------------
    # Coupon tests
    # ------------------------------------------------------------------

    async def _test_coupon_reuse(self, customer: Any) -> List[Vulnerability]:
        """Apply the same coupon twice to check if reuse is prevented."""
        order_ids = self._get_ids("order_ids")
        if len(order_ids) < 2:
            return []

        coupon_codes = self._get_ids("coupon_codes")
        code = coupon_codes[0] if coupon_codes else "SAVE10"

        results = []
        for order_id in order_ids[:2]:
            try:
                resp = await self._http.post(
                    "/coupons/apply",
                    token=customer.token,
                    body={"code": code, "orderId": order_id},
                )
                results.append((order_id, resp.status_code, _safe_json(resp)))
            except Exception:
                continue

        # Both applications succeeded → coupon can be reused
        both_success = len(results) == 2 and all(200 <= r[1] < 300 for r in results)
        if not both_success:
            return []

        return [self._create_vulnerability(
            vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
            severity=Severity.HIGH,
            title="Business Logic: Coupon can be applied to multiple orders",
            endpoint="/coupons/apply",
            method="POST",
            evidence=self._build_evidence(
                method="POST",
                url=f"{self._ctx.target_url}/coupons/apply",
                response_status=results[1][1],
                response_body=results[1][2],
                request_body={"code": code, "orderId": order_ids[1]},
                expected_behavior="Second application of same coupon should be rejected",
                actual_behavior=f"Coupon '{code}' applied to {len(results)} orders successfully",
            ),
            description=(
                f"Coupon code '{code}' can be applied to multiple orders by the same user. "
                "There is no per-user usage limit enforcement."
            ),
            reproduction_steps=[
                f"1. Apply coupon '{code}' to order #{order_ids[0]}",
                f"2. Apply the same coupon to order #{order_ids[1]}",
                "3. Observe both applications succeed",
            ],
            impact="Users can reuse discount coupons across multiple orders, causing revenue loss.",
            remediation=(
                "Track coupon usage per user. Reject second application if the coupon "
                "has already been used by the same user (or if maxUses is reached)."
            ),
            confidence=0.9,
            cwe_id=CWE_BUSINESS_LOGIC,
        )]

    async def _test_multiple_coupons(self, customer: Any) -> List[Vulnerability]:
        """Apply multiple different coupons to the same order."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        order_id = order_ids[0]
        test_codes = ["SAVE10", "DISCOUNT20", "WELCOME15"]

        successes = []
        for code in test_codes:
            try:
                resp = await self._http.post(
                    "/coupons/apply",
                    token=customer.token,
                    body={"code": code, "orderId": order_id},
                )
                if 200 <= resp.status_code < 300:
                    successes.append(code)
            except Exception:
                continue

        if len(successes) < 2:
            return []

        return [self._create_vulnerability(
            vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
            severity=Severity.HIGH,
            title="Business Logic: Multiple coupons can be applied to a single order",
            endpoint="/coupons/apply",
            method="POST",
            evidence=self._build_evidence(
                method="POST",
                url=f"{self._ctx.target_url}/coupons/apply",
                response_status=200,
                request_body={"code": successes[-1], "orderId": order_id},
                expected_behavior="Only one coupon allowed per order",
                actual_behavior=f"Multiple coupons applied: {', '.join(successes)}",
            ),
            description=f"Multiple coupons ({', '.join(successes)}) were successfully applied to order #{order_id}.",
            reproduction_steps=[
                f"1. Apply coupon SAVE10 to order #{order_id}",
                f"2. Apply coupon DISCOUNT20 to the same order",
                "3. Both succeed — stacked discounts applied",
            ],
            impact="Users can stack multiple coupons for near-zero or zero-cost orders.",
            remediation="Enforce one-coupon-per-order policy. Reject if order already has a coupon applied.",
            confidence=0.85,
            cwe_id=CWE_BUSINESS_LOGIC,
        )]

    async def _test_expired_coupon(self, customer: Any) -> List[Vulnerability]:
        """Try to use an expired coupon."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        # Try common expired/test coupon codes
        expired_codes = ["EXPIRED10", "OLD2023", "TEST100"]

        for code in expired_codes:
            try:
                resp = await self._http.post(
                    "/coupons/apply",
                    token=customer.token,
                    body={"code": code, "orderId": order_ids[0]},
                )
                if 200 <= resp.status_code < 300:
                    return [self._create_vulnerability(
                        vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                        severity=Severity.MEDIUM,
                        title=f"Business Logic: Expired coupon '{code}' accepted",
                        endpoint="/coupons/apply",
                        method="POST",
                        evidence=self._build_evidence(
                            method="POST",
                            url=f"{self._ctx.target_url}/coupons/apply",
                            response_status=resp.status_code,
                            response_body=_safe_json(resp),
                            request_body={"code": code, "orderId": order_ids[0]},
                            expected_behavior="Expired coupon should be rejected",
                            actual_behavior=f"HTTP {resp.status_code} — expired coupon accepted",
                        ),
                        description=f"Expired coupon '{code}' was accepted by the server.",
                        reproduction_steps=[
                            f"1. Obtain an expired coupon code (e.g. '{code}')",
                            f"2. POST /coupons/apply with the expired code",
                            "3. Observe discount is applied",
                        ],
                        impact="Users can exploit expired promotional coupons for unauthorized discounts.",
                        remediation="Validate coupon expiration date server-side on every application attempt.",
                        confidence=0.8,
                        cwe_id=CWE_BUSINESS_LOGIC,
                    )]
            except Exception:
                continue

        return []

    # ------------------------------------------------------------------
    # Payment tests
    # ------------------------------------------------------------------

    async def _test_zero_price_payment(self, customer: Any) -> List[Vulnerability]:
        """POST /payments — send amount=0."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        try:
            resp = await self._http.post(
                "/payments",
                token=customer.token,
                body={"orderId": order_ids[0], "amount": 0, "method": "CREDIT_CARD"},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.CRITICAL,
                title="Business Logic: Zero-value payment accepted",
                endpoint="/payments",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/payments",
                    response_status=resp.status_code,
                    response_body=_safe_json(resp),
                    request_body={"orderId": order_ids[0], "amount": 0, "method": "CREDIT_CARD"},
                    expected_behavior="Amount=0 payment should be rejected",
                    actual_behavior=f"HTTP {resp.status_code} — zero-value payment accepted",
                ),
                description="The payment endpoint accepts amount=0, allowing free orders.",
                reproduction_steps=[
                    f"1. Create an order (order #{order_ids[0]})",
                    "2. POST /payments with amount: 0",
                    "3. Observe payment accepted — order marked as paid",
                ],
                impact="Attacker can mark any order as paid without paying anything.",
                remediation="Reject payments where amount <= 0. Validate amount server-side against order total.",
                confidence=0.95,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []

    async def _test_refund_exceeds_payment(self, customer: Any) -> List[Vulnerability]:
        """POST /payments/{id}/refund — request refund > original amount."""
        payment_ids = self._get_ids("payment_ids")
        if not payment_ids:
            return []

        try:
            resp = await self._http.post(
                f"/payments/{payment_ids[0]}/refund",
                token=customer.token,
                body={"amount": 999999.99, "reason": "test"},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            body = _safe_json(resp)
            refund_amount = (body or {}).get("refundAmount") or (body or {}).get("amount")
            if refund_amount and float(refund_amount) > 100:
                return [self._create_vulnerability(
                    vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                    severity=Severity.HIGH,
                    title="Business Logic: Refund amount exceeds original payment",
                    endpoint=f"/payments/{payment_ids[0]}/refund",
                    method="POST",
                    evidence=self._build_evidence(
                        method="POST",
                        url=f"{self._ctx.target_url}/payments/{payment_ids[0]}/refund",
                        response_status=resp.status_code,
                        response_body=body,
                        request_body={"amount": 999999.99, "reason": "test"},
                        expected_behavior="Refund cannot exceed original payment amount",
                        actual_behavior=f"Refund of ${refund_amount} approved",
                    ),
                    description="The refund endpoint does not cap refund amount at the original payment value.",
                    reproduction_steps=[
                        f"1. Make a payment (e.g. $50)",
                        f"2. POST /payments/{payment_ids[0]}/refund with amount: 999999.99",
                        "3. Observe refund approved for the requested amount",
                    ],
                    impact="Attackers can request refunds larger than they paid, effectively stealing money.",
                    remediation="Cap refund amount at the original payment amount. Validate server-side.",
                    confidence=0.88,
                    cwe_id=CWE_BUSINESS_LOGIC,
                )]
        return []

    # ------------------------------------------------------------------
    # Cart / Order tests
    # ------------------------------------------------------------------

    async def _test_order_with_overstock_quantity(self, customer: Any) -> List[Vulnerability]:
        """POST /cart/items — quantity > available stock."""
        product_ids = self._get_ids("product_ids")
        product_id = product_ids[0] if product_ids else 1

        try:
            resp = await self._http.post(
                "/cart/items",
                token=customer.token,
                body={"productId": product_id, "quantity": 999999},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.MEDIUM,
                title="Business Logic: Order quantity exceeds available stock",
                endpoint="/cart/items",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/cart/items",
                    response_status=resp.status_code,
                    response_body=_safe_json(resp),
                    request_body={"productId": product_id, "quantity": 999999},
                    expected_behavior="Should reject quantity > stock",
                    actual_behavior=f"HTTP {resp.status_code} — quantity 999999 accepted",
                ),
                description="Items can be added to cart in quantities exceeding available stock.",
                reproduction_steps=[
                    f"1. POST /cart/items with productId={product_id} and quantity=999999",
                    "2. Observe the item is added without stock validation",
                ],
                impact="Inventory overselling — orders may fail fulfillment, causing customer dissatisfaction.",
                remediation="Validate quantity against current stock level when adding to cart and at checkout.",
                confidence=0.85,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []

    async def _test_negative_quantity_in_cart(self, customer: Any) -> List[Vulnerability]:
        """Add negative quantity — may result in credit."""
        product_ids = self._get_ids("product_ids")
        product_id = product_ids[0] if product_ids else 1

        try:
            resp = await self._http.post(
                "/cart/items",
                token=customer.token,
                body={"productId": product_id, "quantity": -5},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.HIGH,
                title="Business Logic: Negative cart quantity accepted",
                endpoint="/cart/items",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/cart/items",
                    response_status=resp.status_code,
                    response_body=_safe_json(resp),
                    request_body={"productId": product_id, "quantity": -5},
                    expected_behavior="Negative quantity should be rejected (400 Bad Request)",
                    actual_behavior=f"HTTP {resp.status_code} — negative quantity accepted",
                ),
                description=(
                    "Negative quantity can be added to the cart. "
                    "This may result in negative order totals, inventory manipulation, or credit fraud."
                ),
                reproduction_steps=[
                    "1. POST /cart/items with quantity: -5",
                    "2. Checkout — observe negative total or unexpected behavior",
                ],
                impact="Negative quantities may produce negative totals, effectively creating store credit.",
                remediation="Validate quantity > 0 server-side. Return 400 for invalid quantities.",
                confidence=0.9,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []

    async def _test_empty_cart_checkout(self, customer: Any) -> List[Vulnerability]:
        """Try to checkout with an empty cart."""
        address_ids = self._get_ids("address_ids")
        address_id = address_ids[0] if address_ids else 1

        # First, clear the cart
        try:
            await self._http.delete("/cart", token=customer.token)
        except Exception:
            pass

        try:
            resp = await self._http.post(
                "/orders",
                token=customer.token,
                body={"addressId": address_id},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.MEDIUM,
                title="Business Logic: Order created from empty cart",
                endpoint="/orders",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/orders",
                    response_status=resp.status_code,
                    response_body=_safe_json(resp),
                    request_body={"addressId": address_id},
                    expected_behavior="Cannot checkout with empty cart",
                    actual_behavior=f"HTTP {resp.status_code} — empty order created",
                ),
                description="An order can be created when the cart is empty, producing a zero-item order.",
                reproduction_steps=[
                    "1. Clear the cart (DELETE /cart)",
                    "2. POST /orders",
                    "3. Observe order created with no items",
                ],
                impact="Creates invalid orders that pollute order management and may cause processing errors.",
                remediation="Validate that cart is non-empty before creating an order.",
                confidence=0.8,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []

    async def _test_cancel_delivered_order(self, customer: Any) -> List[Vulnerability]:
        """Try to cancel an already-delivered order."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        # Try cancelling each known order — one might be DELIVERED
        for order_id in order_ids[:3]:
            # First check order status
            try:
                status_resp = await self._http.get(f"/orders/{order_id}", token=customer.token)
                if status_resp.status_code != 200:
                    continue
                order_data = _safe_json(status_resp)
                if not order_data:
                    continue
                order_status = order_data.get("status", "")
                if order_status not in ("DELIVERED", "COMPLETED"):
                    continue
            except Exception:
                continue

            try:
                resp = await self._http.post(
                    f"/orders/{order_id}/cancel",
                    token=customer.token,
                )
            except Exception:
                continue

            if 200 <= resp.status_code < 300:
                return [self._create_vulnerability(
                    vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                    severity=Severity.HIGH,
                    title=f"Business Logic: Delivered order #{order_id} can be cancelled",
                    endpoint=f"/orders/{order_id}/cancel",
                    method="POST",
                    evidence=self._build_evidence(
                        method="POST",
                        url=f"{self._ctx.target_url}/orders/{order_id}/cancel",
                        response_status=resp.status_code,
                        response_body=_safe_json(resp),
                        expected_behavior="Cannot cancel an already-delivered order",
                        actual_behavior=f"HTTP {resp.status_code} — delivered order cancelled",
                    ),
                    description=f"Order #{order_id} with status DELIVERED was successfully cancelled.",
                    reproduction_steps=[
                        f"1. Identify a delivered order (order #{order_id})",
                        f"2. POST /orders/{order_id}/cancel",
                        "3. Observe cancellation accepted despite delivered status",
                    ],
                    impact="Fraudulent refunds — customers can receive items and then cancel orders for a refund.",
                    remediation="Enforce order state machine: only PENDING/PROCESSING orders can be cancelled.",
                    confidence=0.92,
                    cwe_id=CWE_BUSINESS_LOGIC,
                )]

        return []

    async def _test_duplicate_review(self, customer: Any) -> List[Vulnerability]:
        """Submit the same review twice for the same product."""
        product_ids = self._get_ids("product_ids")
        product_id = product_ids[0] if product_ids else 1

        review_body = {"productId": product_id, "rating": 5, "comment": "Great product!"}

        results = []
        for _ in range(2):
            try:
                resp = await self._http.post("/reviews", token=customer.token, body=review_body)
                results.append(resp.status_code)
            except Exception:
                break

        if len(results) == 2 and all(200 <= s < 300 for s in results):
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.MEDIUM,
                title="Business Logic: Same product can be reviewed multiple times",
                endpoint="/reviews",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/reviews",
                    response_status=results[1],
                    request_body=review_body,
                    expected_behavior="Second review for same product should be rejected",
                    actual_behavior=f"Both review submissions returned 2xx",
                ),
                description=f"A user can submit multiple reviews for product #{product_id}, inflating ratings.",
                reproduction_steps=[
                    f"1. POST /reviews with productId={product_id}",
                    "2. POST /reviews again with same productId",
                    "3. Both accepted",
                ],
                impact="Review bombing — users can inflate or deflate product ratings unfairly.",
                remediation="Enforce one-review-per-user-per-product constraint at the database level.",
                confidence=0.88,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []

    async def _test_review_without_purchase(self, customer: Any) -> List[Vulnerability]:
        """Submit a review for a product the user never purchased."""
        # Find a product not in order history
        product_ids = self._get_ids("product_ids")
        if len(product_ids) < 3:
            return []

        # Use last product (less likely to be purchased)
        product_id = product_ids[-1]

        try:
            resp = await self._http.post(
                "/reviews",
                token=customer.token,
                body={"productId": product_id, "rating": 1, "comment": "Never bought this but reviewing anyway"},
            )
        except Exception:
            return []

        if 200 <= resp.status_code < 300:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.BUSINESS_LOGIC_FLAW,
                severity=Severity.LOW,
                title="Business Logic: Review submitted without verified purchase",
                endpoint="/reviews",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/reviews",
                    response_status=resp.status_code,
                    response_body=_safe_json(resp),
                    request_body={"productId": product_id, "rating": 1},
                    expected_behavior="Only users who purchased the product can leave reviews",
                    actual_behavior=f"HTTP {resp.status_code} — review accepted without purchase verification",
                ),
                description="Users can review products they have never purchased.",
                reproduction_steps=[
                    f"1. Find a product you haven't purchased (product #{product_id})",
                    "2. POST /reviews for that product",
                    "3. Observe review accepted",
                ],
                impact="Fake reviews can mislead customers and unfairly affect seller ratings.",
                remediation="Check that the user has a completed order containing the reviewed product.",
                confidence=0.75,
                cwe_id=CWE_BUSINESS_LOGIC,
            )]
        return []


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
