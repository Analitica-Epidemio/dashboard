"""
Modelos base para toda la aplicación.

Proveen funcionalidad común como timestamps, soft delete, y métodos útiles.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin para campos de auditoría temporal."""

    created_at: datetime = Field(
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
        description="Fecha y hora de creación del registro",
    )

    updated_at: datetime = Field(
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
            "nullable": False,
        },
        description="Fecha y hora de última actualización",
    )


class SoftDeleteMixin(SQLModel):
    """Mixin para soft delete (borrado lógico)."""

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
        description="Fecha de borrado lógico",
    )

    is_active: bool = Field(
        default=True, description="Indica si el registro está activo"
    )

    @property
    def is_deleted(self) -> bool:
        """Verifica si el registro está eliminado."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca el registro como eliminado."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_active = False

    def restore(self) -> None:
        """Restaura un registro eliminado."""
        self.deleted_at = None
        self.is_active = True


class BaseModel(TimestampMixin, SQLModel):
    """
    Modelo base para todas las entidades principales.

    Incluye:
    - ID autoincremental
    - Timestamps (created_at, updated_at)
    - Configuración común
    """

    id: Optional[int] = Field(
        default=None, primary_key=True, description="Identificador único"
    )

    class Config:
        # Permite usar el modelo con ORM
        orm_mode = True
        # Valida datos en asignación
        validate_assignment = True
        # Usa enum por valor
        use_enum_values = True
        # Permite campos arbitrarios en JSON
        arbitrary_types_allowed = True

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Override para excluir campos None por defecto."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza el modelo desde un diccionario."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class BaseModelWithSoftDelete(BaseModel, SoftDeleteMixin):
    """
    Modelo base con soft delete.

    Usar para entidades que no deben eliminarse físicamente
    (ej: usuarios, datos sensibles, registros de auditoría).
    """

    pass


class BaseModelWithoutId(TimestampMixin, SQLModel):
    """
    Modelo base sin ID para tablas intermedias.

    Útil para:
    - Tablas de relación muchos-a-muchos
    - Tablas con llaves primarias compuestas
    """

    class Config:
        orm_mode = True
        validate_assignment = True
        use_enum_values = True
