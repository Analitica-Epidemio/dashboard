"""Modelos del dominio de Viajes y desplazamientos epidemiológicos."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.territorio.geografia_models import Localidad
    from .ciudadanos_models import Ciudadano


class ViajesCiudadano(BaseModel, table=True):
    """
    Registro de viajes realizados por ciudadanos.

    Importante para rastreo epidemiológico de posibles exposiciones
    o transmisión de enfermedades entre regiones.
    """

    __tablename__ = "viajes_ciudadano"
    __table_args__ = {"extend_existing": True}

    # Usar ID SNVS como identificador único
    id_snvs_viaje_epidemiologico: int = Field(
        unique=True, index=True, description="ID SNVS del viaje epidemiológico"
    )

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_localidad_destino_viaje: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad de destino del viaje",
    )

    # Campos propios
    fecha_inicio_viaje: Optional[date] = Field(
        None, description="Fecha de inicio del viaje"
    )
    fecha_finalizacion_viaje: Optional[date] = Field(
        None, description="Fecha de finalización del viaje"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="viajes")
    localidad: Optional["Localidad"] = Relationship()