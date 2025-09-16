"""
Update current user information endpoint
"""

import logging

from fastapi import Depends, HTTPException, status

from app.domains.autenticacion.dependencies import get_auth_service, get_current_user
from app.domains.autenticacion.models import User
from app.domains.autenticacion.schemas import UserResponse, UserUpdate
from app.domains.autenticacion.service import AuthService

logger = logging.getLogger(__name__)


async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Update current user information

    Users can update their own profile information.
    Role and status changes require superadmin privileges.
    """
    # Users can't change their own role/status
    if user_data.role is not None or user_data.status is not None:
        if current_user.role.value != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change role or status"
            )

    updated_user = await auth_service.update_user(current_user.id, user_data)
    logger.info(f"User {current_user.email} updated their profile")
    return updated_user