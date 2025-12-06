"""Modelos de establecimientos de salud y su participación en eventos epidemiológicos."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, Text
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.territorio.geografia_models import Localidad
    from app.domains.vigilancia_nominal.models.atencion import (
        DiagnosticoCasoEpidemiologico,
    )
    from app.domains.vigilancia_nominal.models.salud import MuestraCasoEpidemiologico


class Establecimiento(BaseModel, table=True):
    """
    Catálogo de establecimientos de salud.

    Registra información básica de establecimientos donde se realizan
    atenciones médicas, toma de muestras, diagnósticos y tratamientos.
    Datos obtenidos del Instituto Geográfico Nacional (IGN) - Capa: ign:salud_020801.
    """

    __tablename__ = "establecimiento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre del establecimiento"
    )

    source: Optional[str] = Field(
        None,
        max_length=20,
        description="Origen de los datos: 'IGN' (Instituto Geográfico Nacional) o 'SNVS' (Sistema Nacional de Vigilancia)",
    )

    # Campos IGN (Instituto Geográfico Nacional)
    codigo_refes: Optional[str] = Field(
        None, max_length=50, description="Código GID del IGN (antes REFES)"
    )

    # Campos SNVS (para establecimientos creados desde CSVs)
    codigo_snvs: Optional[str] = Field(
        None, max_length=20, description="ID del establecimiento en SNVS (si aplica)"
    )
    latitud: Optional[float] = Field(
        None, description="Latitud del establecimiento (WGS84)"
    )
    longitud: Optional[float] = Field(
        None, description="Longitud del establecimiento (WGS84)"
    )

    # Foreign Keys - Localidad
    id_localidad_indec: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        index=True,
        description="ID INDEC de la localidad donde se encuentra el establecimiento",
    )

    # Campos de mapeo SNVS → IGN
    mapeo_validado: Optional[bool] = Field(
        None, description="Si el mapeo SNVS→IGN fue validado manualmente"
    )
    mapeo_confianza: Optional[str] = Field(
        None,
        max_length=20,
        description="Nivel de confianza del mapeo: HIGH, MEDIUM, LOW",
    )
    mapeo_score: Optional[float] = Field(
        None, description="Score de similitud del mapeo (0-100)"
    )
    mapeo_similitud_nombre: Optional[float] = Field(
        None, description="Similitud de nombre del mapeo (0-100)"
    )
    mapeo_razon: Optional[str] = Field(
        None, sa_column=Column(Text), description="Razón/descripción del mapeo"
    )
    mapeo_es_manual: Optional[bool] = Field(
        None, description="Si el mapeo fue creado manualmente o automático"
    )

    # Relaciones
    localidad_establecimiento: Mapped[Optional["Localidad"]] = Relationship(
        back_populates="establecimientos"
    )
    muestras: Mapped[List["MuestraCasoEpidemiologico"]] = Relationship(
        back_populates="establecimiento"
    )
    diagnosticos: Mapped[List["DiagnosticoCasoEpidemiologico"]] = Relationship(
        back_populates="establecimiento"
    )
