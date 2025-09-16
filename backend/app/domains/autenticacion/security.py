"""
Security utilities for authentication
Modern practices including password hashing, JWT tokens, rate limiting
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings

from .schemas import TokenData


class SecurityConfig:
    """Security configuration constants"""
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128

    # JWT settings
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours for development
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Session settings
    SESSION_EXPIRE_HOURS = 24
    MAX_SESSIONS_PER_USER = 5

    # Security limits
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Token lengths
    VERIFICATION_TOKEN_LENGTH = 32
    RESET_TOKEN_LENGTH = 32


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer security
security = HTTPBearer()


class PasswordSecurity:
    """Password hashing and verification utilities"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength according to modern security standards
        Returns (is_valid, error_message)
        """
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters"

        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            return False, f"Password must be at most {SecurityConfig.MAX_PASSWORD_LENGTH} characters"

        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"

        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"

        # Check for at least one lowercase letter
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"

        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character"

        return True, ""


class TokenSecurity:
    """JWT token utilities"""

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=SecurityConfig.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=SecurityConfig.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """
        Verify and decode JWT token
        Returns TokenData if valid, None if invalid
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[SecurityConfig.ALGORITHM]
            )

            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
                return None

            # Extract token data (sub is a string per JWT standard)
            user_id_str = payload.get("sub")
            if user_id_str is None:
                return None

            try:
                user_id: int = int(user_id_str)  # Convert string sub to int
            except (ValueError, TypeError):
                logger.warning(f"Invalid user_id in token: {user_id_str}")
                return None

            email: str = payload.get("email")
            role: str = payload.get("role")
            session_id: int = payload.get("session_id")

            token_data = TokenData(
                user_id=user_id,
                email=email,
                role=role,
                session_id=session_id
            )
            return token_data

        except JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            return None
        except ValidationError as e:
            logger.warning(f"Token data validation error: {str(e)}")
            return None


class SessionSecurity:
    """Session management utilities"""

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def is_session_expired(session_expires_at: datetime) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > session_expires_at

    @staticmethod
    def get_session_expiry(hours: int = None) -> datetime:
        """Get session expiry time"""
        if hours is None:
            hours = SecurityConfig.SESSION_EXPIRE_HOURS
        return datetime.now(timezone.utc) + timedelta(hours=hours)


class SecurityTokens:
    """Utilities for generating secure tokens"""

    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(SecurityConfig.VERIFICATION_TOKEN_LENGTH)

    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(SecurityConfig.RESET_TOKEN_LENGTH)

    @staticmethod
    def generate_api_key() -> str:
        """Generate API key for service accounts"""
        return f"epid_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"


class RateLimiter:
    """Simple in-memory rate limiter for login attempts"""
    _attempts = {}

    @classmethod
    def is_rate_limited(cls, identifier: str, max_attempts: int = None) -> bool:
        """Check if identifier is rate limited"""
        if max_attempts is None:
            max_attempts = SecurityConfig.MAX_LOGIN_ATTEMPTS

        now = datetime.now(timezone.utc)

        if identifier not in cls._attempts:
            cls._attempts[identifier] = {"count": 0, "reset_time": now}
            return False

        attempt_data = cls._attempts[identifier]

        # Reset if lockout period has passed
        if now > attempt_data["reset_time"]:
            cls._attempts[identifier] = {"count": 0, "reset_time": now}
            return False

        return attempt_data["count"] >= max_attempts

    @classmethod
    def record_attempt(cls, identifier: str, success: bool = False) -> None:
        """Record a login attempt"""
        now = datetime.now(timezone.utc)

        if identifier not in cls._attempts:
            cls._attempts[identifier] = {"count": 0, "reset_time": now}

        if success:
            # Reset on successful login
            cls._attempts[identifier] = {"count": 0, "reset_time": now}
        else:
            # Increment failed attempts
            cls._attempts[identifier]["count"] += 1
            if cls._attempts[identifier]["count"] >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                cls._attempts[identifier]["reset_time"] = now + timedelta(
                    minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
                )

    @classmethod
    def clear_attempts(cls, identifier: str) -> None:
        """Clear rate limit for identifier"""
        if identifier in cls._attempts:
            del cls._attempts[identifier]


def create_credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    """Create standardized credentials exception"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )