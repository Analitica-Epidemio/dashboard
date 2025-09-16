"""
Logout specific session endpoint
"""

import logging

from fastapi import Depends, HTTPException, status

from app.domains.autenticacion.dependencies import get_auth_service, get_current_user
from app.domains.autenticacion.models import User
from app.domains.autenticacion.service import AuthService

logger = logging.getLogger(__name__)


async def logout_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout specific session
    """
    success = await auth_service.logout_specific_session(
        current_user.id,
        session_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or not owned by user"
        )

    logger.info(f"User {current_user.email} logged out session {session_id}")
    return {"message": "Session logged out successfully"}