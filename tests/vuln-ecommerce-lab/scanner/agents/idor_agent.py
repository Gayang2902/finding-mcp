"""
IDOR Agent — detects Insecure Direct Object References across all user-scoped endpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.llm_prompts import (
    analyze_idor_response,
    assess_idor_impact,
    generate_idor_remediation,
)
from scanner.config.endpoints import get_user_scoped_endpoints
from scanner.models.vulnerability import Severity, Vulnerability, VulnerabilityType
from scanner.utils.diff_analyzer import compare_responses, extract_sensitive_fields

logger = logging.getLogger(__name__)

# CWE-639: Authorization Bypass Through User-Controlled Key
CWE_IDOR = "CWE-639"

# Default fallback IDs for path resolution
_FALLBACK_IDS = [1, 2, 3, 5, 10]


class IDORAgent(BaseAnalysisAgent):
    """
    Detects Insecure Direct Object References by cross-testing user resources.

    Strategy for each user-scoped endpoint:
      1. User A authenticates and accesses their own resource → record response
      2. User B authenticates and accesses User A's resource → record response
      3. Compare: if User B gets 2xx where 403/404 is expected → IDOR confirmed
      4. LLM analyzes the leak to assess impact and severity
    """

    name = "idor_agent"
    description = "Detects IDOR vulnerabilities across user-scoped endpoints"
    vuln_types = [VulnerabilityType.IDOR]

    async def analyze(self) -> List[Vulnerability]:
        self._log("Starting IDOR analysis")
        findings: List[Vulnerability] = []

        customers = self._get_customers()
        if len(customers) < 2:
            self._log("Need at least 2 customer users for IDOR testing — skipping")
            return findings

        user_a, user_b = customers[0], customers[1]
        self._log("Testing IDOR: user_a=%s vs user_b=%s", user_a.alias, user_b.alias)

        # Run specific IDOR test cases
        findings += await self._test_order_idor(user_a, user_b)
        findings += await self._test_order_number_idor(user_a, user_b)
        findings += await self._test_address_idor(user_a, user_b)
        findings += await self._test_payment_idor(user_a, user_b)
        findings += await self._test_cart_item_idor(user_a, user_b)
        findings += await self._test_review_idor(user_a, user_b)
        findings += await self._test_notification_idor(user_a, user_b)
        findings += await self._test_shipping_idor(user_a, user_b)
        findings += await self._test_user_profile_idor(user_a, user_b)

        # Also dynamically test any other user-scoped endpoints
        findings += await self._test_generic_scoped_endpoints(user_a, user_b)

        self._log("IDOR analysis complete: %d findings", len(findings))
        for v in findings:
            self._log_finding(v)
            self._ctx.add_finding(v)

        return findings

    # ------------------------------------------------------------------
    # Specific IDOR test cases
    # ------------------------------------------------------------------

    async def _test_order_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET /orders/{id} with another user's order ID."""
        ids = self._get_ids("order_ids")
        if not ids:
            return []

        findings = []
        for order_id in ids[:3]:  # test up to 3 IDs
            path = f"/orders/{order_id}"
            vuln = await self._cross_user_test(
                method="GET",
                path=path,
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"order #{order_id}",
                expected_behavior="User B should receive 403 or 404",
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_order_number_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET /orders/number/{orderNumber} with another user's order number."""
        numbers = self._get_ids("order_numbers")
        if not numbers:
            return []

        findings = []
        for order_num in numbers[:2]:
            path = f"/orders/number/{order_num}"
            vuln = await self._cross_user_test(
                method="GET",
                path=path,
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"order number {order_num}",
                expected_behavior="User B should receive 403 or 404",
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_address_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET/PUT /addresses/{id} with another user's address."""
        ids = self._get_ids("address_ids")
        if not ids:
            # Try to create an address to get an ID
            await self._ensure_address(user_a)
            ids = self._get_ids("address_ids")
        if not ids:
            return []

        findings = []
        for addr_id in ids[:2]:
            # GET test
            vuln = await self._cross_user_test(
                method="GET",
                path=f"/addresses/{addr_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"address #{addr_id}",
                expected_behavior="User B should receive 403 or 404",
            )
            if vuln:
                findings.append(vuln)

            # PUT test (data modification)
            vuln = await self._cross_user_test(
                method="PUT",
                path=f"/addresses/{addr_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"address #{addr_id} (write)",
                expected_behavior="User B should not be able to modify another user's address",
                request_body={"street": "HACKED", "city": "HACKED", "country": "XX", "zipCode": "00000"},
                severity_override=Severity.HIGH,
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_payment_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET /payments/{id} with another user's payment."""
        ids = self._get_ids("payment_ids")
        if not ids:
            return []

        findings = []
        for pay_id in ids[:2]:
            vuln = await self._cross_user_test(
                method="GET",
                path=f"/payments/{pay_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"payment #{pay_id}",
                expected_behavior="User B should receive 403 or 404",
                severity_override=Severity.HIGH,
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_cart_item_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """PUT /cart/items/{id} with another user's cart item."""
        ids = self._get_ids("cart_item_ids")
        if not ids:
            return []

        findings = []
        for item_id in ids[:2]:
            vuln = await self._cross_user_test(
                method="PUT",
                path=f"/cart/items/{item_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"cart item #{item_id}",
                expected_behavior="User B should not be able to modify another user's cart",
                request_body={"quantity": 999},
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_review_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """DELETE /reviews/{id} with another user's review."""
        ids = self._get_ids("review_ids")
        if not ids:
            return []

        findings = []
        for review_id in ids[:2]:
            vuln = await self._cross_user_test(
                method="DELETE",
                path=f"/reviews/{review_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"review #{review_id}",
                expected_behavior="User B should not be able to delete another user's review",
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_notification_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """PUT /notifications/{id}/read with another user's notification."""
        ids = self._get_ids("notification_ids")
        if not ids:
            return []

        findings = []
        for notif_id in ids[:2]:
            vuln = await self._cross_user_test(
                method="PUT",
                path=f"/notifications/{notif_id}/read",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"notification #{notif_id}",
                expected_behavior="User B should not be able to mark another user's notification as read",
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_shipping_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET /shipping/order/{id} with another user's order."""
        ids = self._get_ids("order_ids")
        if not ids:
            return []

        findings = []
        for order_id in ids[:2]:
            vuln = await self._cross_user_test(
                method="GET",
                path=f"/shipping/order/{order_id}",
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"shipping for order #{order_id}",
                expected_behavior="User B should receive 403 or 404",
            )
            if vuln:
                findings.append(vuln)
        return findings

    async def _test_user_profile_idor(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """GET /users/{id} with another user's ID."""
        user_ids = self._get_ids("user_ids")
        # Use user_a's actual ID as the target
        target_id = user_a.user_id or (user_ids[0] if user_ids else None)
        if not target_id:
            return []

        vuln = await self._cross_user_test(
            method="GET",
            path=f"/users/{target_id}",
            user_a=user_a,
            user_b=user_b,
            resource_desc=f"user profile #{target_id}",
            expected_behavior="User B should not be able to read another user's profile",
            severity_override=Severity.HIGH,
        )
        return [vuln] if vuln else []

    async def _test_generic_scoped_endpoints(self, user_a: Any, user_b: Any) -> List[Vulnerability]:
        """Test any user-scoped endpoints from the config not covered above."""
        already_tested = {
            "/orders/", "/addresses/", "/payments/", "/cart/items/",
            "/reviews/", "/notifications/", "/shipping/order/", "/users/",
        }
        findings = []
        for ep in get_user_scoped_endpoints():
            if not ep.has_path_id:
                continue
            if any(prefix in ep.path for prefix in already_tested):
                continue
            # Try with fallback ID 1
            concrete_path = ep.path.replace("{id}", "1").replace("{orderId}", "1")
            if "{" in concrete_path:
                continue  # still has unfilled params
            vuln = await self._cross_user_test(
                method=ep.method,
                path=concrete_path,
                user_a=user_a,
                user_b=user_b,
                resource_desc=f"{ep.method} {ep.path}",
                expected_behavior=f"User B should not access {ep.description}",
            )
            if vuln:
                findings.append(vuln)
        return findings

    # ------------------------------------------------------------------
    # Core cross-user test logic
    # ------------------------------------------------------------------

    async def _cross_user_test(
        self,
        method: str,
        path: str,
        user_a: Any,
        user_b: Any,
        resource_desc: str,
        expected_behavior: str,
        request_body: Optional[Dict] = None,
        severity_override: Optional[Severity] = None,
    ) -> Optional[Vulnerability]:
        """
        Core IDOR test:
          1. user_a accesses their resource (establish baseline)
          2. user_b accesses user_a's resource
          3. If user_b gets 2xx → IDOR confirmed
        """
        base_url = self._ctx.target_url

        # Step 1: User A accesses their own resource
        try:
            resp_a = await self._http.make_request(
                method=method,
                path=path,
                token=user_a.token,
                body=request_body,
            )
        except Exception as exc:
            logger.debug("IDOR test: user_a request failed for %s: %s", path, exc)
            return None

        # Step 2: User B accesses user_a's resource
        try:
            resp_b = await self._http.make_request(
                method=method,
                path=path,
                token=user_b.token,
                body=request_body,
            )
        except Exception as exc:
            logger.debug("IDOR test: user_b request failed for %s: %s", path, exc)
            return None

        # Step 3: Evaluate
        comparison = compare_responses(resp_a, resp_b)

        if not comparison.idor_likely:
            logger.debug("No IDOR: %s %s — user_b got %d", method, path, resp_b.status_code)
            return None

        # Confirmed IDOR — gather evidence
        body_b = _safe_json(resp_b)
        leaked_fields = extract_sensitive_fields(body_b) if body_b else []

        # LLM impact analysis
        llm_result = await self._ask_llm_for_analysis(
            analyze_idor_response(
                endpoint=path,
                method=method,
                user_a_response={"status": resp_a.status_code, "body": _safe_json(resp_a)},
                user_b_response={"status": resp_b.status_code, "body": body_b},
            )
        )

        severity = severity_override or self._determine_severity(llm_result, leaked_fields, method)
        confidence = float(llm_result.get("confidence", 0.8))

        evidence = self._build_evidence(
            method=method,
            url=f"{base_url}{path}",
            response_status=resp_b.status_code,
            response_body=body_b,
            request_body=request_body,
            expected_behavior=expected_behavior,
            actual_behavior=f"HTTP {resp_b.status_code} — user_b accessed user_a's {resource_desc}",
            comparison_url=f"{base_url}{path} (as {user_a.alias})",
            comparison_status=resp_a.status_code,
            comparison_body=_safe_json(resp_a),
        )

        remediation_result = await self._ask_llm_for_analysis(
            generate_idor_remediation(
                endpoint=path,
                vuln_details=f"User B accessed User A's {resource_desc} via {method} {path}",
            )
        )
        remediation = (
            remediation_result.get("primary_fix", "")
            or "Verify resource ownership server-side before returning data. "
               "Compare the resource owner ID with the authenticated user's ID."
        )

        return self._create_vulnerability(
            vuln_type=VulnerabilityType.IDOR,
            severity=severity,
            title=f"IDOR: Unauthorized access to {resource_desc}",
            endpoint=path,
            method=method,
            evidence=evidence,
            description=(
                f"User '{user_b.alias}' (role={user_b.role}) can access "
                f"'{resource_desc}' belonging to user '{user_a.alias}' "
                f"by providing the resource ID directly. "
                f"The server does not verify resource ownership."
            ),
            reproduction_steps=[
                f"1. Authenticate as {user_a.alias} and note a resource ID for {resource_desc}",
                f"2. Authenticate as {user_b.alias} (a different user)",
                f"3. Send {method} {path} with {user_b.alias}'s token but {user_a.alias}'s resource ID",
                f"4. Observe HTTP {resp_b.status_code} — access granted without ownership verification",
            ],
            impact=(
                llm_result.get("impact")
                or f"Attacker can read/modify/delete any user's {resource_desc}. "
                   f"Leaked fields: {', '.join(leaked_fields) or 'unknown'}."
            ),
            remediation=remediation,
            confidence=confidence,
            cwe_id=CWE_IDOR,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _determine_severity(
        self,
        llm_result: Dict[str, Any],
        leaked_fields: List[str],
        method: str,
    ) -> Severity:
        # Use LLM severity if available
        llm_severity = llm_result.get("severity")
        if llm_severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            return Severity(llm_severity)

        # Heuristic: write methods on sensitive data are HIGH+
        if method in ("PUT", "DELETE", "PATCH"):
            return Severity.HIGH
        if any(f in leaked_fields for f in ["email", "password", "creditCard", "phone"]):
            return Severity.HIGH
        return Severity.MEDIUM

    async def _ensure_address(self, user: Any) -> None:
        """Create an address for *user* so we have an ID to test against."""
        try:
            resp = await self._http.post(
                "/addresses",
                token=user.token,
                body={
                    "street": "123 Test Street",
                    "city": "Testville",
                    "country": "US",
                    "zipCode": "12345",
                    "state": "CA",
                },
            )
            if resp.status_code in (200, 201):
                body = _safe_json(resp)
                if body and "id" in body:
                    self._ctx.add_resource_ids("address_ids", [body["id"]])
        except Exception as exc:
            logger.debug("Failed to create address for %s: %s", user.alias, exc)


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
