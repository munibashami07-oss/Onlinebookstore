"""Centralized FastAPI dependencies for database sessions, authentication, and permissions."""

from app.core.session import get_db
from app.security.oauth2 import (
    get_current_active_user,
    get_current_admin,
    get_current_user,
    get_current_user_optional,
)
from app.security.permissions import (
    RoleChecker,
    require_admin,
    require_customer,
    require_role,
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
    "get_current_admin",
    "RoleChecker",
    "require_admin",
    "require_customer",
    "require_role",
]