"""
Get current user information endpoint
"""

from fastapi import Depends

from app.domains.auth.schemas import UserResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User


async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current user information
    """
    return current_user