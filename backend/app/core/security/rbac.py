"""
Security utilities and RBAC decorators
Modern role-based access control following 2025 best practices
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status

from app.domains.autenticacion.dependencies import get_current_user
from app.domains.autenticacion.models import User, UserRole, UserStatus

logger = logging.getLogger(__name__)


class RoleBasedAccessControl:
    """
    Role-based access control utilities
    Provides decorators and dependency factories for different permission levels
    """

    @staticmethod
    def require_roles(*allowed_roles: UserRole):
        """
        Decorator factory for role-based access control
        Usage: @RoleBasedAccessControl.require_roles(UserRole.SUPERADMIN)
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from kwargs (injected by FastAPI)
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="User dependency not properly injected",
                    )

                if current_user.rol not in allowed_roles:
                    logger.warning(
                        f"Access denied: User {current_user.email} (role: {current_user.rol.value}) "
                        f"tried to access endpoint requiring roles: {[r.value for r in allowed_roles]}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def require_superadmin(func: Callable) -> Callable:
        """Decorator for superadmin-only endpoints"""
        return RoleBasedAccessControl.require_roles(UserRole.SUPERADMIN)(func)

    @staticmethod
    def require_any_role(func: Callable) -> Callable:
        """Decorator for authenticated users (any role)"""
        return RoleBasedAccessControl.require_roles(
            UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO
        )(func)

    @staticmethod
    def require_active_user(func: Callable) -> Callable:
        """Decorator to ensure user is active"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User dependency not properly injected",
                )

            if current_user.estado != UserStatus.ACTIVE:
                logger.warning(
                    f"Inactive user {current_user.email} tried to access endpoint"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {current_user.estado.value}. Contact administrator.",
                )

            return await func(*args, **kwargs)

        return wrapper


# Dependency factories for common use cases (modern approach)
def RequireSuperadmin():
    """Dependency factory for superadmin-only endpoints"""

    async def _require_superadmin(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.rol != UserRole.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superadmin access required",
            )
        return current_user

    return _require_superadmin


def RequireAnyRole():
    """Dependency factory for any authenticated user"""

    async def _require_any_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol not in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Valid role required"
            )
        return current_user

    return _require_any_role


def RequireActiveUser():
    """Dependency factory for active users only"""

    async def _require_active_user(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.estado != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {current_user.estado.value}",
            )
        return current_user

    return _require_active_user


def RequireRoles(*roles: UserRole):
    """Dependency factory for specific roles"""

    async def _require_roles(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}",
            )
        return current_user

    return _require_roles


# Permission checking utilities for business logic
class PermissionChecker:
    """Utility class for checking permissions in business logic"""

    @staticmethod
    def can_modify_user(current_user: User, target_user: User) -> bool:
        """Check if current user can modify target user"""
        if current_user.rol == UserRole.SUPERADMIN:
            return True
        return current_user.id == target_user.id

    @staticmethod
    def can_view_user(current_user: User, target_user: User) -> bool:
        """Check if current user can view target user"""
        if current_user.rol == UserRole.SUPERADMIN:
            return True
        return current_user.id == target_user.id

    @staticmethod
    def can_create_user(current_user: User) -> bool:
        """Check if current user can create new users"""
        return current_user.rol == UserRole.SUPERADMIN

    @staticmethod
    def can_access_reports(current_user: User) -> bool:
        """Check if current user can access reports"""
        return current_user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]

    @staticmethod
    def can_modify_system_data(current_user: User) -> bool:
        """Check if current user can modify system data (estrategias, eventos, etc)"""
        return current_user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]

    @staticmethod
    def can_upload_files(current_user: User) -> bool:
        """Check if current user can upload files"""
        return current_user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]

    @staticmethod
    def can_view_charts(current_user: User) -> bool:
        """Check if current user can view charts and analytics"""
        return current_user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]

    @staticmethod
    def ensure_permission(condition: bool, message: str = "Access denied") -> None:
        """Raise exception if permission condition is not met"""
        if not condition:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


# Context manager for permission checking in business logic
class PermissionContext:
    """Context manager for checking permissions within business logic"""

    def __init__(self, current_user: User, action: str):
        self.current_user = current_user
        self.action = action

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def require_superadmin(self):
        """Require superadmin role"""
        PermissionChecker.ensure_permission(
            self.current_user.rol == UserRole.SUPERADMIN,
            f"Superadmin access required for {self.action}",
        )
        return self

    def require_any_role(self):
        """Require any valid role"""
        PermissionChecker.ensure_permission(
            self.current_user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO],
            f"Valid role required for {self.action}",
        )
        return self

    def require_active_user(self):
        """Require active user status"""
        PermissionChecker.ensure_permission(
            self.current_user.estado == UserStatus.ACTIVE,
            f"Active account required for {self.action}",
        )
        return self

    def require_permission(self, condition: bool, message: Optional[str] = None):
        """Require custom permission condition"""
        if message is None:
            message = f"Permission denied for {self.action}"
        PermissionChecker.ensure_permission(condition, message)
        return self


# Note: Audit logging removed per best practices
# Use structured logging at application level or external audit systems


# Note: Rate limiting and audit logging removed per best practices
# These should be implemented at infrastructure level (web server, CDN, etc.)
# For application-level needs, use specialized tools like Redis
