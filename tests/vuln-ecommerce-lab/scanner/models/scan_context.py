"""
Scan context — shared state passed between pipeline phases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from scanner.models.vulnerability import Vulnerability


class DiscoveredEndpoint(BaseModel):
    """An endpoint observed during crawling/probing."""

    method: str
    path: str
    auth_required: Optional[bool] = None
    status_codes: Dict[str, int] = Field(default_factory=dict)  # role → status
    response_sample: Optional[Any] = None
    response_time_ms: Optional[float] = None
    content_type: Optional[str] = None
    requires_body: bool = False


class ScanContext(BaseModel):
    """
    Mutable shared context for the scan pipeline.

    Phases populate this incrementally; agents read from it.
    """

    target_url: str
    scan_start: datetime = Field(default_factory=datetime.utcnow)

    # Phase 1: Discovery
    discovered_endpoints: List[DiscoveredEndpoint] = Field(default_factory=list)

    # Phase 2: Authentication
    # alias → TestUser (stored as dict to avoid circular import; use test_users helpers)
    authenticated_users: Dict[str, Any] = Field(default_factory=dict)

    # Resource IDs collected during enumeration
    # e.g. {"order_ids": [1, 2, 3], "product_ids": [10, 11]}
    resource_ids: Dict[str, List[Any]] = Field(default_factory=dict)

    # Phase 3-4: Findings accumulated across agents
    findings: List[Vulnerability] = Field(default_factory=list)

    # Counters
    total_requests: int = 0

    def add_resource_ids(self, resource_type: str, ids: List[Any]) -> None:
        existing = self.resource_ids.get(resource_type, [])
        merged = list(dict.fromkeys(existing + ids))  # deduplicate, preserve order
        self.resource_ids[resource_type] = merged

    def get_ids(self, resource_type: str) -> List[Any]:
        return self.resource_ids.get(resource_type, [])

    def add_finding(self, vuln: Vulnerability) -> None:
        self.findings.append(vuln)

    def get_user(self, alias: str) -> Optional[Any]:
        return self.authenticated_users.get(alias)

    def get_user_by_role(self, role: str) -> Optional[Any]:
        for user in self.authenticated_users.values():
            if hasattr(user, "role") and user.role == role:
                return user
        return None

    def get_users_by_role(self, role: str) -> List[Any]:
        return [u for u in self.authenticated_users.values() if hasattr(u, "role") and u.role == role]

    def get_other_users(self, exclude_alias: str) -> List[Any]:
        return [u for alias, u in self.authenticated_users.items() if alias != exclude_alias]

    @property
    def customer_users(self) -> List[Any]:
        return self.get_users_by_role("customer")
