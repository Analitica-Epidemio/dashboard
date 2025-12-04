"""Modelos del dominio de Ámbitos de concurrencia epidemiológica."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.core.shared.enums import FrecuenciaOcurrencia

if TYPE_CHECKING:
    from app.domains.territorio.geografia_models import Localidad

    from .eventos.models import Evento


class AmbitosConcurrenciaEvento(BaseModel, table=True):
    """Ámbitos de concurrencia durante eventos epidemiológicos"""

    __tablename__ = "ambitos_concurrencia_evento"
    __table_args__ = (
        UniqueConstraint('id_evento', name='uq_ambito_evento'),
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    id_localidad_ambito_ocurrencia: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )

    # Campos propios
    nombre_lugar_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Nombre del lugar"
    )
    tipo_lugar_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Tipo de lugar"
    )
    localidad_ambito_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Localidad del ámbito"
    )
    fecha_ambito_ocurrencia: Optional[date] = Field(
        None, description="Fecha de ocurrencia"
    )
    frecuencia_concurrencia: Optional[FrecuenciaOcurrencia] = Field(
        None, description="Frecuencia de concurrencia al lugar"
    )
    es_sitio_probable_adquisicion_infeccion: Optional[bool] = Field(
        None, description="Es el sitio probable donde se adquirió la infección"
    )
    es_sitio_probable_diseminacion_infeccion: Optional[bool] = Field(
        None, description="Es el sitio probable donde se diseminó la infección"
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="ambitos_concurrencia")
    localidad: Optional["Localidad"] = Relationship()