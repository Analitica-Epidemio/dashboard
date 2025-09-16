"""
Change current user password endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import UserChangePassword
from app.domains.auth.dependencies import get_current_user, get_auth_service
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change current user's password

    - **current_password**: Current password
    - **new_password**: New strong password

    This will logout all other sessions for security.
    """
    await auth_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    logger.info(f"User {current_user.email} changed their password")
    return {"message": "Password changed successfully"}