"""
Get current user sessions endpoint
"""

from typing import List
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import SessionInfo
from app.domains.auth.dependencies import get_current_user, get_auth_service, get_current_user_token
from app.domains.auth.models import User


async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    token_data=Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service)
) -> List[SessionInfo]:
    """
    Get current user's active sessions
    """
    sessions = await auth_service.get_user_sessions(
        current_user.id,
        token_data.session_id
    )
    return sessions