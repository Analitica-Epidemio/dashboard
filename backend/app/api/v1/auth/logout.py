"""
Logout current session endpoint
"""

import logging

from fastapi import Depends

from app.domains.autenticacion.dependencies import (
    get_auth_service,
    get_current_user_token,
)
from app.domains.autenticacion.service import AuthService

logger = logging.getLogger(__name__)


async def logout(
    token_data=Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current session
    """
    if token_data.id_sesion:
        await auth_service.cerrar_sesion_usuario(token_data.id_sesion)
    return {"message": "Logged out successfully"}
