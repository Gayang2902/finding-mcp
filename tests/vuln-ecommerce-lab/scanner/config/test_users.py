"""
Test user definitions matching the seeded e-commerce database.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from scanner.utils.http_client import AsyncHTTPClient

logger = logging.getLogger(__name__)


@dataclass
class TestUser:
    """Represents a test user with credentials and optional auth token."""

    email: str
    password: str
    role: str
    alias: str
    token: Optional[str] = field(default=None, repr=False)
    user_id: Optional[int] = field(default=None)
    extra: Dict = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    @property
    def auth_header(self) -> Dict[str, str]:
        if not self.token:
            raise ValueError(f"User {self.alias} is not authenticated")
        return {"Authorization": f"Bearer {self.token}"}


# Predefined users matching the seeded database
PREDEFINED_USERS: List[TestUser] = [
    TestUser(
        alias="admin",
        email="admin@vulnshop.com",
        password="admin123",
        role="admin",
    ),
    TestUser(
        alias="seller",
        email="seller1@vulnshop.com",
        password="password123",
        role="seller",
    ),
    TestUser(
        alias="customer1",
        email="customer1@vulnshop.com",
        password="password123",
        role="customer",
    ),
    TestUser(
        alias="customer2",
        email="customer2@vulnshop.com",
        password="password123",
        role="customer",
    ),
]

# Index by alias for fast lookup
_USER_INDEX: Dict[str, TestUser] = {u.alias: u for u in PREDEFINED_USERS}


def get_user_by_role(role: str) -> Optional[TestUser]:
    """Return the first user matching *role*, or None."""
    for user in PREDEFINED_USERS:
        if user.role == role:
            return user
    return None


def get_user_by_alias(alias: str) -> Optional[TestUser]:
    """Return user by alias, or None."""
    return _USER_INDEX.get(alias)


def get_all_users() -> List[TestUser]:
    return list(PREDEFINED_USERS)


async def authenticate_all(http_client: "AsyncHTTPClient") -> Dict[str, TestUser]:
    """
    Authenticate every predefined user and store their JWT tokens.

    Returns a mapping of alias → authenticated TestUser.
    Raises on total failure (if no user can authenticate).
    """
    authenticated: Dict[str, TestUser] = {}

    for user in PREDEFINED_USERS:
        try:
            response = await http_client.make_request(
                method="POST",
                path="/auth/login",
                body={"email": user.email, "password": user.password},
            )
            if response.status_code == 200:
                data = response.json()
                user.token = data.get("token") or data.get("accessToken") or data.get("access_token")
                user.user_id = data.get("userId") or data.get("id")
                if user.token:
                    authenticated[user.alias] = user
                    logger.info("Authenticated user %s (role=%s, id=%s)", user.alias, user.role, user.user_id)
                else:
                    logger.warning("No token in response for user %s: %s", user.alias, data)
            else:
                logger.warning(
                    "Authentication failed for %s: HTTP %d", user.alias, response.status_code
                )
        except Exception as exc:
            logger.error("Authentication error for %s: %s", user.alias, exc)

    if not authenticated:
        raise RuntimeError("Failed to authenticate any test user — is the target running?")

    return authenticated
