"""
Security module for authentication and authorization
"""

# Re-export main security functions from rbac.py
# Export flexible auth
from .flexible_auth import RequireAuthOrSignedUrl
from .rbac import (
    PermissionChecker,
    PermissionContext,
    RequireActiveUser,
    RequireAnyRole,
    RequireRoles,
    RequireSuperadmin,
    RoleBasedAccessControl,
)
from .signed_url_auth import verify_signed_url_headers

# Create rbac instance for backward compatibility
rbac = RoleBasedAccessControl()

__all__ = [
    'RoleBasedAccessControl',
    'RequireSuperadmin',
    'RequireAnyRole',
    'RequireActiveUser',
    'RequireRoles',
    'RequireAuthOrSignedUrl',
    'verify_signed_url_headers',
    'rbac',
    'PermissionChecker',
    'PermissionContext'
]