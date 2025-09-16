"""
Authentication endpoints - Login and token refresh (public endpoints)
"""

import logging
from fastapi import Depends, Request

from app.domains.auth.service import AuthService
from app.domains.auth.schemas import UserLogin, Token, RefreshToken
from app.domains.auth.dependencies import get_auth_service

logger = logging.getLogger(__name__)


async def login(
    credentials: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Authenticate user and return JWT tokens

    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Keep session active for 7 days (default: false)

    Returns access token (30 min) and refresh token (7 days)
    """
    user, token = await auth_service.authenticate_user(credentials, request)
    logger.info(f"User {user.email} logged in successfully")
    return token


async def refresh_access_token(
    refresh_data: RefreshToken,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Refresh access token using refresh token

    Returns new access token and optionally new refresh token
    """
    token = await auth_service.refresh_token(refresh_data.refresh_token)
    logger.info("Access token refreshed successfully")
    return token