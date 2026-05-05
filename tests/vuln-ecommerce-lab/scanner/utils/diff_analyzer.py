"""
Response diff analyzer — compare two HTTP responses to detect authorization bypass.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import httpx

logger = logging.getLogger(__name__)

# Fields that may indicate PII or sensitive data
_SENSITIVE_PATTERNS: List[str] = [
    "email", "password", "ssn", "phone", "creditCard", "cardNumber",
    "cvv", "bankAccount", "token", "secret", "apiKey", "address",
    "dateOfBirth", "dob", "taxId", "passportNumber",
]

_SENSITIVE_RE = re.compile(
    r"(" + "|".join(re.escape(p) for p in _SENSITIVE_PATTERNS) + r")",
    re.IGNORECASE,
)


@dataclass
class ResponseComparison:
    """Result of comparing two HTTP responses."""

    same_status: bool
    same_body: bool
    similar_structure: bool

    status_a: int
    status_b: int

    body_a: Any
    body_b: Any

    leaked_fields: List[str] = field(default_factory=list)
    structural_diff: Dict[str, Any] = field(default_factory=dict)

    @property
    def access_granted_to_b(self) -> bool:
        """True if response B (attacker) got a successful response."""
        return 200 <= self.status_b < 300

    @property
    def idor_likely(self) -> bool:
        """
        Heuristic: IDOR is likely if:
        - user B got a 2xx where 403/404 was expected
        - response bodies have the same structure with different owner data
        """
        if self.status_a in (200, 201) and self.access_granted_to_b:
            return True
        return False


def compare_responses(
    response_a: httpx.Response,
    response_b: httpx.Response,
) -> ResponseComparison:
    """
    Compare two HTTP responses. *response_a* is the legitimate owner's response;
    *response_b* is the attacker's response accessing the same resource.
    """
    body_a = _safe_json(response_a)
    body_b = _safe_json(response_b)

    same_status = response_a.status_code == response_b.status_code
    same_body = body_a == body_b
    similar_structure = _similar_structure(body_a, body_b)

    leaked = []
    if response_b.status_code in (200, 201) and body_b:
        leaked = extract_sensitive_fields(body_b)

    structural_diff = _compute_structural_diff(body_a, body_b)

    return ResponseComparison(
        same_status=same_status,
        same_body=same_body,
        similar_structure=similar_structure,
        status_a=response_a.status_code,
        status_b=response_b.status_code,
        body_a=body_a,
        body_b=body_b,
        leaked_fields=leaked,
        structural_diff=structural_diff,
    )


def detect_data_leak(response: httpx.Response, user_context: Dict[str, Any]) -> List[str]:
    """
    Check if *response* body contains data that belongs to another user.

    *user_context* should have keys like: email, id, name (owner's data).

    Returns list of leaked field descriptions.
    """
    body = _safe_json(response)
    if not body:
        return []

    body_str = json.dumps(body, default=str).lower()
    leaks: List[str] = []

    for key, value in user_context.items():
        if value and str(value).lower() in body_str:
            leaks.append(f"{key}={value} found in response")

    return leaks


def extract_sensitive_fields(response_body: Any) -> List[str]:
    """
    Walk *response_body* and return field names that match known sensitive patterns.
    """
    if not response_body:
        return []

    body_str = json.dumps(response_body, default=str)
    matches = _SENSITIVE_RE.findall(body_str)
    # Deduplicate case-insensitively
    seen: Set[str] = set()
    result: List[str] = []
    for m in matches:
        lower = m.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(m)
    return result


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text or None


def _similar_structure(a: Any, b: Any) -> bool:
    """True if both values have the same type and, for dicts, same keys."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys())
    return True


def _compute_structural_diff(a: Any, b: Any) -> Dict[str, Any]:
    """Identify top-level fields present in one response but not the other."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {}

    only_in_a = {k: a[k] for k in a if k not in b}
    only_in_b = {k: b[k] for k in b if k not in a}
    changed = {k: {"a": a[k], "b": b[k]} for k in a if k in b and a[k] != b[k]}

    diff: Dict[str, Any] = {}
    if only_in_a:
        diff["only_in_owner"] = only_in_a
    if only_in_b:
        diff["only_in_attacker"] = only_in_b
    if changed:
        diff["changed_values"] = changed
    return diff
