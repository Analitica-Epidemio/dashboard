"""
Authentication Pydantic schemas for requests/responses
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user"""

    contrasena: str = Field(min_length=8, max_length=128)
    rol: UserRole = UserRole.EPIDEMIOLOGO


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: EmailStr | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    rol: UserRole | None = None
    estado: UserStatus | None = None


class UserResponse(UserBase):
    """Schema for user response (public info)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    rol: UserRole
    estado: UserStatus
    es_email_verificado: bool
    created_at: datetime
    ultimo_login: datetime | None = None


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    contrasena: str = Field(min_length=1)
    recordarme: bool = False


class UserChangePassword(BaseModel):
    """Schema for changing password"""

    contrasena_actual: str
    nueva_contrasena: str = Field(min_length=8, max_length=128)


class PasswordReset(BaseModel):
    """Schema for password reset request"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""

    token: str
    nueva_contrasena: str = Field(min_length=8, max_length=128)


class TokenUser(BaseModel):
    """User info in token response"""

    id: int
    email: str
    nombre: str
    apellido: str
    rol: UserRole


class Token(BaseModel):
    """JWT Token response with user info"""

    token_acceso: str
    token_type: str = "bearer"
    expira_en: int
    token_refresco: str | None = None
    usuario: TokenUser | None = None


class TokenData(BaseModel):
    """Token payload data"""

    user_id: int | None = None
    email: str | None = None
    rol: str | None = None
    id_sesion: int | None = None


class RefreshToken(BaseModel):
    """Refresh token request"""

    token_refresco: str


class SessionInfo(BaseModel):
    """Session information response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    direccion_ip: str | None
    agente_usuario: str | None
    created_at: datetime
    ultima_actividad: datetime
    es_actual: bool = False
