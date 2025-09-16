"""
Authentication API endpoints
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.auth.service import AuthService
from app.domains.auth.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserChangePassword,
    Token, RefreshToken, SessionInfo
)
from app.domains.auth.dependencies import (
    get_current_user, get_auth_service, require_superadmin, get_current_user_token
)
from app.domains.auth.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
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


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshToken,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token

    Returns new access token and refresh token
    """
    token = await auth_service.refresh_token(refresh_data.refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_data = Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current session
    """
    if token_data.session_id:
        await auth_service.logout_user(token_data.session_id)
    return {"message": "Logged out successfully"}


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout from all sessions
    """
    await auth_service.logout_all_sessions(current_user.id)
    logger.info(f"User {current_user.email} logged out from all sessions")
    return {"message": "Logged out from all sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user information

    Users can update their own profile information.
    Role and status changes require superadmin privileges.
    """
    # Users can't change their own role/status
    if user_data.role is not None or user_data.status is not None:
        if current_user.role.value != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change role or status"
            )

    updated_user = await auth_service.update_user(current_user.id, user_data)
    logger.info(f"User {current_user.email} updated their profile")
    return updated_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change current user's password

    - **current_password**: Current password
    - **new_password**: New strong password

    This will logout all other sessions for security.
    """
    await auth_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    logger.info(f"User {current_user.email} changed their password")
    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    token_data = Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user's active sessions
    """
    sessions = await auth_service.get_user_sessions(
        current_user.id,
        token_data.session_id
    )
    return sessions


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def logout_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout specific session
    """
    # Verify session belongs to current user
    sessions = await auth_service.get_user_sessions(current_user.id)
    session_ids = [s.id for s in sessions]

    if session_id not in session_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    await auth_service.logout_user(session_id)
    logger.info(f"User {current_user.email} logged out session {session_id}")
    return {"message": "Session logged out"}


# Superadmin-only endpoints

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
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


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_async_session)
):
    """
    List all users (Superadmin only)

    - **skip**: Number of users to skip
    - **limit**: Maximum number of users to return
    """
    from sqlalchemy import select
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user by ID (Superadmin only)
    """
    user = await auth_service._get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update user by ID (Superadmin only)

    Superadmins can update any user's information including role and status.
    """
    updated_user = await auth_service.update_user(user_id, user_data)
    logger.info(f"Superadmin {current_user.email} updated user {updated_user.email}")
    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Deactivate user (Superadmin only)

    This sets the user status to inactive rather than deleting the record.
    """
    from app.domains.auth.models import UserStatus

    user_data = UserUpdate(status=UserStatus.INACTIVE)
    updated_user = await auth_service.update_user(user_id, user_data)

    # Logout all user sessions
    await auth_service.logout_all_sessions(user_id)

    logger.info(f"Superadmin {current_user.email} deactivated user {updated_user.email}")
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/unlock", status_code=status.HTTP_200_OK)
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