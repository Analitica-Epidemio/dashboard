"""
Security utilities for authentication
Modern practices including password hashing, JWT tokens, rate limiting
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
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


# JWT Bearer security
security = HTTPBearer()


class PasswordSecurity:
    """Password hashing and verification utilities"""

    @staticmethod
    def verificar_contrasena(contrasena_plana: str, contrasena_hasheada: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(
            contrasena_plana.encode("utf-8"), contrasena_hasheada.encode("utf-8")
        )

    @staticmethod
    def obtener_hash_contrasena(contrasena: str) -> str:
        """Hash a password"""
        return bcrypt.hashpw(
            contrasena.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    @staticmethod
    def validar_fortaleza_contrasena(contrasena: str) -> tuple[bool, str]:
        """
        Validate password strength according to modern security standards
        Returns (is_valid, error_message)
        """
        if len(contrasena) < SecurityConfig.MIN_PASSWORD_LENGTH:
            return (
                False,
                f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters",
            )

        if len(contrasena) > SecurityConfig.MAX_PASSWORD_LENGTH:
            return (
                False,
                f"Password must be at most {SecurityConfig.MAX_PASSWORD_LENGTH} characters",
            )

        # Check for at least one digit
        if not any(char.isdigit() for char in contrasena):
            return False, "Password must contain at least one digit"

        # Check for at least one uppercase letter
        if not any(char.isupper() for char in contrasena):
            return False, "Password must contain at least one uppercase letter"

        # Check for at least one lowercase letter
        if not any(char.islower() for char in contrasena):
            return False, "Password must contain at least one lowercase letter"

        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in contrasena):
            return False, "Password must contain at least one special character"

        return True, ""


class TokenSecurity:
    """JWT token utilities"""

    @staticmethod
    def crear_token_acceso(
        datos: dict, delta_expiracion: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        a_codificar = datos.copy()

        if delta_expiracion:
            expira = datetime.now(timezone.utc) + delta_expiracion
        else:
            expira = datetime.now(timezone.utc) + timedelta(
                minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        a_codificar.update({"exp": expira, "type": "access"})
        jwt_codificado = jwt.encode(
            a_codificar, settings.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM
        )
        return str(jwt_codificado)

    @staticmethod
    def crear_token_refresco(datos: dict) -> str:
        """Create JWT refresh token"""
        a_codificar = datos.copy()
        expira = datetime.now(timezone.utc) + timedelta(
            days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS
        )
        a_codificar.update({"exp": expira, "type": "refresh"})
        jwt_codificado = jwt.encode(
            a_codificar, settings.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM
        )
        return str(jwt_codificado)

    @staticmethod
    def verificar_token(token: str, tipo_token: str = "access") -> Optional[TokenData]:
        """
        Verify and decode JWT token
        Returns TokenData if valid, None if invalid
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM]
            )

            # Check token type
            if payload.get("type") != tipo_token:
                logger.warning(
                    f"Token type mismatch. Expected: {tipo_token}, Got: {payload.get('type')}"
                )
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

            email: Optional[str] = payload.get("email")
            rol: Optional[str] = payload.get("role")
            id_sesion_raw = payload.get("session_id")
            id_sesion: Optional[int] = (
                int(id_sesion_raw) if id_sesion_raw is not None else None
            )

            token_data = TokenData(
                user_id=user_id, email=email, rol=rol, id_sesion=id_sesion
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
    def generar_token_sesion() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def es_sesion_expirada(expiracion_sesion: datetime) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > expiracion_sesion

    @staticmethod
    def obtener_expiracion_sesion(horas: Optional[int] = None) -> datetime:
        """Get session expiry time"""
        if horas is None:
            horas = SecurityConfig.SESSION_EXPIRE_HOURS
        return datetime.now(timezone.utc) + timedelta(hours=horas)


class SecurityTokens:
    """Utilities for generating secure tokens"""

    @staticmethod
    def generar_token_verificacion() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(SecurityConfig.VERIFICATION_TOKEN_LENGTH)

    @staticmethod
    def generar_token_reset() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(SecurityConfig.RESET_TOKEN_LENGTH)

    @staticmethod
    def generar_api_key() -> str:
        """Generate API key for service accounts"""
        return f"epid_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"


class RateLimiter:
    """
    Redis-based rate limiter for login attempts.

    Funciona consistentemente entre múltiples workers/procesos.
    REQUIERE Redis - sin fallback (Docker siempre disponible).
    """

    _redis_client = None
    _PREFIX = "rate_limit:"

    @classmethod
    def _get_redis(cls) -> Any:
        """Get Redis connection lazily."""
        if cls._redis_client is None:
            import redis

            cls._redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3
            )
        return cls._redis_client

    @classmethod
    def esta_limitado(
        cls, identificador: str, max_intentos: Optional[int] = None
    ) -> bool:
        """Check if identifier is rate limited"""
        if max_intentos is None:
            max_intentos = SecurityConfig.MAX_LOGIN_ATTEMPTS

        redis_client = cls._get_redis()
        clave = f"{cls._PREFIX}{identificador}"
        conteo = redis_client.get(clave)

        if conteo is None:
            return False
        return int(conteo) >= max_intentos

    @classmethod
    def registrar_intento(cls, identificador: str, exito: bool = False) -> None:
        """Record a login attempt"""
        redis_client = cls._get_redis()
        clave = f"{cls._PREFIX}{identificador}"

        if exito:
            # Reset on successful login
            redis_client.delete(clave)
        else:
            # Increment failed attempts with expiry
            pipe = redis_client.pipeline()
            pipe.incr(clave)
            pipe.expire(clave, SecurityConfig.LOCKOUT_DURATION_MINUTES * 60)
            pipe.execute()

    @classmethod
    def limpiar_intentos(cls, identificador: str) -> None:
        """Clear rate limit for identifier"""
        redis_client = cls._get_redis()
        redis_client.delete(f"{cls._PREFIX}{identificador}")


def crear_excepcion_credenciales(
    detalle: str = "Could not validate credentials",
) -> HTTPException:
    """Create standardized credentials exception"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )
