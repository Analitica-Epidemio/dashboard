"""
Logout all sessions endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.dependencies import get_current_user, get_auth_service
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout from all sessions
    """
    await auth_service.logout_all_sessions(current_user.id)
    logger.info(f"User {current_user.email} logged out from all sessions")
    return {"message": "Logged out from all sessions"}