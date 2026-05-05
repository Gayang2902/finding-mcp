"""
Known API endpoint definitions with expected access-control metadata.
Used by crawlers and agents to drive targeted testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EndpointDefinition:
    """Static description of an API endpoint."""

    method: str                          # HTTP verb (uppercase)
    path: str                            # Path template, e.g. /orders/{id}
    description: str = ""
    auth_required: bool = True
    roles_allowed: List[str] = field(default_factory=list)   # empty = any authenticated
    params: Dict[str, str] = field(default_factory=dict)     # query params
    body_schema: Dict = field(default_factory=dict)          # example body
    tags: List[str] = field(default_factory=list)
    user_scoped: bool = False            # endpoint should enforce ownership
    has_path_id: bool = False            # path contains a resource ID parameter


# ---------------------------------------------------------------------------
# Full endpoint catalog
# ---------------------------------------------------------------------------

ENDPOINTS: List[EndpointDefinition] = [
    # ------------------------------------------------------------------
    # Auth (public)
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="POST", path="/auth/register",
        description="Register a new customer account",
        auth_required=False,
        body_schema={"email": "str", "password": "str", "firstName": "str", "lastName": "str"},
        tags=["auth", "public"],
    ),
    EndpointDefinition(
        method="POST", path="/auth/login",
        description="Login and receive JWT token",
        auth_required=False,
        body_schema={"email": "str", "password": "str"},
        tags=["auth", "public"],
    ),
    EndpointDefinition(
        method="POST", path="/auth/refresh",
        description="Refresh access token",
        auth_required=False,
        body_schema={"refreshToken": "str"},
        tags=["auth"],
    ),
    EndpointDefinition(
        method="POST", path="/auth/logout",
        description="Invalidate token",
        auth_required=True,
        tags=["auth"],
    ),

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/users/me",
        description="Get current user profile",
        auth_required=True,
        tags=["users"],
    ),
    EndpointDefinition(
        method="PUT", path="/users/me",
        description="Update current user profile",
        auth_required=True,
        body_schema={"firstName": "str", "lastName": "str", "phone": "str"},
        tags=["users"],
    ),
    EndpointDefinition(
        method="GET", path="/users/{id}",
        description="Get user by ID (admin or self)",
        auth_required=True,
        roles_allowed=["admin", "customer", "seller"],
        tags=["users", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="PUT", path="/users/{id}",
        description="Update user by ID",
        auth_required=True,
        roles_allowed=["admin"],
        body_schema={"firstName": "str", "lastName": "str", "role": "str"},
        tags=["users", "admin", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="PUT", path="/users/{id}/role",
        description="Change user role (admin only)",
        auth_required=True,
        roles_allowed=["admin"],
        body_schema={"role": "ADMIN"},
        tags=["users", "admin", "privilege-escalation"],
        has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Products (public reads, seller/admin writes)
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/products",
        description="List all products",
        auth_required=False,
        tags=["products", "public"],
        params={"page": "0", "size": "20", "category": "str", "search": "str"},
    ),
    EndpointDefinition(
        method="GET", path="/products/{id}",
        description="Get product detail",
        auth_required=False,
        tags=["products", "public"],
        has_path_id=True,
    ),
    EndpointDefinition(
        method="POST", path="/products",
        description="Create product",
        auth_required=True,
        roles_allowed=["seller", "admin"],
        body_schema={"name": "str", "price": 0.0, "stock": 0, "categoryId": 1},
        tags=["products", "seller"],
    ),
    EndpointDefinition(
        method="PUT", path="/products/{id}",
        description="Update product",
        auth_required=True,
        roles_allowed=["seller", "admin"],
        body_schema={"name": "str", "price": 0.0, "stock": 0},
        tags=["products", "seller", "idor-target"],
        has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/products/{id}",
        description="Delete product",
        auth_required=True,
        roles_allowed=["seller", "admin"],
        tags=["products", "seller"],
        has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/orders",
        description="List current user's orders",
        auth_required=True,
        tags=["orders"],
    ),
    EndpointDefinition(
        method="POST", path="/orders",
        description="Create a new order",
        auth_required=True,
        body_schema={"addressId": 1, "couponCode": "str", "items": []},
        tags=["orders", "business-logic"],
    ),
    EndpointDefinition(
        method="GET", path="/orders/{id}",
        description="Get order by ID",
        auth_required=True,
        tags=["orders", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="GET", path="/orders/number/{orderNumber}",
        description="Get order by order number",
        auth_required=True,
        tags=["orders", "idor-target"],
        user_scoped=True,
    ),
    EndpointDefinition(
        method="PUT", path="/orders/{id}/status",
        description="Update order status (admin only)",
        auth_required=True,
        roles_allowed=["admin"],
        body_schema={"status": "SHIPPED"},
        tags=["orders", "admin", "privilege-escalation"],
        has_path_id=True,
    ),
    EndpointDefinition(
        method="POST", path="/orders/{id}/cancel",
        description="Cancel order",
        auth_required=True,
        tags=["orders", "business-logic", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Cart
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/cart",
        description="Get current user's cart",
        auth_required=True,
        tags=["cart"],
    ),
    EndpointDefinition(
        method="POST", path="/cart/items",
        description="Add item to cart",
        auth_required=True,
        body_schema={"productId": 1, "quantity": 1},
        tags=["cart", "business-logic"],
    ),
    EndpointDefinition(
        method="PUT", path="/cart/items/{id}",
        description="Update cart item quantity",
        auth_required=True,
        body_schema={"quantity": 1},
        tags=["cart", "idor-target", "business-logic"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/cart/items/{id}",
        description="Remove item from cart",
        auth_required=True,
        tags=["cart", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/cart",
        description="Clear entire cart",
        auth_required=True,
        tags=["cart"],
    ),

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/reviews/product/{id}",
        description="Get reviews for a product",
        auth_required=False,
        tags=["reviews", "public"],
        has_path_id=True,
    ),
    EndpointDefinition(
        method="POST", path="/reviews",
        description="Submit a review",
        auth_required=True,
        body_schema={"productId": 1, "rating": 5, "comment": "str"},
        tags=["reviews", "business-logic"],
    ),
    EndpointDefinition(
        method="PUT", path="/reviews/{id}",
        description="Update own review",
        auth_required=True,
        body_schema={"rating": 5, "comment": "str"},
        tags=["reviews", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/reviews/{id}",
        description="Delete review (own or admin)",
        auth_required=True,
        tags=["reviews", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Addresses
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/addresses",
        description="List current user's addresses",
        auth_required=True,
        tags=["addresses"],
    ),
    EndpointDefinition(
        method="POST", path="/addresses",
        description="Create address",
        auth_required=True,
        body_schema={"street": "str", "city": "str", "country": "str", "zipCode": "str"},
        tags=["addresses"],
    ),
    EndpointDefinition(
        method="GET", path="/addresses/{id}",
        description="Get address by ID",
        auth_required=True,
        tags=["addresses", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="PUT", path="/addresses/{id}",
        description="Update address",
        auth_required=True,
        body_schema={"street": "str", "city": "str"},
        tags=["addresses", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/addresses/{id}",
        description="Delete address",
        auth_required=True,
        tags=["addresses", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/payments",
        description="List current user's payments",
        auth_required=True,
        tags=["payments"],
    ),
    EndpointDefinition(
        method="POST", path="/payments",
        description="Create a payment",
        auth_required=True,
        body_schema={"orderId": 1, "amount": 0.0, "method": "CREDIT_CARD"},
        tags=["payments", "business-logic"],
    ),
    EndpointDefinition(
        method="GET", path="/payments/{id}",
        description="Get payment by ID",
        auth_required=True,
        tags=["payments", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="POST", path="/payments/{id}/refund",
        description="Request refund",
        auth_required=True,
        body_schema={"amount": 0.0, "reason": "str"},
        tags=["payments", "business-logic", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Coupons
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="POST", path="/coupons/validate",
        description="Validate a coupon code",
        auth_required=True,
        body_schema={"code": "str"},
        tags=["coupons", "business-logic"],
    ),
    EndpointDefinition(
        method="POST", path="/coupons/apply",
        description="Apply coupon to order",
        auth_required=True,
        body_schema={"code": "str", "orderId": 1},
        tags=["coupons", "business-logic"],
    ),
    EndpointDefinition(
        method="GET", path="/coupons",
        description="List all coupons (admin)",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["coupons", "admin"],
    ),
    EndpointDefinition(
        method="POST", path="/coupons",
        description="Create coupon (admin)",
        auth_required=True,
        roles_allowed=["admin"],
        body_schema={"code": "str", "discount": 10, "type": "PERCENTAGE", "maxUses": 100},
        tags=["coupons", "admin"],
    ),

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/notifications",
        description="Get current user's notifications",
        auth_required=True,
        tags=["notifications"],
    ),
    EndpointDefinition(
        method="PUT", path="/notifications/{id}/read",
        description="Mark notification as read",
        auth_required=True,
        tags=["notifications", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="DELETE", path="/notifications/{id}",
        description="Delete notification",
        auth_required=True,
        tags=["notifications", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),

    # ------------------------------------------------------------------
    # Shipping
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/shipping/order/{id}",
        description="Get shipping info for an order",
        auth_required=True,
        tags=["shipping", "idor-target"],
        user_scoped=True, has_path_id=True,
    ),
    EndpointDefinition(
        method="GET", path="/shipping/track/{trackingNumber}",
        description="Track shipment by number",
        auth_required=True,
        tags=["shipping", "idor-target"],
        user_scoped=True,
    ),

    # ------------------------------------------------------------------
    # Admin
    # ------------------------------------------------------------------
    EndpointDefinition(
        method="GET", path="/admin/dashboard",
        description="Admin dashboard statistics",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
    ),
    EndpointDefinition(
        method="GET", path="/admin/users",
        description="List all users",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
    ),
    EndpointDefinition(
        method="GET", path="/admin/orders",
        description="List all orders",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
    ),
    EndpointDefinition(
        method="GET", path="/admin/products",
        description="List all products (admin view)",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
    ),
    EndpointDefinition(
        method="DELETE", path="/admin/reviews/{id}",
        description="Delete any review (admin moderation)",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
        has_path_id=True,
    ),
    EndpointDefinition(
        method="GET", path="/admin/analytics",
        description="Revenue analytics",
        auth_required=True,
        roles_allowed=["admin"],
        tags=["admin", "missing-access-control"],
    ),
]


def get_all_endpoints() -> List[EndpointDefinition]:
    return list(ENDPOINTS)


def get_endpoints_by_tag(tag: str) -> List[EndpointDefinition]:
    """Return all endpoints that carry the given tag."""
    return [ep for ep in ENDPOINTS if tag in ep.tags]


def get_user_scoped_endpoints() -> List[EndpointDefinition]:
    """Return endpoints that should enforce resource ownership."""
    return [ep for ep in ENDPOINTS if ep.user_scoped]


def get_admin_endpoints() -> List[EndpointDefinition]:
    return get_endpoints_by_tag("admin")


def get_public_endpoints() -> List[EndpointDefinition]:
    return [ep for ep in ENDPOINTS if not ep.auth_required]
