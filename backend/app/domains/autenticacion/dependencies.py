"""
Authentication dependencies for FastAPI
"""
import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

from .models import User, UserRole, UserStatus
from .schemas import TokenData
from .security import SessionSecurity, TokenSecurity, crear_excepcion_credenciales
from .service import AuthService

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_async_session)) -> AuthService:
    """Get authentication service"""
    return AuthService(db)


async def get_current_user_token(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> TokenData:
    """
    Extract and validate current user from JWT token
    Returns TokenData for use in other dependencies
    """
    # Extract token from Authorization header
    if hasattr(token, 'credentials'):
        token_str = token.credentials
    else:
        token_str = str(token)

    logger.debug("Token validation attempt")

    # Verify token
    token_data = TokenSecurity.verificar_token(token_str, "access")
    if not token_data or not token_data.user_id:
        logger.warning("Token validation failed: Invalid or missing token data")
        raise crear_excepcion_credenciales()

    # Validate session if present
    if token_data.id_sesion:
        auth_service = AuthService(db)
        session = await auth_service._obtener_sesion(token_data.id_sesion)
        if not session or not session.es_activa:
            logger.warning(f"Session validation failed: Session {token_data.id_sesion} not found or inactive")
            raise crear_excepcion_credenciales("Session expired")

        # Check session expiry
        if SessionSecurity.es_sesion_expirada(session.expira_en):
            from datetime import datetime, timezone
            logger.warning(f"Session {token_data.id_sesion} expired. Expiry: {session.expira_en}, Current: {datetime.now(timezone.utc)}")
            session.es_activa = False
            await db.commit()
            raise crear_excepcion_credenciales("Session expired")

        # Update last activity to current time
        from datetime import datetime, timezone
        session.ultima_actividad = datetime.now(timezone.utc)
        await db.commit()

    logger.debug(f"Token validated successfully for user_id: {token_data.user_id}")
    return token_data


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get current authenticated user
    Validates user exists and is active
    """
    auth_service = AuthService(db)
    user = await auth_service._obtener_usuario_por_id(token_data.user_id)

    if not user:
        raise crear_excepcion_credenciales("User not found")

    if user.estado != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.estado.value}"
        )

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Does not raise exceptions for missing auth
    """
    try:
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        # Verify token
        token_data = TokenSecurity.verificar_token(token, "access")
        if not token_data or not token_data.user_id:
            return None

        # Get user
        auth_service = AuthService(db)
        user = await auth_service._obtener_usuario_por_id(token_data.user_id)

        if not user or user.estado != UserStatus.ACTIVE:
            return None

        return user
    except Exception:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for backward compatibility)
    """
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control
    Usage: @router.get("/admin", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
    """
    async def check_user_role(current_user: User = Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user

    return check_user_role


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Require superadmin role"""
    if current_user.rol != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return current_user


def require_any_role(current_user: User = Depends(get_current_user)) -> User:
    """Require any valid role (epidemiologo or superadmin)"""
    if current_user.rol not in [UserRole.EPIDEMIOLOGO, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid role required"
        )
    return current_user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Useful for endpoints that work for both authenticated and anonymous users
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        token_data = TokenSecurity.verificar_token(token, "access")
        if not token_data:
            return None

        auth_service = AuthService(db)
        user = await auth_service._obtener_usuario_por_id(token_data.user_id)
        if not user or user.estado != UserStatus.ACTIVE:
            return None

        return user

    except Exception:
        return None


class AuthorizedUser:
    """
    Enhanced user wrapper with authorization helpers
    """
    def __init__(self, user: User):
        self.user = user

    @property
    def is_superadmin(self) -> bool:
        return self.user.rol == UserRole.SUPERADMIN

    @property
    def is_epidemiologo(self) -> bool:
        return self.user.rol == UserRole.EPIDEMIOLOGO

    @property
    def can_write(self) -> bool:
        """Can create/modify data"""
        return self.user.rol in [UserRole.SUPERADMIN, UserRole.EPIDEMIOLOGO]

    @property
    def can_admin(self) -> bool:
        """Can perform admin functions"""
        return self.user.rol == UserRole.SUPERADMIN

    def can_access_organization(self, organization: str) -> bool:
        """Check if user can access specific organization data"""
        if self.is_superadmin:
            return True
        return self.user.organization == organization

    def can_modify_user(self, target_user: User) -> bool:
        """Check if user can modify another user"""
        if self.is_superadmin:
            return True
        return self.user.id == target_user.id  # Can modify self


async def get_authorized_user(
    current_user: User = Depends(get_current_user)
) -> AuthorizedUser:
    """Get user with authorization helpers"""
    return AuthorizedUser(current_user)
