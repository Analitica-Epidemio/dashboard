"""
Authentication service layer
Handles user management, authentication, and session management
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, Request, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserLogin, UserSession, UserStatus
from .schemas import SessionInfo, Token, UserCreate, UserUpdate
from .schemas import UserLogin as UserLoginSchema
from .security import (
    PasswordSecurity,
    SecurityConfig,
    SecurityTokens,
    SessionSecurity,
    TokenSecurity,
    create_credentials_exception,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with validation"""
        # Check if user already exists
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        is_valid, error_msg = PasswordSecurity.validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Create user
        hashed_password = PasswordSecurity.get_password_hash(user_data.password)
        verification_token = SecurityTokens.generate_verification_token()

        user = User(
            email=user_data.email,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            hashed_password=hashed_password,
            role=user_data.role,
            email_verification_token=verification_token,
            status=UserStatus.ACTIVE,  # Auto-activate for now
            is_email_verified=False
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Created new user: {user.email}")
        return user

    async def authenticate_user(
        self,
        credentials: UserLoginSchema,
        request: Request
    ) -> Tuple[User, Token]:
        """Authenticate user and create session - simplified and fixed"""
        # Get user with all needed data in single query
        user = await self._get_user_by_email(credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Extract ALL needed values BEFORE any database operations
        user_id = user.id
        user_email = user.email
        user_nombre = user.nombre
        user_apellido = user.apellido
        user_role = user.role
        user_status = user.status
        user_locked_until = user.locked_until
        user_hashed_password = user.hashed_password

        # Check if user is locked
        if user_locked_until and user_locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked"
            )

        # Check user status
        if user_status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user_status.value}"
            )

        # Verify password
        if not PasswordSecurity.verify_password(credentials.password, user_hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update user for successful login
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)

        # Commit and refresh in single transaction
        await self.db.commit()
        await self.db.refresh(user)

        # Create session
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        session = await self._create_user_session(
            user_id, ip_address, user_agent, credentials.remember_me
        )

        # Create tokens using extracted values
        token = self._create_tokens_with_data(
            user_id, user_email, user_nombre, user_apellido, user_role, session
        )

        logger.info(f"User {user_email} authenticated successfully")
        return user, token

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        token_data = TokenSecurity.verify_token(refresh_token, "refresh")
        if not token_data or not token_data.session_id:
            raise create_credentials_exception("Invalid refresh token")

        # Get session
        session = await self._get_session(token_data.session_id)
        if not session or not session.is_active:
            raise create_credentials_exception("Session expired or invalid")

        # Get user
        user = await self._get_user_by_id(session.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise create_credentials_exception("User not found or inactive")

        # Update session activity
        session.last_activity = datetime.now(timezone.utc)
        await self.db.commit()

        # Create new tokens
        return self._create_tokens(user, session)

    async def logout_user(self, session_id: int) -> None:
        """Logout user by deactivating session"""
        session = await self._get_session(session_id)
        if session:
            session.is_active = False
            await self.db.commit()
            logger.info(f"User session {session_id} logged out")

    async def logout_specific_session(self, user_id: int, session_id: int) -> bool:
        """
        Logout a specific session owned by the user
        Returns True if session was found and logged out, False otherwise
        """
        session = await self._get_session(session_id)

        # Verificar que la sesión existe y pertenece al usuario
        if not session or session.user_id != user_id:
            return False

        # Cerrar la sesión
        session.is_active = False
        await self.db.commit()
        logger.info(f"User {user_id} logged out session {session_id}")
        return True

    async def logout_all_sessions(self, user_id: int) -> None:
        """Logout user from all sessions"""
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(is_active=False)
        )
        await self.db.commit()
        logger.info(f"All sessions for user {user_id} logged out")

    async def get_user_sessions(self, user_id: int, current_session_id: int = None) -> List[SessionInfo]:
        """Get active sessions for user"""
        result = await self.db.execute(
            select(UserSession)
            .where(and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc)
            ))
            .order_by(UserSession.last_activity.desc())
        )
        sessions = result.scalars().all()

        return [
            SessionInfo(
                id=session.id,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                created_at=session.created_at,
                last_activity=session.last_activity,
                is_current=(session.id == current_session_id)
            )
            for session in sessions
        ]

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check for email conflicts
        if user_data.email and user_data.email != user.email:
            existing = await self._get_user_by_email(user_data.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Updated user {user.email}")
        return user

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        """Change user password"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not PasswordSecurity.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password
        is_valid, error_msg = PasswordSecurity.validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Update password
        user.hashed_password = PasswordSecurity.get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Logout all other sessions for security
        await self.logout_all_sessions(user_id)

        logger.info(f"Password changed for user {user.email}")

    # Private helper methods

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()



    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_session(self, session_id: int) -> Optional[UserSession]:
        """Get session by ID"""
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def _create_user_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> UserSession:
        """Create new user session - fixed version without problematic cleanup"""
        # Session duration
        hours = 24 * 7 if remember_me else SecurityConfig.SESSION_EXPIRE_HOURS

        session = UserSession(
            user_id=user_id,
            session_token=SessionSecurity.generate_session_token(),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=SessionSecurity.get_session_expiry(hours)
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _cleanup_user_sessions(self, user_id: int) -> None:
        """Clean up old sessions for user"""
        # Deactivate expired sessions
        await self.db.execute(
            update(UserSession)
            .where(and_(
                UserSession.user_id == user_id,
                UserSession.expires_at < datetime.now(timezone.utc)
            ))
            .values(is_active=False)
        )

        # Keep only the most recent active sessions - use subquery to avoid loading objects
        subquery = select(UserSession.id).where(and_(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )).order_by(UserSession.last_activity.desc()).offset(SecurityConfig.MAX_SESSIONS_PER_USER - 1)

        # Deactivate old sessions using direct UPDATE
        await self.db.execute(
            update(UserSession)
            .where(UserSession.id.in_(subquery))
            .values(is_active=False)
        )

        await self.db.commit()

    def _create_tokens(self, user: User, session: UserSession) -> Token:
        """Create JWT tokens for user session"""
        return self._create_tokens_with_data(
            user.id, user.email, user.nombre, user.apellido, user.role, session
        )

    def _create_tokens_with_data(
        self, user_id: int, user_email: str, user_nombre: str, user_apellido: str,
        user_role, session: UserSession
    ) -> Token:
        """Create JWT tokens using extracted data (avoids accessing expired user object)"""
        from .schemas import TokenUser

        token_data = {
            "sub": str(user_id),  # JWT standard requires sub to be a string
            "email": user_email,
            "role": user_role.value,
            "session_id": session.id
        }

        access_token = TokenSecurity.create_access_token(token_data)
        refresh_token = TokenSecurity.create_refresh_token(token_data)

        # Include user info in response
        user_info = TokenUser(
            id=user_id,
            email=user_email,
            nombre=user_nombre,
            apellido=user_apellido,
            role=user_role
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info
        )

    async def _log_login_attempt(
        self,
        email: str,
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> None:
        """Log login attempt for audit purposes"""
        login_log = UserLogin(
            user_id=user_id,
            email_attempted=email,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(login_log)
        await self.db.commit()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"