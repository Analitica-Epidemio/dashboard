"""
Modelos del dominio de Localidades.

Estructura normalizada para datos geográficos argentinos con integridad referencial.
Solo incluye Argentina ya que es el único país que manejamos actualmente.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, Numeric, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
        CiudadanoDomicilio,
    )
    from app.domains.sujetos_epidemiologicos.viajes_models import ViajesCiudadano
    from app.domains.eventos_epidemiologicos.ambitos_models import AmbitosConcurrenciaEvento
    from app.domains.eventos_epidemiologicos.eventos.models import Evento
    from app.domains.territorio.establecimientos_models import Establecimiento


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

    # Coordenadas del centroide (para visualización en mapa)
    latitud: Optional[float] = Field(None, description="Latitud del centroide geográfico")
    longitud: Optional[float] = Field(None, description="Longitud del centroide geográfico")

    # Relaciones
    departamentos: List["Departamento"] = Relationship(back_populates="provincia")


class Departamento(BaseModel, table=True):
    """Departamentos/Partidos con código INDEC."""

    # TODO: Este lo agregué yo (ignacio), creo que da mas normalización y nos permitiria consultas mas interesantes

    __tablename__ = "departamento"
    __table_args__ = (
        # Constraint UNIQUE compuesta: el código de departamento solo es único dentro de cada provincia
        # Ej: Buenos Aires (prov 6) y Chubut (prov 26) pueden tener ambas un departamento con código 7
        UniqueConstraint("id_provincia_indec", "id_departamento_indec", name="uq_departamento_provincia_departamento"),
        {"extend_existing": True},
    )

    # ID INDEC (NO único globalmente - solo dentro de cada provincia)
    id_departamento_indec: int = Field(
        index=True, description="ID de departamento INDEC (único por provincia)"
    )
    nombre: str = Field(
        max_length=150, index=True, description="Nombre del departamento"
    )
    id_provincia_indec: int = Field(
        foreign_key="provincia.id_provincia_indec",
        index=True,
        description="ID de la provincia"
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

    # Coordenadas del centroide (para visualización en mapa)
    latitud: Optional[float] = Field(None, description="Latitud del centroide geográfico")
    longitud: Optional[float] = Field(None, description="Longitud del centroide geográfico")

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
    # Código INDEC del departamento (para referencia y búsqueda)
    id_departamento_indec: Optional[int] = Field(
        None,
        index=True,
        description="Código INDEC del departamento (no es FK)",
    )
    # ID del departamento en la BD (foreign key real)
    id_departamento: Optional[int] = Field(
        None,
        foreign_key="departamento.id",
        description="ID interno del departamento (opcional para localidades de viaje)",
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
    domicilios_ciudadano: List["CiudadanoDomicilio"] = Relationship(back_populates="localidad")
    domicilios: List["Domicilio"] = Relationship(back_populates="localidad")
    viajes: List["ViajesCiudadano"] = Relationship(back_populates="localidad")
    ambitos_concurrencia: List["AmbitosConcurrenciaEvento"] = Relationship(
        back_populates="localidad"
    )


class Domicilio(BaseModel, table=True):
    """
    Domicilios geocodificados (INMUTABLES).

    Cada domicilio es un registro único e inmutable que representa una dirección física.
    - NO se modifica: si hay un error, se crea uno nuevo
    - Múltiples personas/eventos pueden apuntar al mismo domicilio
    - Un domicilio se geocodifica una sola vez
    - UNIQUE constraint evita duplicados

    Casos de uso:
    - Eventos apuntan al domicilio donde ocurrió el caso
    - Personas tienen historial temporal de domicilios (PersonaDomicilio)
    - Análisis de clusters (múltiples casos en mismo edificio)
    """

    __tablename__ = "domicilio"
    __table_args__ = (
        # UNIQUE constraint: misma dirección = mismo domicilio
        UniqueConstraint(
            "calle",
            "numero",
            "id_localidad_indec",
            name="uq_domicilio_direccion"
        ),
    )

    # Campos de dirección (solo los que existen en el CSV y tienen datos)
    calle: Optional[str] = Field(
        None,
        max_length=150,
        index=True,
        description="Nombre de la calle"
    )
    numero: Optional[str] = Field(
        None,
        max_length=10,
        description="Número de calle"
    )

    # Localidad (FK)
    id_localidad_indec: int = Field(
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        index=True,
        description="ID INDEC de la localidad"
    )

    # Coordenadas geográficas (geocodificadas)
    latitud: Optional[Decimal] = Field(
        None,
        sa_column=Column(Numeric(precision=10, scale=8)),
        description="Latitud GPS (geocodificada)"
    )
    longitud: Optional[Decimal] = Field(
        None,
        sa_column=Column(Numeric(precision=11, scale=8)),
        description="Longitud GPS (geocodificada)"
    )

    # Metadata de geocodificación
    geocodificado: bool = Field(
        default=False,
        description="Si ya fue geocodificado"
    )
    proveedor_geocoding: Optional[str] = Field(
        None,
        max_length=50,
        description="Proveedor usado (mapbox, google, etc.)"
    )
    confidence_geocoding: Optional[float] = Field(
        None,
        description="Score de confianza de la geocodificación (0-1)"
    )

    # Relaciones
    localidad: "Localidad" = Relationship(back_populates="domicilios")
    eventos: List["Evento"] = Relationship(back_populates="domicilio")
    # personas_historico: List["PersonaDomicilio"] = Relationship(back_populates="domicilio")
