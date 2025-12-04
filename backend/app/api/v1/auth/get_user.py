"""
Get user by ID endpoint
"""

from fastapi import Depends, HTTPException, status

from app.domains.autenticacion.dependencies import get_auth_service, require_superadmin
from app.domains.autenticacion.models import User
from app.domains.autenticacion.schemas import UserResponse
from app.domains.autenticacion.service import AuthService


async def get_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Get user by ID (Superadmin only)
    """
    user = await auth_service._get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
