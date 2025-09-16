"""
User and Authentication Models
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User roles for authorization"""
    SUPERADMIN = "superadmin"
    EPIDEMIOLOGO = "epidemiologo"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(SQLModel, table=True):
    """User model with modern security practices"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)

    # Role and status
    role: UserRole = Field(default=UserRole.EPIDEMIOLOGO)
    status: UserStatus = Field(default=UserStatus.ACTIVE)

    # Security fields
    is_email_verified: bool = Field(default=False)
    email_verification_token: Optional[str] = Field(default=None, max_length=255)
    password_reset_token: Optional[str] = Field(default=None, max_length=255)
    password_reset_expires: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )

    # Audit fields
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    last_login: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )


class UserSession(SQLModel, table=True):
    """Track user sessions for security"""
    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    session_token: str = Field(unique=True, index=True, max_length=255)

    # Session metadata
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 support
    user_agent: Optional[str] = Field(default=None, max_length=500)
    device_fingerprint: Optional[str] = Field(default=None, max_length=255)

    # Session lifecycle
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    is_active: bool = Field(default=True)

    # Relationships (disabled to avoid sync/async conflicts)
    # user: Optional[User] = Relationship()


class UserLogin(SQLModel, table=True):
    """Audit log for login attempts"""
    __tablename__ = "user_logins"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    email_attempted: str = Field(max_length=255, index=True)

    # Login attempt details
    success: bool = Field(default=False)
    failure_reason: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # Timing
    attempted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    # Relationships (disabled to avoid sync/async conflicts)
    # user: Optional[User] = Relationship()