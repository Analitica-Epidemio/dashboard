"""Modelos del dominio de Animales en eventos epidemiológicos."""

from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import JSON, BigInteger, Column
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.eventos_epidemiologicos.eventos.models import Evento
    from app.domains.territorio.geografia_models import Localidad


class Animal(BaseModel, table=True):
    """Datos principales de animales para eventos epidemiológicos"""

    __tablename__ = "animal"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    especie: str = Field(..., max_length=100, description="Especie del animal")
    raza: Optional[str] = Field(None, max_length=100, description="Raza del animal")
    sexo: Optional[str] = Field(None, max_length=20, description="Sexo del animal")
    edad_aproximada: Optional[int] = Field(None, description="Edad aproximada en meses")
    identificacion: Optional[str] = Field(
        None,
        max_length=100,
        description="Identificación del animal (collar, chip, etc)",
    )

    # Campos adicionales para mejor clasificación
    subespecie: Optional[str] = Field(
        None,
        max_length=100,
        description="Subespecie o nombre científico completo (ej: TADARIDA BRASILIENSIS)",
    )
    clasificacion_taxonomica: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Información taxonómica estructurada extraída automáticamente",
    )
    origen_deteccion: Optional[str] = Field(
        None,
        max_length=255,
        description="Cómo se detectó: 'automatico', 'manual', 'revision'",
    )
    confidence_deteccion: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confianza en la detección automática (0.0 a 1.0)",
    )

    # Datos del propietario/responsable
    propietario_nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre del propietario"
    )
    propietario_contacto: Optional[str] = Field(
        None, max_length=150, description="Contacto del propietario"
    )

    # Ubicación
    id_localidad_indec: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )
    direccion: Optional[str] = Field(
        None, max_length=200, description="Dirección donde se encuentra el animal"
    )

    # Relaciones
    localidad: Optional["Localidad"] = Relationship()
    eventos: List["Evento"] = Relationship(back_populates="animal")