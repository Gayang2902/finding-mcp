"""
Auth crawler — maps authentication and authorization requirements for each endpoint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from scanner.config.endpoints import EndpointDefinition, get_all_endpoints
from scanner.config.test_users import TestUser
from scanner.models.scan_context import DiscoveredEndpoint, ScanContext
from scanner.utils.http_client import AsyncHTTPClient

logger = logging.getLogger(__name__)


class AuthCrawler:
    """
    Systematically tests each endpoint with:
      - No authentication
      - Customer token
      - Seller token
      - Admin token

    Identifies:
      - Endpoints that should require auth but don't
      - Endpoints that allow wrong roles
    """

    def __init__(
        self,
        http_client: AsyncHTTPClient,
        scan_context: ScanContext,
    ) -> None:
        self._http = http_client
        self._ctx = scan_context

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run(self, authenticated_users: Dict[str, TestUser]) -> Dict[str, Any]:
        """
        Execute auth mapping pass. Returns a report dict.
        """
        logger.info("Starting auth crawl")
        endpoints = get_all_endpoints()

        results: List[Dict[str, Any]] = []
        for ep in endpoints:
            if ep.has_path_id:
                # Skip path-param endpoints in auth crawl — they need real IDs
                continue
            result = await self._test_endpoint_roles(ep, authenticated_users)
            results.append(result)

        unauthenticated = self.find_unauthenticated_sensitive_endpoints(results)
        role_bypass = self.find_role_bypass_endpoints(results, authenticated_users)

        logger.info(
            "Auth crawl complete: %d endpoints tested, %d unauthenticated sensitive, %d role bypass",
            len(results), len(unauthenticated), len(role_bypass),
        )

        return {
            "endpoint_results": results,
            "unauthenticated_sensitive": unauthenticated,
            "role_bypass": role_bypass,
        }

    # ------------------------------------------------------------------
    # Per-endpoint testing
    # ------------------------------------------------------------------

    async def authenticate(self, email: str, password: str) -> Optional[str]:
        """
        Login and return the JWT token, or None on failure.
        """
        try:
            resp = await self._http.post(
                "/auth/login",
                body={"email": email, "password": password},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("token") or data.get("accessToken") or data.get("access_token")
        except Exception as exc:
            logger.error("Login failed for %s: %s", email, exc)
        return None

    async def test_endpoint_auth(self, endpoint: EndpointDefinition, token: Optional[str] = None) -> bool:
        """
        Returns True if the endpoint requires authentication
        (i.e. returns 401 without a token and 2xx with one).
        """
        try:
            anon_resp = await self._http.make_request(endpoint.method, endpoint.path)
            if anon_resp.status_code in (401, 403):
                if token:
                    auth_resp = await self._http.make_request(endpoint.method, endpoint.path, token=token)
                    return 200 <= auth_resp.status_code < 300
                return True
            return False
        except Exception as exc:
            logger.debug("Auth test failed for %s: %s", endpoint.path, exc)
            return False

    async def test_endpoint_roles(
        self,
        endpoint: EndpointDefinition,
        tokens_by_role: Dict[str, str],
    ) -> Dict[str, int]:
        """
        Test an endpoint with each role token. Returns role → status_code.
        """
        results: Dict[str, int] = {}
        try:
            anon_resp = await self._http.make_request(endpoint.method, endpoint.path)
            results["anonymous"] = anon_resp.status_code
        except Exception:
            results["anonymous"] = -1

        for role, token in tokens_by_role.items():
            try:
                resp = await self._http.make_request(endpoint.method, endpoint.path, token=token)
                results[role] = resp.status_code
            except Exception:
                results[role] = -1

        return results

    async def _test_endpoint_roles(
        self,
        ep: EndpointDefinition,
        authenticated_users: Dict[str, TestUser],
    ) -> Dict[str, Any]:
        """Full per-endpoint role test with result metadata."""
        tokens_by_role: Dict[str, str] = {}
        # Use first user per role
        role_seen = set()
        for user in authenticated_users.values():
            if user.role not in role_seen and user.token:
                tokens_by_role[user.role] = user.token
                role_seen.add(user.role)

        role_statuses = await self.test_endpoint_roles(ep, tokens_by_role)

        return {
            "method": ep.method,
            "path": ep.path,
            "expected_roles": ep.roles_allowed,
            "expected_auth": ep.auth_required,
            "role_statuses": role_statuses,
            "description": ep.description,
            "tags": ep.tags,
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def find_unauthenticated_sensitive_endpoints(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Return endpoints that:
        - Are expected to require authentication
        - But return 200 without any token
        """
        flagged = []
        for r in results:
            if r["expected_auth"] and r["role_statuses"].get("anonymous", 999) in (200, 201):
                flagged.append(r)
        return flagged

    def find_role_bypass_endpoints(
        self,
        results: List[Dict[str, Any]],
        authenticated_users: Dict[str, TestUser],
    ) -> List[Dict[str, Any]]:
        """
        Return endpoints where a non-allowed role receives a 2xx response.
        """
        flagged = []
        for r in results:
            expected_roles = set(r.get("expected_roles", []))
            if not expected_roles:
                continue  # No role restriction defined — skip
            for role, status in r["role_statuses"].items():
                if role == "anonymous":
                    continue
                if role not in expected_roles and 200 <= status < 300:
                    flagged.append({**r, "bypassing_role": role, "bypass_status": status})
                    break
        return flagged

    async def discover_auth_requirements(
        self, authenticated_users: Dict[str, TestUser]
    ) -> Dict[str, Any]:
        """Alias for run() — discover auth requirements for all endpoints."""
        return await self.run(authenticated_users)
