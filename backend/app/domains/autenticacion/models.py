"""
User and Authentication Models
"""

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User roles for authorization"""

    SUPERADMIN = "SUPERADMIN"
    EPIDEMIOLOGO = "EPIDEMIOLOGO"


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class User(SQLModel, table=True):
    """User model with modern security practices"""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    contrasena_hasheada: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)

    # Role and status
    rol: UserRole = Field(default=UserRole.EPIDEMIOLOGO)
    estado: UserStatus = Field(default=UserStatus.ACTIVE)

    # Security fields
    es_email_verificado: bool = Field(default=False)
    token_verificacion_email: str | None = Field(default=None, max_length=255)
    token_reset_contrasena: str | None = Field(default=None, max_length=255)
    expiracion_reset_contrasena: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    # Audit fields
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    ultimo_login: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    intentos_login: int = Field(default=0)
    bloqueado_hasta: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )


class UserSession(SQLModel, table=True):
    """Track user sessions for security"""

    __tablename__ = "user_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_sesion: str = Field(unique=True, index=True, max_length=255)

    # Session metadata
    direccion_ip: str | None = Field(default=None, max_length=45)  # IPv6 support
    agente_usuario: str | None = Field(default=None, max_length=500)
    huella_dispositivo: str | None = Field(default=None, max_length=255)

    # Session lifecycle
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    expira_en: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    ultima_actividad: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    es_activa: bool = Field(default=True)

    # Relationships (disabled to avoid sync/async conflicts)
    # user: Optional[User] = Relationship()


class UserLogin(SQLModel, table=True):
    """Audit log for login attempts"""

    __tablename__ = "user_logins"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    email_intentado: str = Field(max_length=255, index=True)

    # Login attempt details
    exito: bool = Field(default=False)
    motivo_fallo: str | None = Field(default=None, max_length=255)
    direccion_ip: str | None = Field(default=None, max_length=45)
    agente_usuario: str | None = Field(default=None, max_length=500)

    # Timing
    intentado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )

    # Relationships (disabled to avoid sync/async conflicts)
    # user: Optional[User] = Relationship()
