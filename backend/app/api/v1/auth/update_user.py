"""
Update user endpoint
"""

import logging

from fastapi import Depends

from app.domains.autenticacion.dependencies import get_auth_service, require_superadmin
from app.domains.autenticacion.models import User
from app.domains.autenticacion.schemas import UserResponse, UserUpdate
from app.domains.autenticacion.service import AuthService

logger = logging.getLogger(__name__)


async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Update user by ID (Superadmin only)

    Superadmins can update any user's information including role and status.
    """
    updated_user = await auth_service.actualizar_usuario(user_id, user_data)
    logger.info(f"Superadmin {current_user.email} updated user {updated_user.email}")
    return UserResponse.model_validate(updated_user)
