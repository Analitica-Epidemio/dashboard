"""
Unlock user endpoint
"""

import logging

from fastapi import Depends, HTTPException, status

from app.domains.autenticacion.dependencies import get_auth_service, require_superadmin
from app.domains.autenticacion.models import User
from app.domains.autenticacion.service import AuthService

logger = logging.getLogger(__name__)


async def unlock_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Unlock user account (Superadmin only)

    Clears login attempts and unlock time.
    """
    user = await auth_service._obtener_usuario_por_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.intentos_login = 0
    user.bloqueado_hasta = None
    await auth_service.db.commit()

    logger.info(f"Superadmin {current_user.email} unlocked user {user.email}")
    return {"message": "User unlocked successfully"}
