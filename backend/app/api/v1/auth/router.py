"""
Auth router - Organizes authentication endpoints by responsibility
"""

from typing import List
from fastapi import APIRouter, status

from app.domains.auth.schemas import Token, UserResponse, SessionInfo
from .login import login, refresh_access_token
from .logout import logout
from .logout_all import logout_all_sessions
from .get_me import get_current_user_info
from .update_me import update_current_user
from .change_password import change_password
from .get_sessions import get_user_sessions
from .logout_session import logout_session
from .create_user import create_user
from .list_users import list_users
from .get_user import get_user
from .update_user import update_user
from .deactivate_user import deactivate_user
from .unlock_user import unlock_user

# Crear router principal
router = APIRouter(prefix="/auth", tags=["Authentication"])

# === PUBLIC ENDPOINTS ===

# Login endpoints (public)
router.add_api_route(
    "/login",
    login,
    methods=["POST"],
    response_model=Token,
)

router.add_api_route(
    "/refresh",
    refresh_access_token,
    methods=["POST"],
    response_model=Token,
)

# === AUTHENTICATED ENDPOINTS ===

# Profile endpoints (authenticated users)
router.add_api_route(
    "/logout",
    logout,
    methods=["POST"],
    status_code=status.HTTP_204_NO_CONTENT,
)

router.add_api_route(
    "/logout-all",
    logout_all_sessions,
    methods=["POST"],
    status_code=status.HTTP_204_NO_CONTENT,
)

router.add_api_route(
    "/me",
    get_current_user_info,
    methods=["GET"],
    response_model=UserResponse,
)

router.add_api_route(
    "/me",
    update_current_user,
    methods=["PUT"],
    response_model=UserResponse,
)

router.add_api_route(
    "/change-password",
    change_password,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/sessions",
    get_user_sessions,
    methods=["GET"],
    response_model=List[SessionInfo],
)

router.add_api_route(
    "/sessions/{session_id}",
    logout_session,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
)

# === SUPERADMIN ENDPOINTS ===

# User management endpoints (superadmin only)
router.add_api_route(
    "/users",
    create_user,
    methods=["POST"],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/users",
    list_users,
    methods=["GET"],
    response_model=List[UserResponse],
)

router.add_api_route(
    "/users/{user_id}",
    get_user,
    methods=["GET"],
    response_model=UserResponse,
)

router.add_api_route(
    "/users/{user_id}",
    update_user,
    methods=["PUT"],
    response_model=UserResponse,
)

router.add_api_route(
    "/users/{user_id}",
    deactivate_user,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
)

router.add_api_route(
    "/users/{user_id}/unlock",
    unlock_user,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
)