"""Modelos de establecimientos de salud y su participación en eventos epidemiológicos."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.diagnosticos.models import DiagnosticoEvento
    from app.domains.localidades.models import Localidad
    from app.domains.atencion_medica.salud_models.models import MuestraEvento


class Establecimiento(BaseModel, table=True):
    """
    Catálogo de establecimientos de salud.

    Registra información básica de establecimientos donde se realizan
    atenciones médicas, toma de muestras, diagnósticos y tratamientos.
    """

    __tablename__ = "establecimiento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre del establecimiento"
    )

    # Foreign Keys
    id_localidad_establecimiento: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )

    # Relaciones
    localidad_establecimiento: Optional["Localidad"] = Relationship(
        back_populates="establecimientos"
    )
    muestras: List["MuestraEvento"] = Relationship(back_populates="establecimiento")
    diagnosticos: List["DiagnosticoEvento"] = Relationship(
        back_populates="establecimiento"
    )
