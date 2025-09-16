"""
Logout current session endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.dependencies import get_auth_service, get_current_user_token

logger = logging.getLogger(__name__)


async def logout(
    token_data=Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current session
    """
    if token_data.session_id:
        await auth_service.logout_user(token_data.session_id)
    return {"message": "Logged out successfully"}