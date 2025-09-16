"""
Deactivate user endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import UserUpdate
from app.domains.auth.dependencies import get_auth_service, require_superadmin
from app.domains.auth.models import User, UserStatus

logger = logging.getLogger(__name__)


async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Deactivate user (Superadmin only)

    This sets the user status to inactive rather than deleting the record.
    """
    user_data = UserUpdate(status=UserStatus.INACTIVE)
    updated_user = await auth_service.update_user(user_id, user_data)

    # Logout all user sessions
    await auth_service.logout_all_sessions(user_id)

    logger.info(f"Superadmin {current_user.email} deactivated user {updated_user.email}")
    return {"message": "User deactivated"}