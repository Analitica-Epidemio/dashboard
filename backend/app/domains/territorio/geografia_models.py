"""
Modelos del dominio de Localidades.

Estructura normalizada para datos geográficos argentinos con integridad referencial.
Solo incluye Argentina ya que es el único país que manejamos actualmente.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.sujetos_epidemiologicos.ciudadanos_models.models import (
        AmbitosConcurrenciaEvento,
        CiudadanoDomicilio,
        ViajesCiudadano,
    )
    from app.domains.establecimientos.models import Establecimiento


class Provincia(BaseModel, table=True):
    """Provincias argentinas con código INDEC."""

    # TODO: Este lo agregué yo (ignacio), creo que da mas normalización y nos permitiria consultas mas interesantes

    __tablename__ = "provincia"

    # ID INDEC único e indexado (no primary key)
    id_provincia_indec: int = Field(
        unique=True, index=True, description="ID de provincia INDEC"
    )
    nombre: str = Field(
        max_length=150, index=True, description="Nombre de la provincia"
    )

    # Datos adicionales
    poblacion: Optional[int] = Field(
        None, description="Población total de la provincia"
    )
    superficie_km2: Optional[float] = Field(None, description="Superficie en km²")

    # Relaciones
    departamentos: List["Departamento"] = Relationship(back_populates="provincia")


class Departamento(BaseModel, table=True):
    """Departamentos/Partidos con código INDEC."""

    # TODO: Este lo agregué yo (ignacio), creo que da mas normalización y nos permitiria consultas mas interesantes

    __tablename__ = "departamento"

    # ID INDEC único e indexado (no primary key)
    id_departamento_indec: int = Field(
        unique=True, index=True, description="ID de departamento INDEC"
    )
    nombre: str = Field(
        max_length=150, index=True, description="Nombre del departamento"
    )
    id_provincia_indec: int = Field(
        foreign_key="provincia.id_provincia_indec", description="ID de la provincia"
    )

    # Datos específicos de salud
    region_sanitaria: Optional[str] = Field(
        None, max_length=150, description="Región sanitaria/Área programática"
    )

    # Datos adicionales
    poblacion: Optional[int] = Field(
        None, description="Población total del departamento"
    )
    superficie_km2: Optional[float] = Field(None, description="Superficie en km²")

    # Relaciones
    provincia: "Provincia" = Relationship(back_populates="departamentos")
    localidades: List["Localidad"] = Relationship(back_populates="departamento")


class Localidad(BaseModel, table=True):
    """Localidades argentinas con estructura normalizada."""

    __tablename__ = "localidad"

    # ID INDEC único e indexado (no primary key)
    id_localidad_indec: int = Field(
        sa_type=BigInteger, unique=True, index=True, description="ID de localidad INDEC"
    )
    nombre: str = Field(
        max_length=150, index=True, description="Nombre de la localidad"
    )
    id_departamento_indec: Optional[int] = Field(
        None,
        foreign_key="departamento.id_departamento_indec",
        description="ID del departamento (opcional para localidades de viaje)",
    )
    # TODO: El original tenia provincia indec, pero con esto lo podemos sacar a traves de un join con el  departamento

    # Datos adicionales
    # TODO: Agregado por ignacio
    poblacion: Optional[int] = Field(None, description="Población de la localidad")
    # TODO: Agregado por ignacio
    codigo_postal: Optional[str] = Field(
        None, max_length=10, description="Código postal"
    )
    # TODO: Agregado por ignacio
    latitud: Optional[float] = Field(None, description="Latitud geográfica")
    # TODO: Agregado por ignacio
    longitud: Optional[float] = Field(None, description="Longitud geográfica")

    # Relaciones
    departamento: Optional["Departamento"] = Relationship(back_populates="localidades")
    establecimientos: List["Establecimiento"] = Relationship(
        back_populates="localidad_establecimiento"
    )
    domicilios: List["CiudadanoDomicilio"] = Relationship(back_populates="localidad")
    viajes: List["ViajesCiudadano"] = Relationship(back_populates="localidad")
    ambitos_concurrencia: List["AmbitosConcurrenciaEvento"] = Relationship(
        back_populates="localidad"
    )
