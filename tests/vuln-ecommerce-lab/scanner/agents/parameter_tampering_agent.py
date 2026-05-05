"""
Parameter Tampering Agent — detects server-side trust of client-supplied values
that should be computed or restricted server-side.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.llm_prompts import analyze_parameter_trust, identify_tamperable_params
from scanner.models.vulnerability import Severity, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)

CWE_PARAMETER_TAMPERING = "CWE-472"


class ParameterTamperingAgent(BaseAnalysisAgent):
    """
    Tests endpoints for parameter tampering vulnerabilities.

    Targets parameters that clients should NOT control:
    - price / totalAmount / discount
    - role / status (user elevation)
    - userId (cross-user manipulation)
    - quantity with edge cases (negative, zero, overflow)
    """

    name = "parameter_tampering_agent"
    description = "Detects client-side parameter trust issues"
    vuln_types = [VulnerabilityType.PARAMETER_TAMPERING]

    async def analyze(self) -> List[Vulnerability]:
        self._log("Starting parameter tampering analysis")
        findings: List[Vulnerability] = []

        # Use first available authenticated customer
        customer = self._ctx.get_user("customer1") or self._ctx.get_user_by_role("customer")
        if not customer or not customer.token:
            self._log("No authenticated customer — skipping parameter tampering tests")
            return findings

        admin = self._ctx.get_user("admin")
        seller = self._ctx.get_user("seller")

        findings += await self._test_cart_price_injection(customer)
        findings += await self._test_order_amount_tampering(customer)
        findings += await self._test_payment_amount_tampering(customer)
        findings += await self._test_role_elevation(customer)
        findings += await self._test_negative_quantity(customer)
        findings += await self._test_coupon_discount_injection(customer)
        findings += await self._test_user_id_override(customer)

        self._log("Parameter tampering analysis complete: %d findings", len(findings))
        for v in findings:
            self._log_finding(v)
            self._ctx.add_finding(v)

        return findings

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    async def _test_cart_price_injection(self, customer: Any) -> List[Vulnerability]:
        """
        POST /cart/items — inject a custom price field.
        If the server uses the client-supplied price, this is a critical flaw.
        """
        product_ids = self._get_ids("product_ids")
        product_id = product_ids[0] if product_ids else 1

        # Normal add to cart (baseline)
        normal_body = {"productId": product_id, "quantity": 1}
        tampered_body = {"productId": product_id, "quantity": 1, "price": 0.01, "unitPrice": 0.01}

        try:
            resp_normal = await self._http.post("/cart/items", token=customer.token, body=normal_body)
            resp_tampered = await self._http.post("/cart/items", token=customer.token, body=tampered_body)
        except Exception as exc:
            logger.debug("Cart price injection test failed: %s", exc)
            return []

        body_normal = _safe_json(resp_normal)
        body_tampered = _safe_json(resp_tampered)

        # Check if tampered price was reflected in cart item
        tampered_price_accepted = False
        if resp_tampered.status_code in (200, 201) and body_tampered:
            price_in_response = (
                body_tampered.get("price")
                or body_tampered.get("unitPrice")
                or (body_tampered.get("item") or {}).get("price")
            )
            if price_in_response and float(price_in_response) < 1.0:
                tampered_price_accepted = True

        llm_result = await self._ask_llm_for_analysis(
            analyze_parameter_trust(
                endpoint="/cart/items",
                method="POST",
                request_body=tampered_body,
                response={"status": resp_tampered.status_code, "body": body_tampered},
            )
        )

        server_accepted = llm_result.get("server_accepted_value", tampered_price_accepted)
        if not (server_accepted or tampered_price_accepted):
            return []

        return [self._create_vulnerability(
            vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
            severity=Severity.CRITICAL,
            title="Parameter Tampering: Client-controlled price accepted in cart",
            endpoint="/cart/items",
            method="POST",
            evidence=self._build_evidence(
                method="POST",
                url=f"{self._ctx.target_url}/cart/items",
                response_status=resp_tampered.status_code,
                response_body=body_tampered,
                request_body=tampered_body,
                expected_behavior="Server should ignore client-supplied price field and use server-side price",
                actual_behavior=f"Server accepted client-supplied price=0.01 in cart item",
            ),
            description=(
                "The /cart/items endpoint accepts a client-supplied price field. "
                "An attacker can add items to their cart at arbitrary prices."
            ),
            reproduction_steps=[
                "1. Authenticate as a customer",
                "2. POST /cart/items with body: {\"productId\": 1, \"quantity\": 1, \"price\": 0.01}",
                "3. Observe the cart item is created with the tampered price",
                "4. Proceed to checkout — order total will use the attacker-controlled price",
            ],
            impact="Attacker can purchase any product for an arbitrary (potentially zero) price.",
            remediation=(
                "Never trust client-supplied price values. "
                "Always look up the current price from the database server-side when adding items to cart."
            ),
            confidence=float(llm_result.get("confidence", 0.85)),
            cwe_id=CWE_PARAMETER_TAMPERING,
        )]

    async def _test_order_amount_tampering(self, customer: Any) -> List[Vulnerability]:
        """POST /orders — try to set totalAmount in request body."""
        order_ids = self._get_ids("order_ids")
        address_ids = self._get_ids("address_ids")
        address_id = address_ids[0] if address_ids else 1

        tampered_body = {
            "addressId": address_id,
            "totalAmount": 0.01,
            "total": 0.01,
            "amount": 0.01,
        }

        try:
            resp = await self._http.post("/orders", token=customer.token, body=tampered_body)
        except Exception as exc:
            logger.debug("Order amount tampering test failed: %s", exc)
            return []

        body = _safe_json(resp)
        if resp.status_code not in (200, 201) or not body:
            return []

        # Check if totalAmount in response matches tampered value
        resp_total = body.get("totalAmount") or body.get("total")
        if resp_total and float(resp_total) < 1.0:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
                severity=Severity.CRITICAL,
                title="Parameter Tampering: Client can set order total amount",
                endpoint="/orders",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/orders",
                    response_status=resp.status_code,
                    response_body=body,
                    request_body=tampered_body,
                    expected_behavior="Server should calculate order total from cart items",
                    actual_behavior=f"Order created with client-supplied totalAmount={resp_total}",
                ),
                description=(
                    "The /orders endpoint accepts a client-supplied totalAmount field, "
                    "allowing an attacker to create orders with an arbitrary (near-zero) total."
                ),
                reproduction_steps=[
                    "1. Authenticate as a customer with items in cart",
                    "2. POST /orders with body including totalAmount: 0.01",
                    "3. Observe the order is created with the tampered total",
                ],
                impact="Attacker can purchase any items for near-zero cost.",
                remediation="Calculate order total server-side from cart contents. Never accept client-supplied totals.",
                confidence=0.9,
                cwe_id=CWE_PARAMETER_TAMPERING,
            )]
        return []

    async def _test_payment_amount_tampering(self, customer: Any) -> List[Vulnerability]:
        """POST /payments — send amount lower than order total."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        tampered_body = {
            "orderId": order_ids[0],
            "amount": 0.01,
            "method": "CREDIT_CARD",
        }

        try:
            resp = await self._http.post("/payments", token=customer.token, body=tampered_body)
        except Exception as exc:
            logger.debug("Payment amount tampering test failed: %s", exc)
            return []

        body = _safe_json(resp)
        if resp.status_code not in (200, 201):
            return []

        # Server accepted a payment of $0.01 — likely a vulnerability
        return [self._create_vulnerability(
            vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
            severity=Severity.CRITICAL,
            title="Parameter Tampering: Payment amount not validated against order total",
            endpoint="/payments",
            method="POST",
            evidence=self._build_evidence(
                method="POST",
                url=f"{self._ctx.target_url}/payments",
                response_status=resp.status_code,
                response_body=body,
                request_body=tampered_body,
                expected_behavior="Server should reject payments where amount < order total",
                actual_behavior=f"HTTP {resp.status_code} — payment of $0.01 accepted",
            ),
            description=(
                "The /payments endpoint accepts arbitrary amount values without validating "
                "against the actual order total. An attacker can pay $0.01 for any order."
            ),
            reproduction_steps=[
                "1. Create an order (e.g. total=$99.99)",
                "2. POST /payments with amount: 0.01",
                "3. Observe the payment is accepted — order marked as paid",
            ],
            impact="Attacker can pay any amount for an order, effectively getting items for free.",
            remediation=(
                "Server must validate that payment amount equals or exceeds the order total. "
                "Never trust client-supplied payment amounts."
            ),
            confidence=0.85,
            cwe_id=CWE_PARAMETER_TAMPERING,
        )]

    async def _test_role_elevation(self, customer: Any) -> List[Vulnerability]:
        """PUT /users/{id} or profile update — try to set own role to ADMIN."""
        user_id = customer.user_id or 1
        tampered_body = {"role": "ADMIN", "firstName": "Test"}

        endpoints_to_test = [
            ("PUT", f"/users/{user_id}", tampered_body),
            ("PUT", "/users/me", tampered_body),
        ]

        findings = []
        for method, path, body in endpoints_to_test:
            try:
                resp = await self._http.make_request(method, path, token=customer.token, body=body)
            except Exception:
                continue

            resp_body = _safe_json(resp)
            if resp.status_code not in (200, 201) or not resp_body:
                continue

            # Check if role was changed in response
            new_role = resp_body.get("role") or (resp_body.get("user") or {}).get("role")
            if new_role and new_role.upper() in ("ADMIN", "SELLER"):
                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
                    severity=Severity.CRITICAL,
                    title=f"Parameter Tampering: User can self-assign elevated role via {path}",
                    endpoint=path,
                    method=method,
                    evidence=self._build_evidence(
                        method=method,
                        url=f"{self._ctx.target_url}{path}",
                        response_status=resp.status_code,
                        response_body=resp_body,
                        request_body=body,
                        expected_behavior="Role field should be ignored or rejected for non-admin users",
                        actual_behavior=f"Role changed to {new_role}",
                    ),
                    description=f"A customer can change their own role to {new_role} via {method} {path}.",
                    reproduction_steps=[
                        f"1. Authenticate as customer (role=customer)",
                        f"2. Send {method} {path} with body: {{\"role\": \"ADMIN\"}}",
                        f"3. Observe role is now {new_role} in the response",
                        "4. Use the same token to access admin endpoints",
                    ],
                    impact="Complete privilege escalation to admin. Full application takeover.",
                    remediation=(
                        "Remove 'role' from user-updatable fields. "
                        "Role changes must go through a dedicated admin-only endpoint."
                    ),
                    confidence=0.95,
                    cwe_id=CWE_PARAMETER_TAMPERING,
                ))
        return findings

    async def _test_negative_quantity(self, customer: Any) -> List[Vulnerability]:
        """POST /cart/items — send negative quantity."""
        product_ids = self._get_ids("product_ids")
        product_id = product_ids[0] if product_ids else 1

        try:
            resp = await self._http.post(
                "/cart/items",
                token=customer.token,
                body={"productId": product_id, "quantity": -1},
            )
        except Exception:
            return []

        body = _safe_json(resp)
        if resp.status_code not in (200, 201):
            return []

        return [self._create_vulnerability(
            vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
            severity=Severity.MEDIUM,
            title="Business Logic: Negative quantity accepted in cart",
            endpoint="/cart/items",
            method="POST",
            evidence=self._build_evidence(
                method="POST",
                url=f"{self._ctx.target_url}/cart/items",
                response_status=resp.status_code,
                response_body=body,
                request_body={"productId": product_id, "quantity": -1},
                expected_behavior="Server should reject quantity < 1",
                actual_behavior=f"HTTP {resp.status_code} — negative quantity accepted",
            ),
            description="The /cart/items endpoint accepts negative quantity values, potentially causing negative totals.",
            reproduction_steps=[
                "1. POST /cart/items with quantity: -1",
                "2. Observe the item is added with negative quantity",
            ],
            impact="May result in negative cart totals, credit manipulation, or inventory corruption.",
            remediation="Validate quantity >= 1 on the server side.",
            confidence=0.9,
            cwe_id=CWE_PARAMETER_TAMPERING,
        )]

    async def _test_coupon_discount_injection(self, customer: Any) -> List[Vulnerability]:
        """POST /coupons/apply — inject discount values."""
        order_ids = self._get_ids("order_ids")
        order_id = order_ids[0] if order_ids else 1

        tampered_body = {"code": "DISCOUNT100", "orderId": order_id, "discount": 100, "discountPercent": 100}

        try:
            resp = await self._http.post("/coupons/apply", token=customer.token, body=tampered_body)
        except Exception:
            return []

        body = _safe_json(resp)
        if resp.status_code not in (200, 201):
            return []

        # Check if 100% discount was applied
        discount_val = (body or {}).get("discount") or (body or {}).get("discountAmount")
        if discount_val and float(discount_val) >= 50:
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
                severity=Severity.HIGH,
                title="Parameter Tampering: Coupon discount percentage controllable by client",
                endpoint="/coupons/apply",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/coupons/apply",
                    response_status=resp.status_code,
                    response_body=body,
                    request_body=tampered_body,
                    expected_behavior="Discount should come from server-side coupon lookup, not client input",
                    actual_behavior=f"Client-supplied discount={discount_val} was applied",
                ),
                description="The coupon endpoint trusts client-supplied discount values.",
                reproduction_steps=[
                    "1. POST /coupons/apply with discount: 100",
                    "2. Observe 100% discount applied to order",
                ],
                impact="Attacker can get 100% discount on any order.",
                remediation="Always look up coupon discount from the database by coupon code. Never trust client discount values.",
                confidence=0.8,
                cwe_id=CWE_PARAMETER_TAMPERING,
            )]
        return []

    async def _test_user_id_override(self, customer: Any) -> List[Vulnerability]:
        """
        Test if passing a userId in the request body allows acting as another user.
        """
        # Try to create an address on behalf of user ID 1 (likely admin)
        admin = self._ctx.get_user("admin")
        if not admin:
            return []

        target_user_id = admin.user_id or 1
        tampered_body = {
            "userId": target_user_id,
            "street": "1337 Hacker Lane",
            "city": "Exploit City",
            "country": "US",
            "zipCode": "00000",
        }

        try:
            resp = await self._http.post("/addresses", token=customer.token, body=tampered_body)
        except Exception:
            return []

        body = _safe_json(resp)
        if resp.status_code not in (200, 201) or not body:
            return []

        # Check if the address was created for the target user
        created_user_id = body.get("userId") or body.get("user_id")
        if created_user_id and str(created_user_id) == str(target_user_id):
            return [self._create_vulnerability(
                vuln_type=VulnerabilityType.PARAMETER_TAMPERING,
                severity=Severity.HIGH,
                title="Parameter Tampering: userId override allows acting as another user",
                endpoint="/addresses",
                method="POST",
                evidence=self._build_evidence(
                    method="POST",
                    url=f"{self._ctx.target_url}/addresses",
                    response_status=resp.status_code,
                    response_body=body,
                    request_body=tampered_body,
                    expected_behavior="userId should be taken from JWT token, not request body",
                    actual_behavior=f"Address created for user ID {target_user_id} (admin)",
                ),
                description="The /addresses endpoint trusts userId from request body over the authenticated user's ID.",
                reproduction_steps=[
                    "1. Authenticate as customer",
                    "2. POST /addresses with userId: 1 (admin's ID)",
                    "3. Observe address created for admin user",
                ],
                impact="Attacker can create/modify resources on behalf of any user.",
                remediation="Always derive userId from the authenticated JWT token. Never trust userId from request body.",
                confidence=0.9,
                cwe_id=CWE_PARAMETER_TAMPERING,
            )]
        return []


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
