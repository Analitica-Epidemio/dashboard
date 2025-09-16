"""
Unlock user endpoint
"""

import logging
from fastapi import Depends, HTTPException, status

from app.domains.auth.service import AuthService
from app.domains.auth.dependencies import get_auth_service, require_superadmin
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def unlock_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Unlock user account (Superadmin only)

    Clears login attempts and unlock time.
    """
    user = await auth_service._get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.login_attempts = 0
    user.locked_until = None
    await auth_service.db.commit()

    logger.info(f"Superadmin {current_user.email} unlocked user {user.email}")
    return {"message": "User unlocked successfully"}