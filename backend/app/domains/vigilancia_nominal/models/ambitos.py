"""
Ámbitos de concurrencia epidemiológica.

Registra los lugares donde el paciente estuvo antes de enfermar,
útil para identificar posibles sitios de adquisición de la infección.
"""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.core.constants import FrecuenciaOcurrencia

if TYPE_CHECKING:
    from app.domains.territorio.geografia_models import Localidad
    from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico


class AmbitosConcurrenciaCaso(BaseModel, table=True):
    """
    Ámbitos de concurrencia durante casos epidemiológicos.

    Registra lugares frecuentados por el paciente que podrían ser
    sitios de adquisición o diseminación de la infección.
    """

    __tablename__ = "ambitos_concurrencia_caso"
    __table_args__ = (
        UniqueConstraint('id_caso', name='uq_ambito_caso'),
    )

    # Foreign Keys
    id_caso: int = Field(foreign_key="caso_epidemiologico.id", description="ID del caso")
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
    caso: "CasoEpidemiologico" = Relationship(back_populates="ambitos_concurrencia")
    localidad: Optional["Localidad"] = Relationship()
