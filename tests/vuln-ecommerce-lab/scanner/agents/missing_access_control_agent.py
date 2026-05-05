"""
Missing Access Control Agent — finds endpoints accessible without proper authentication/authorization.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.llm_prompts import analyze_access_control
from scanner.config.endpoints import get_all_endpoints, get_admin_endpoints
from scanner.models.vulnerability import Severity, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)

CWE_MISSING_ACCESS_CONTROL = "CWE-285"


class MissingAccessControlAgent(BaseAnalysisAgent):
    """
    Maps every endpoint against expected access requirements and flags deviations:
    - Endpoints accessible without any token (should require auth)
    - Endpoints accessible by wrong roles
    """

    name = "missing_access_control_agent"
    description = "Detects missing or misconfigured access control on API endpoints"
    vuln_types = [VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL]

    async def analyze(self) -> List[Vulnerability]:
        self._log("Starting missing access control analysis")
        findings: List[Vulnerability] = []

        customer = self._ctx.get_user("customer1") or self._ctx.get_user_by_role("customer")
        seller = self._ctx.get_user("seller") or self._ctx.get_user_by_role("seller")
        admin = self._ctx.get_user("admin") or self._ctx.get_user_by_role("admin")

        findings += await self._test_unauthenticated_access()
        findings += await self._test_admin_endpoints_without_admin(customer, seller)
        findings += await self._test_sensitive_data_unauthenticated()

        self._log("Missing access control analysis complete: %d findings", len(findings))
        for v in findings:
            self._log_finding(v)
            self._ctx.add_finding(v)

        return findings

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    async def _test_unauthenticated_access(self) -> List[Vulnerability]:
        """Test all auth-required endpoints without any token."""
        findings = []
        endpoints = get_all_endpoints()

        for ep in endpoints:
            if not ep.auth_required:
                continue
            if ep.has_path_id:
                continue  # skip path-param endpoints

            resp = await self._probe(ep.method, ep.path, token=None)
            if resp is None:
                continue

            if 200 <= resp.status_code < 300:
                severity = self._classify_severity_by_endpoint(ep.path, ep.tags)

                llm_result = await self._ask_llm_for_analysis(
                    analyze_access_control(
                        endpoint=ep.path,
                        method=ep.method,
                        role_responses={"anonymous": {"status": resp.status_code, "body": _safe_json(resp)}},
                        expected_roles=ep.roles_allowed or ["authenticated"],
                    )
                )

                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL,
                    severity=severity,
                    title=f"Missing Auth: {ep.method} {ep.path} accessible without authentication",
                    endpoint=ep.path,
                    method=ep.method,
                    evidence=self._build_evidence(
                        method=ep.method,
                        url=f"{self._ctx.target_url}{ep.path}",
                        response_status=resp.status_code,
                        response_body=_safe_json(resp),
                        expected_behavior="Should return 401 Unauthorized without a token",
                        actual_behavior=f"HTTP {resp.status_code} — no authentication required",
                    ),
                    description=(
                        f"The endpoint {ep.method} {ep.path} ({ep.description}) is accessible "
                        f"without any authentication token. It should require authentication."
                    ),
                    reproduction_steps=[
                        f"1. Send {ep.method} {ep.path} without any Authorization header",
                        f"2. Observe HTTP {resp.status_code} — data returned without auth",
                    ],
                    impact=(
                        llm_result.get("impact")
                        or f"Unauthenticated users can access {ep.description}"
                    ),
                    remediation=(
                        f"Add authentication requirement to {ep.path}. "
                        "Ensure all requests are validated against a valid JWT token."
                    ),
                    confidence=float(llm_result.get("confidence", 0.95)),
                    cwe_id=CWE_MISSING_ACCESS_CONTROL,
                ))

        return findings

    async def _test_admin_endpoints_without_admin(
        self,
        customer: Optional[Any],
        seller: Optional[Any],
    ) -> List[Vulnerability]:
        """Test admin-only endpoints with customer and seller tokens."""
        findings = []
        admin_endpoints = get_admin_endpoints()

        for ep in admin_endpoints:
            if ep.has_path_id:
                continue

            role_responses: Dict[str, Dict[str, Any]] = {}

            for role_name, user in [("customer", customer), ("seller", seller)]:
                if not user or not user.token:
                    continue
                resp = await self._probe(ep.method, ep.path, user.token)
                if resp is None:
                    continue

                role_responses[role_name] = {
                    "status": resp.status_code,
                    "body": _safe_json(resp),
                }

                if 200 <= resp.status_code < 300:
                    llm_result = await self._ask_llm_for_analysis(
                        analyze_access_control(
                            endpoint=ep.path,
                            method=ep.method,
                            role_responses=role_responses,
                            expected_roles=["admin"],
                        )
                    )

                    findings.append(self._create_vulnerability(
                        vuln_type=VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL,
                        severity=Severity.CRITICAL,
                        title=f"Missing Access Control: {role_name} accesses admin endpoint {ep.path}",
                        endpoint=ep.path,
                        method=ep.method,
                        evidence=self._build_evidence(
                            method=ep.method,
                            url=f"{self._ctx.target_url}{ep.path}",
                            response_status=resp.status_code,
                            response_body=_safe_json(resp),
                            expected_behavior="403 Forbidden — admin role required",
                            actual_behavior=f"HTTP {resp.status_code} — {role_name} access granted",
                        ),
                        description=(
                            f"Admin endpoint {ep.method} {ep.path} is accessible by "
                            f"a {role_name}-role user. This endpoint should be restricted to admin only."
                        ),
                        reproduction_steps=[
                            f"1. Authenticate as {role_name} user",
                            f"2. Send {ep.method} {ep.path} with {role_name}'s JWT token",
                            f"3. Observe HTTP {resp.status_code} — access granted",
                        ],
                        impact=(
                            llm_result.get("impact")
                            or f"Non-admin users gain access to {ep.description}"
                        ),
                        remediation=(
                            f"Add @PreAuthorize(\"hasRole('ADMIN')\") or equivalent to {ep.path}. "
                            "Verify role on every request, not just at login."
                        ),
                        confidence=float(llm_result.get("confidence", 0.92)),
                        cwe_id=CWE_MISSING_ACCESS_CONTROL,
                    ))

        return findings

    async def _test_sensitive_data_unauthenticated(self) -> List[Vulnerability]:
        """Test specific high-value sensitive endpoints without auth."""
        sensitive_endpoints = [
            ("GET", "/admin/users", "All user data including emails"),
            ("GET", "/admin/orders", "All order data"),
            ("GET", "/admin/dashboard", "Revenue and business metrics"),
            ("GET", "/admin/analytics", "Business analytics"),
            ("GET", "/payments", "Payment information"),
            ("GET", "/orders", "Order data"),
            ("GET", "/addresses", "User addresses (PII)"),
        ]

        findings = []
        for method, path, data_desc in sensitive_endpoints:
            resp = await self._probe(method, path, token=None)
            if resp is None:
                continue

            if 200 <= resp.status_code < 300:
                body = _safe_json(resp)
                # Check if response actually contains data (not empty list)
                has_data = bool(body) and (isinstance(body, list) and len(body) > 0 or isinstance(body, dict))

                if not has_data:
                    continue

                findings.append(self._create_vulnerability(
                    vuln_type=VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL,
                    severity=Severity.CRITICAL,
                    title=f"Unauthenticated Access to Sensitive Data: {path}",
                    endpoint=path,
                    method=method,
                    evidence=self._build_evidence(
                        method=method,
                        url=f"{self._ctx.target_url}{path}",
                        response_status=resp.status_code,
                        response_body=body,
                        expected_behavior="401 Unauthorized — authentication required",
                        actual_behavior=f"HTTP {resp.status_code} — {data_desc} exposed without auth",
                    ),
                    description=(
                        f"Sensitive endpoint {method} {path} returns {data_desc} "
                        "without requiring authentication."
                    ),
                    reproduction_steps=[
                        f"1. Send GET {path} with no Authorization header",
                        f"2. Observe HTTP {resp.status_code} — sensitive data returned",
                    ],
                    impact=f"Any unauthenticated user can access {data_desc}.",
                    remediation="Add authentication middleware to all non-public endpoints.",
                    confidence=0.98,
                    cwe_id=CWE_MISSING_ACCESS_CONTROL,
                ))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _probe(
        self, method: str, path: str, token: Optional[str]
    ) -> Optional[httpx.Response]:
        try:
            return await self._http.make_request(method, path, token=token)
        except Exception as exc:
            logger.debug("Probe failed %s %s: %s", method, path, exc)
            return None

    @staticmethod
    def _classify_severity_by_endpoint(path: str, tags: List[str]) -> Severity:
        """Heuristic severity based on endpoint characteristics."""
        if "admin" in tags or "/admin/" in path:
            return Severity.CRITICAL
        if any(t in tags for t in ["payments", "orders", "users"]):
            return Severity.HIGH
        if any(t in tags for t in ["addresses", "reviews"]):
            return Severity.MEDIUM
        return Severity.LOW


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
