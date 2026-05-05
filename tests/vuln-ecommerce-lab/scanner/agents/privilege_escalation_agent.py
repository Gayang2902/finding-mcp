"""
Privilege Escalation Agent — tests both horizontal and vertical access control.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.llm_prompts import analyze_access_control, assess_escalation_impact
from scanner.config.endpoints import get_admin_endpoints, get_endpoints_by_tag
from scanner.models.vulnerability import Severity, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)

CWE_PRIVILEGE_ESCALATION = "CWE-269"


class PrivilegeEscalationAgent(BaseAnalysisAgent):
    """
    Tests privilege escalation vulnerabilities:

    Horizontal: customer1 accessing customer2's resources (same role, different user)
    Vertical:   customer/seller accessing admin-only functions
    """

    name = "privilege_escalation_agent"
    description = "Detects horizontal and vertical privilege escalation"
    vuln_types = [VulnerabilityType.PRIVILEGE_ESCALATION]

    async def analyze(self) -> List[Vulnerability]:
        self._log("Starting privilege escalation analysis")
        findings: List[Vulnerability] = []

        customer = self._ctx.get_user("customer1") or self._ctx.get_user_by_role("customer")
        seller = self._ctx.get_user("seller") or self._ctx.get_user_by_role("seller")
        admin = self._ctx.get_user("admin") or self._ctx.get_user_by_role("admin")

        # Vertical escalation: customer/seller → admin
        if customer:
            findings += await self._test_vertical_escalation_as_customer(customer)
        if seller:
            findings += await self._test_vertical_escalation_as_seller(seller)

        # Vertical: order status update (should be admin-only)
        if customer:
            findings += await self._test_order_status_escalation(customer)

        # Horizontal: customer accessing another customer's data
        customers = self._ctx.customer_users
        if len(customers) >= 2:
            findings += await self._test_horizontal_escalation(customers[0], customers[1])

        self._log("Privilege escalation analysis complete: %d findings", len(findings))
        for v in findings:
            self._log_finding(v)
            self._ctx.add_finding(v)

        return findings

    # ------------------------------------------------------------------
    # Vertical escalation
    # ------------------------------------------------------------------

    async def _test_vertical_escalation_as_customer(self, customer: Any) -> List[Vulnerability]:
        """Test all admin endpoints as a customer."""
        findings = []
        admin_endpoints = get_admin_endpoints()

        for ep in admin_endpoints:
            if ep.has_path_id:
                continue  # skip path-param endpoints (need real IDs)

            resp = await self._probe(ep.method, ep.path, customer.token)
            if resp is None:
                continue

            if 200 <= resp.status_code < 300:
                llm_result = await self._ask_llm_for_analysis(
                    analyze_access_control(
                        endpoint=ep.path,
                        method=ep.method,
                        role_responses={"customer": {"status": resp.status_code, "body": _safe_json(resp)}},
                        expected_roles=["admin"],
                    )
                )

                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                    severity=Severity.CRITICAL,
                    title=f"Privilege Escalation: Customer accesses admin endpoint {ep.path}",
                    endpoint=ep.path,
                    method=ep.method,
                    evidence=self._build_evidence(
                        method=ep.method,
                        url=f"{self._ctx.target_url}{ep.path}",
                        response_status=resp.status_code,
                        response_body=_safe_json(resp),
                        expected_behavior="Should return 403 Forbidden for customer role",
                        actual_behavior=f"HTTP {resp.status_code} — customer can access admin endpoint",
                    ),
                    description=(
                        f"The endpoint {ep.method} {ep.path} (described as: {ep.description}) "
                        f"is accessible by a customer-role user. "
                        f"This endpoint should be restricted to admin role only."
                    ),
                    reproduction_steps=[
                        "1. Authenticate as a customer user",
                        f"2. Send {ep.method} {ep.path} with the customer's JWT token",
                        f"3. Observe HTTP {resp.status_code} — access granted",
                    ],
                    impact=(
                        llm_result.get("impact")
                        or f"Customers can access admin functionality: {ep.description}"
                    ),
                    remediation=(
                        f"Add role-based access control check to {ep.path}. "
                        "Only users with ADMIN role should be allowed."
                    ),
                    confidence=float(llm_result.get("confidence", 0.9)),
                    cwe_id=CWE_PRIVILEGE_ESCALATION,
                ))
        return findings

    async def _test_vertical_escalation_as_seller(self, seller: Any) -> List[Vulnerability]:
        """Test admin-specific endpoints as a seller."""
        findings = []

        # Admin-only endpoints a seller should NOT access
        seller_blocked = [
            ("GET", "/admin/users"),
            ("GET", "/admin/dashboard"),
            ("GET", "/admin/analytics"),
            ("DELETE", "/admin/reviews/1"),
        ]

        for method, path in seller_blocked:
            resp = await self._probe(method, path, seller.token)
            if resp is None:
                continue

            if 200 <= resp.status_code < 300:
                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                    severity=Severity.HIGH,
                    title=f"Privilege Escalation: Seller accesses admin-only endpoint {path}",
                    endpoint=path,
                    method=method,
                    evidence=self._build_evidence(
                        method=method,
                        url=f"{self._ctx.target_url}{path}",
                        response_status=resp.status_code,
                        response_body=_safe_json(resp),
                        expected_behavior="Should return 403 for seller role",
                        actual_behavior=f"HTTP {resp.status_code} — seller access granted",
                    ),
                    description=f"Seller role can access admin-only endpoint {method} {path}.",
                    reproduction_steps=[
                        "1. Authenticate as seller",
                        f"2. Send {method} {path} with seller JWT",
                        f"3. Observe HTTP {resp.status_code}",
                    ],
                    impact="Sellers gain access to admin functionality including user management and analytics.",
                    remediation="Enforce admin-only role check. Seller role should be separate from admin.",
                    confidence=0.9,
                    cwe_id=CWE_PRIVILEGE_ESCALATION,
                ))
        return findings

    async def _test_order_status_escalation(self, customer: Any) -> List[Vulnerability]:
        """PUT /orders/{id}/status — customer tries to update order status."""
        order_ids = self._get_ids("order_ids")
        if not order_ids:
            return []

        findings = []
        for order_id in order_ids[:2]:
            path = f"/orders/{order_id}/status"
            try:
                resp = await self._http.put(
                    path,
                    token=customer.token,
                    body={"status": "DELIVERED"},
                )
            except Exception:
                continue

            if 200 <= resp.status_code < 300:
                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                    severity=Severity.HIGH,
                    title=f"Privilege Escalation: Customer can update order status",
                    endpoint=path,
                    method="PUT",
                    evidence=self._build_evidence(
                        method="PUT",
                        url=f"{self._ctx.target_url}{path}",
                        response_status=resp.status_code,
                        response_body=_safe_json(resp),
                        request_body={"status": "DELIVERED"},
                        expected_behavior="Should return 403 — only admins can update order status",
                        actual_behavior=f"HTTP {resp.status_code} — customer updated order status",
                    ),
                    description=(
                        f"A customer can change the status of order #{order_id} to DELIVERED "
                        "without admin privileges."
                    ),
                    reproduction_steps=[
                        "1. Authenticate as customer",
                        f"2. PUT /orders/{order_id}/status with body: {{\"status\": \"DELIVERED\"}}",
                        f"3. Observe HTTP {resp.status_code} — status changed",
                    ],
                    impact="Customer can mark orders as delivered without actually receiving them, enabling fraud.",
                    remediation="Restrict PUT /orders/{id}/status to admin role only.",
                    confidence=0.95,
                    cwe_id=CWE_PRIVILEGE_ESCALATION,
                ))
        return findings

    # ------------------------------------------------------------------
    # Horizontal escalation
    # ------------------------------------------------------------------

    async def _test_horizontal_escalation(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """
        Customer1 accessing customer2's resources using guessable IDs.
        This overlaps with IDOR but focuses on role-level analysis.
        """
        findings = []

        # Horizontal: customer accessing admin order list
        resp = await self._probe("GET", "/admin/orders", user_a.token)
        if resp and 200 <= resp.status_code < 300:
            body = _safe_json(resp)
            # If response contains orders from multiple users → horizontal escalation
            findings.append(self._create_vulnerability(
                vuln_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                severity=Severity.HIGH,
                title="Privilege Escalation: Customer can list all orders (admin endpoint)",
                endpoint="/admin/orders",
                method="GET",
                evidence=self._build_evidence(
                    method="GET",
                    url=f"{self._ctx.target_url}/admin/orders",
                    response_status=resp.status_code,
                    response_body=body,
                    expected_behavior="403 Forbidden for non-admin users",
                    actual_behavior=f"HTTP {resp.status_code} — all orders exposed to customer",
                ),
                description="A customer can access the admin orders endpoint and see all users' orders.",
                reproduction_steps=[
                    "1. Authenticate as customer",
                    "2. GET /admin/orders",
                    f"3. Observe HTTP {resp.status_code} — all orders returned",
                ],
                impact="Customer can enumerate all orders in the system, exposing other users' purchase data.",
                remediation="Enforce ADMIN role check on /admin/orders.",
                confidence=0.95,
                cwe_id=CWE_PRIVILEGE_ESCALATION,
            ))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _probe(self, method: str, path: str, token: Optional[str]) -> Optional[httpx.Response]:
        try:
            return await self._http.make_request(method, path, token=token)
        except Exception as exc:
            logger.debug("Probe failed %s %s: %s", method, path, exc)
            return None


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
