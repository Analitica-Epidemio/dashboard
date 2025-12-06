"""
Modelo de notificaciones semanales de vigilancia pasiva.

Representa el encabezado de una notificación semanal de un establecimiento
(mapea a ID_ENCABEZADO del SNVS).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, List, Optional

from pydantic import field_validator
from sqlalchemy import BigInteger, Index, SmallInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.domains.vigilancia_agregada.constants import (
    EstadoNotificacion,
    OrigenDatosPasivos,
)

if TYPE_CHECKING:
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.vigilancia_agregada.models.conteos import (
        ConteoCamasIRA,
        ConteoCasosClinicos,
        ConteoEstudiosLab,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Tipos anotados para validación
# ═══════════════════════════════════════════════════════════════════════════

SemanaEpidemiologica = Annotated[int, Field(ge=1, le=53)]
AnioEpidemiologico = Annotated[int, Field(ge=2000, le=2100)]


class NotificacionSemanal(BaseModel, table=True):
    """
    Notificación semanal de vigilancia pasiva de un establecimiento.

    Representa el "encabezado" de una carga semanal (ID_ENCABEZADO en SNVS).
    Cada establecimiento envía una notificación por semana epidemiológica
    por tipo de vigilancia (clínica, laboratorio, internación).

    Una notificación contiene múltiples conteos (líneas de detalle) que
    desglosan cantidades por evento/demografía.

    Ejemplo:
        Hospital Zonal de Trelew envía notificación de SE 40/2025:
        - 47 casos de ETI en mujeres de 15-24 años
        - 23 casos de ETI en hombres de 15-24 años
        - 12 casos de Neumonía en adultos mayores
        - etc.

    Attributes:
        id_snvs: ID único de la notificación en SNVS
        anio: Año epidemiológico (2024, 2025, ...)
        semana: Semana epidemiológica (1-53)
        origen: Tipo de datos (clínico, laboratorio, internación)
        establecimiento_id: Establecimiento que notifica
    """

    __tablename__ = "notificacion_semanal"
    __table_args__ = (
        Index("ix_notif_periodo", "anio", "semana"),
        Index("ix_notif_estab_periodo", "establecimiento_id", "anio", "semana"),
        Index("ix_notif_snvs", "id_snvs"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="ID de la notificación en SNVS (ID_ENCABEZADO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Período temporal
    # ═══════════════════════════════════════════════════════════════

    anio: int = Field(
        ...,
        ge=2000,
        le=2100,
        sa_type=SmallInteger,
        description="Año epidemiológico",
    )

    semana: int = Field(
        ...,
        ge=1,
        le=53,
        sa_type=SmallInteger,
        description="Semana epidemiológica (1-53)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Clasificación
    # ═══════════════════════════════════════════════════════════════

    origen: OrigenDatosPasivos = Field(
        ...,
        description="Origen: clinico (CLI_P26), laboratorio (LAB_P26), internacion (CLI_P26_INT)",
    )

    estado: EstadoNotificacion = Field(
        default=EstadoNotificacion.PENDIENTE,
        description="Estado de la notificación",
    )

    # ═══════════════════════════════════════════════════════════════
    # Auditoría SNVS (datos originales de la carga)
    # ═══════════════════════════════════════════════════════════════

    fecha_registro_snvs: Optional[datetime] = Field(
        None,
        description="Fecha/hora de registro en SNVS (FECHAREGISTROENCABEZADO)",
    )

    usuario_snvs: Optional[str] = Field(
        None,
        max_length=200,
        description="Usuario que registró en SNVS (USUARIOREGISTROENCABEZADO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Geografía (desnormalizado para queries rápidas)
    # ═══════════════════════════════════════════════════════════════

    establecimiento_nombre_original: Optional[str] = Field(
        None,
        max_length=300,
        description="Nombre del establecimiento como vino en el archivo (ORIGEN)",
    )

    localidad_codigo_snvs: Optional[int] = Field(
        None,
        description="Código de localidad SNVS (CODIGO_LOCALIDAD)",
    )

    localidad_nombre: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre de localidad (LOCALIDAD)",
    )

    departamento_codigo_snvs: Optional[int] = Field(
        None,
        description="Código de departamento SNVS (CODIGO_DEPTO)",
    )

    departamento_nombre: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre de departamento (DEPARTAMENTO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Foreign Keys
    # ═══════════════════════════════════════════════════════════════

    establecimiento_id: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        index=True,
        description="ID del establecimiento (si está mapeado en nuestro catálogo)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Validators
    # ═══════════════════════════════════════════════════════════════

    @field_validator("semana")
    @classmethod
    def validar_semana(cls, v: int) -> int:
        """Valida que la semana esté en rango 1-53."""
        if not 1 <= v <= 53:
            raise ValueError(f"Semana debe estar entre 1 y 53, recibido: {v}")
        return v

    @field_validator("anio")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        """Valida que el año sea razonable."""
        if not 2000 <= v <= 2100:
            raise ValueError(f"Año debe estar entre 2000 y 2100, recibido: {v}")
        return v

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    establecimiento: Optional["Establecimiento"] = Relationship()

    conteos_clinicos: List["ConteoCasosClinicos"] = Relationship(
        back_populates="notificacion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    conteos_laboratorio: List["ConteoEstudiosLab"] = Relationship(
        back_populates="notificacion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    conteos_internacion: List["ConteoCamasIRA"] = Relationship(
        back_populates="notificacion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # ═══════════════════════════════════════════════════════════════
    # Propiedades computadas
    # ═══════════════════════════════════════════════════════════════

    @property
    def periodo_key(self) -> str:
        """Retorna una clave única del período: 'YYYY-WNN'."""
        return f"{self.anio}-W{self.semana:02d}"

    @property
    def tiene_datos(self) -> bool:
        """Indica si la notificación tiene al menos un conteo > 0."""
        return self.estado == EstadoNotificacion.CARGADA_CON_CASOS
