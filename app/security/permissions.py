"""Role-Based Access Control (RBAC) permissions and dependencies."""

from typing import List, Union
from fastapi import HTTPException, status

from app.models.user import User, UserRole


class PermissionDeniedError(HTTPException):
    """Exception raised when an authenticated user lacks required role permissions."""

    def __init__(self, detail: str = "Operation not permitted for this user role."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class RoleChecker:
    """Dependency callable enforcing Role-Based Access Control (RBAC)."""

    def __init__(self, allowed_roles: List[Union[UserRole, str]]):
        """Initialize RoleChecker with allowed roles.

        Args:
            allowed_roles: List of permitted UserRole enum or role string values.
        """
        self.allowed_roles = [
            r if isinstance(r, UserRole) else UserRole(r)
            for r in allowed_roles
        ]

    def __call__(self, current_user: User) -> User:
        """Verify current user has one of the allowed roles.

        Args:
            current_user: Currently authenticated User.

        Returns:
            Validated User object.

        Raises:
            PermissionDeniedError: If user role is not permitted.
        """
        if current_user.role not in self.allowed_roles and not current_user.is_superuser:
            raise PermissionDeniedError(
                f"Role '{current_user.role.value}' is not authorized for this endpoint."
            )
        return current_user


def require_role(role: Union[UserRole, str]) -> RoleChecker:
    """Shortcut helper creating RoleChecker for a single role."""
    return RoleChecker([role])


def require_admin() -> RoleChecker:
    """Shortcut helper requiring admin privileges."""
    return RoleChecker([UserRole.ADMIN])


def require_customer() -> RoleChecker:
    """Shortcut helper requiring customer or admin privileges."""
    return RoleChecker([UserRole.CUSTOMER, UserRole.ADMIN])
