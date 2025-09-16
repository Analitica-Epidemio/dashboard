"""
Update user endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import UserUpdate, UserResponse
from app.domains.auth.dependencies import get_auth_service, require_superadmin
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Update user by ID (Superadmin only)

    Superadmins can update any user's information including role and status.
    """
    updated_user = await auth_service.update_user(user_id, user_data)
    logger.info(f"Superadmin {current_user.email} updated user {updated_user.email}")
    return updated_user