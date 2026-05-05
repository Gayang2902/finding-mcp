"""
ID collector — extracts and categorises resource identifiers from API responses.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Field name patterns that indicate specific resource types
_FIELD_MAP: Dict[str, str] = {
    # user IDs
    "userId": "user_ids",
    "user_id": "user_ids",
    "buyerId": "user_ids",
    "sellerId": "user_ids",

    # product IDs
    "productId": "product_ids",
    "product_id": "product_ids",

    # order IDs
    "orderId": "order_ids",
    "order_id": "order_ids",

    # order number (human-readable)
    "orderNumber": "order_numbers",
    "order_number": "order_numbers",

    # cart items
    "cartItemId": "cart_item_ids",
    "cart_item_id": "cart_item_ids",

    # reviews
    "reviewId": "review_ids",
    "review_id": "review_ids",

    # addresses
    "addressId": "address_ids",
    "address_id": "address_ids",

    # payments
    "paymentId": "payment_ids",
    "payment_id": "payment_ids",

    # coupons
    "couponCode": "coupon_codes",
    "coupon_code": "coupon_codes",
    "code": "coupon_codes",

    # shipping
    "trackingNumber": "tracking_numbers",
    "tracking_number": "tracking_numbers",

    # notifications
    "notificationId": "notification_ids",
    "notification_id": "notification_ids",
}

# Generic top-level "id" field maps to these per-resource-type prefixes
_RESOURCE_TYPE_KEYWORDS: Dict[str, str] = {
    "order": "order_ids",
    "product": "product_ids",
    "user": "user_ids",
    "address": "address_ids",
    "payment": "payment_ids",
    "review": "review_ids",
    "cart": "cart_item_ids",
    "notification": "notification_ids",
}

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


class IDCollector:
    """
    Collects resource IDs from API responses during the discovery phase.

    Usage:
        collector = IDCollector()
        collector.extract("/orders/1", response_json)
        collector.extract("/products/5", response_json)
        order_ids = collector.get_ids("order_ids")
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[Any]] = {
            "user_ids": [],
            "product_ids": [],
            "order_ids": [],
            "order_numbers": [],
            "cart_item_ids": [],
            "review_ids": [],
            "address_ids": [],
            "payment_ids": [],
            "coupon_codes": [],
            "tracking_numbers": [],
            "notification_ids": [],
        }
        self._seen: Dict[str, Set] = {k: set() for k in self._store}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, path: str, response_body: Any) -> None:
        """
        Parse *response_body* (dict or list) and store discovered IDs.
        *path* is used as a hint to identify resource type from URL.
        """
        if isinstance(response_body, dict):
            self._process_dict(path, response_body)
        elif isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict):
                    self._process_dict(path, item)

    def get_ids(self, resource_type: str) -> List[Any]:
        """Return collected IDs for *resource_type*."""
        return list(self._store.get(resource_type, []))

    def get_other_user_ids(self, current_user_id: Any) -> List[Any]:
        """Return user IDs that are NOT *current_user_id*."""
        return [uid for uid in self._store["user_ids"] if uid != current_user_id]

    def all_ids(self) -> Dict[str, List[Any]]:
        return {k: list(v) for k, v in self._store.items() if v}

    def summary(self) -> str:
        parts = [f"{k}: {len(v)}" for k, v in self._store.items() if v]
        return ", ".join(parts) if parts else "no IDs collected"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add(self, resource_type: str, value: Any) -> None:
        if value in self._seen[resource_type]:
            return
        self._seen[resource_type].add(value)
        self._store[resource_type].append(value)

    def _process_dict(self, path: str, obj: Dict[str, Any]) -> None:
        # Map well-known fields directly
        for field, resource_type in _FIELD_MAP.items():
            if field in obj and obj[field] is not None:
                self._add(resource_type, obj[field])

        # Generic "id" field: infer resource type from URL path or parent key
        if "id" in obj and obj["id"] is not None:
            resource_type = self._infer_type_from_path(path)
            if resource_type:
                self._add(resource_type, obj["id"])

        # Recurse into nested dicts and lists
        for value in obj.values():
            if isinstance(value, dict):
                self._process_dict(path, value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._process_dict(path, item)

    @staticmethod
    def _infer_type_from_path(path: str) -> Optional[str]:
        path_lower = path.lower()
        for keyword, resource_type in _RESOURCE_TYPE_KEYWORDS.items():
            if keyword in path_lower:
                return resource_type
        return None
