"""
Create user endpoint
"""

import logging
from fastapi import Depends

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import UserCreate, UserResponse
from app.domains.auth.dependencies import get_auth_service, require_superadmin
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Create a new user (Superadmin only - for UI administration)

    - **email**: Valid email address
    - **nombre**: First name
    - **apellido**: Last name
    - **password**: Strong password (min 8 chars, must include uppercase, lowercase, digit, special char)
    - **role**: User role (superadmin, epidemiologo)
    """
    user = await auth_service.create_user(user_data)
    logger.info(f"Superadmin {current_user.email} created user {user.email}")
    return user