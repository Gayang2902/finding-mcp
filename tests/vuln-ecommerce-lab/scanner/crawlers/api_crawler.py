"""
API crawler — discovers endpoints via OpenAPI spec and predefined catalog,
then probes each endpoint and enumerates resource IDs.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from scanner.config.endpoints import EndpointDefinition, get_all_endpoints
from scanner.config.test_users import TestUser
from scanner.models.scan_context import DiscoveredEndpoint, ScanContext
from scanner.utils.http_client import AsyncHTTPClient
from scanner.utils.id_collector import IDCollector

logger = logging.getLogger(__name__)


class APICrawler:
    """
    Phase-1 crawler that builds a complete picture of the target API.

    Flow:
      1. Attempt OpenAPI discovery (/v3/api-docs, /swagger.json)
      2. Merge with predefined endpoint catalog
      3. Probe each endpoint with available tokens
      4. Enumerate list endpoints to harvest resource IDs
    """

    def __init__(
        self,
        http_client: AsyncHTTPClient,
        scan_context: ScanContext,
        id_collector: IDCollector,
    ) -> None:
        self._http = http_client
        self._ctx = scan_context
        self._ids = id_collector

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run(self, authenticated_users: Dict[str, TestUser]) -> None:
        """
        Execute full discovery. Populates *scan_context* in-place.
        """
        logger.info("Starting API crawl for %s", self._ctx.target_url)

        # 1. Collect endpoint definitions
        endpoints = get_all_endpoints()

        # Optionally augment from OpenAPI spec
        openapi_endpoints = await self._discover_from_openapi()
        if openapi_endpoints:
            logger.info("Discovered %d additional endpoints from OpenAPI spec", len(openapi_endpoints))
            endpoints = self._merge_endpoints(endpoints, openapi_endpoints)

        logger.info("Total endpoints to probe: %d", len(endpoints))

        # 2. Probe each endpoint
        for ep in endpoints:
            discovered = await self._probe_endpoint(ep, authenticated_users)
            self._ctx.discovered_endpoints.append(discovered)

        # 3. Enumerate resources to gather IDs
        await self._enumerate_resources(authenticated_users)

        logger.info(
            "Crawl complete: %d endpoints probed, IDs: %s",
            len(self._ctx.discovered_endpoints),
            self._ids.summary(),
        )

    # ------------------------------------------------------------------
    # OpenAPI discovery
    # ------------------------------------------------------------------

    async def _discover_from_openapi(self) -> List[EndpointDefinition]:
        """
        Try common OpenAPI spec URLs. Returns parsed endpoint definitions.
        """
        candidates = [
            "/v3/api-docs",
            "/swagger.json",
            "/openapi.json",
            "/api-docs",
            "/v2/api-docs",
        ]
        for path in candidates:
            try:
                response = await self._http.get(path)
                if response.status_code == 200:
                    spec = response.json()
                    logger.info("Found OpenAPI spec at %s", path)
                    return self._parse_openapi_spec(spec)
            except Exception as exc:
                logger.debug("OpenAPI probe failed at %s: %s", path, exc)
        return []

    @staticmethod
    def _parse_openapi_spec(spec: Dict[str, Any]) -> List[EndpointDefinition]:
        """Parse an OpenAPI 3.x or Swagger 2.x spec into EndpointDefinitions."""
        endpoints: List[EndpointDefinition] = []
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue
                if not isinstance(operation, dict):
                    continue
                security = operation.get("security", spec.get("security", []))
                auth_required = bool(security)
                tags = operation.get("tags", [])
                description = operation.get("summary", operation.get("description", ""))
                endpoints.append(
                    EndpointDefinition(
                        method=method.upper(),
                        path=path,
                        description=description,
                        auth_required=auth_required,
                        tags=tags,
                        has_path_id="{" in path,
                    )
                )
        return endpoints

    @staticmethod
    def _merge_endpoints(
        predefined: List[EndpointDefinition],
        from_spec: List[EndpointDefinition],
    ) -> List[EndpointDefinition]:
        """Merge spec-discovered endpoints, skipping duplicates."""
        existing_keys = {(ep.method, ep.path) for ep in predefined}
        merged = list(predefined)
        for ep in from_spec:
            if (ep.method, ep.path) not in existing_keys:
                merged.append(ep)
                existing_keys.add((ep.method, ep.path))
        return merged

    # ------------------------------------------------------------------
    # Endpoint probing
    # ------------------------------------------------------------------

    async def _probe_endpoint(
        self,
        ep: EndpointDefinition,
        authenticated_users: Dict[str, TestUser],
    ) -> DiscoveredEndpoint:
        """
        Send a probing request to the endpoint with each available role token.
        Records status codes per role and a sample response body.
        """
        status_codes: Dict[str, int] = {}
        response_sample: Any = None
        response_time: Optional[float] = None

        # Resolve any path template to a concrete path (use first available ID)
        concrete_path = self._resolve_path(ep.path)

        # Try unauthenticated first
        try:
            resp = await self._http.make_request(ep.method, concrete_path)
            status_codes["anonymous"] = resp.status_code
            if resp.status_code in (200, 201) and response_sample is None:
                response_sample = _safe_json(resp)
            if resp.elapsed:
                response_time = resp.elapsed.total_seconds() * 1000
        except Exception as exc:
            logger.debug("Anon probe failed for %s %s: %s", ep.method, concrete_path, exc)

        # Try each authenticated role
        for alias, user in authenticated_users.items():
            if not user.token:
                continue
            try:
                resp = await self._http.make_request(ep.method, concrete_path, token=user.token)
                status_codes[user.role] = resp.status_code
                if resp.status_code in (200, 201) and response_sample is None:
                    response_sample = _safe_json(resp)
                # Collect IDs from successful responses
                if resp.status_code in (200, 201):
                    body = _safe_json(resp)
                    if body:
                        self._ids.extract(concrete_path, body)
            except Exception as exc:
                logger.debug("Auth probe failed for %s %s (%s): %s", ep.method, concrete_path, alias, exc)

        auth_required = "anonymous" not in status_codes or status_codes.get("anonymous", 999) in (401, 403)

        return DiscoveredEndpoint(
            method=ep.method,
            path=ep.path,
            auth_required=auth_required,
            status_codes=status_codes,
            response_sample=response_sample,
            response_time_ms=response_time,
        )

    def _resolve_path(self, path_template: str) -> str:
        """
        Replace {id} / {orderId} etc. in path templates with real IDs
        collected so far, falling back to "1".
        """
        if "{" not in path_template:
            return path_template

        resolved = path_template
        # Map common param names to resource types
        param_to_resource = {
            "id": None,          # generic — needs context
            "orderId": "order_ids",
            "orderNumber": "order_numbers",
            "productId": "product_ids",
            "userId": "user_ids",
            "addressId": "address_ids",
            "paymentId": "payment_ids",
            "reviewId": "review_ids",
            "trackingNumber": "tracking_numbers",
        }

        import re
        for match in re.finditer(r"\{(\w+)\}", path_template):
            param = match.group(1)
            resource_type = param_to_resource.get(param)
            value = "1"
            if resource_type:
                ids = self._ids.get_ids(resource_type)
                if ids:
                    value = str(ids[0])
            resolved = resolved.replace(f"{{{param}}}", value)
        return resolved

    # ------------------------------------------------------------------
    # Resource enumeration
    # ------------------------------------------------------------------

    async def _enumerate_resources(self, authenticated_users: Dict[str, TestUser]) -> None:
        """
        Call list endpoints to harvest as many resource IDs as possible.
        """
        list_paths = [
            "/orders",
            "/products",
            "/addresses",
            "/payments",
            "/reviews/product/1",
            "/cart",
            "/notifications",
            "/users/me",
        ]

        for alias, user in authenticated_users.items():
            if not user.token:
                continue
            for path in list_paths:
                try:
                    resp = await self._http.get(path, token=user.token)
                    if resp.status_code in (200, 201):
                        body = _safe_json(resp)
                        if body:
                            self._ids.extract(path, body)
                            # Update context resource_ids
                            all_ids = self._ids.all_ids()
                            for resource_type, ids in all_ids.items():
                                self._ctx.add_resource_ids(resource_type, ids)
                except Exception as exc:
                    logger.debug("Enumeration failed for %s (%s): %s", path, alias, exc)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_endpoint_map(self) -> str:
        """Return a JSON representation of discovered endpoints."""
        data = [
            {
                "method": ep.method,
                "path": ep.path,
                "auth_required": ep.auth_required,
                "status_codes": ep.status_codes,
                "response_time_ms": ep.response_time_ms,
            }
            for ep in self._ctx.discovered_endpoints
        ]
        return json.dumps(data, indent=2)


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
