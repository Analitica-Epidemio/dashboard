"""
Authentication Pydantic schemas for requests/responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EPIDEMIOLOGO


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response (public info)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str = Field(min_length=1)
    remember_me: bool = False


class UserChangePassword(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    session_id: Optional[int] = None


class RefreshToken(BaseModel):
    """Refresh token request"""
    refresh_token: str


class SessionInfo(BaseModel):
    """Session information response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_current: bool = False