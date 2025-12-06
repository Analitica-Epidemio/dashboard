"""
Modelos del dominio de Localidades.

Estructura normalizada para datos geográficos argentinos con integridad referencial.
Solo incluye Argentina ya que es el único país que manejamos actualmente.
"""

import enum
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Column, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.models import BaseModel


class EstadoGeocodificacion(str, enum.Enum):
    """
    Estado del proceso de geocodificación de un domicilio.

    PENDIENTE: Domicilio recién creado, aún no procesado
    EN_COLA: Marcado para geocodificación, esperando procesamiento
    PROCESANDO: Actualmente siendo geocodificado por un worker
    GEOCODIFICADO: Geocodificación exitosa, tiene coordenadas válidas
    FALLO_TEMPORAL: Error temporal (rate limit, timeout), reintentar más tarde
    FALLO_PERMANENTE: Error permanente (dirección inválida, sin resultados), no reintentar
    NO_GEOCODIFICABLE: Datos insuficientes para geocodificar (ej: solo número sin calle)
    DESHABILITADO: Geocodificación deshabilitada en settings
    """

    PENDIENTE = "PENDIENTE"
    EN_COLA = "EN_COLA"
    PROCESANDO = "PROCESANDO"
    GEOCODIFICADO = "GEOCODIFICADO"
    FALLO_TEMPORAL = "FALLO_TEMPORAL"
    FALLO_PERMANENTE = "FALLO_PERMANENTE"
    NO_GEOCODIFICABLE = "NO_GEOCODIFICABLE"
    DESHABILITADO = "DESHABILITADO"


if TYPE_CHECKING:
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.vigilancia_nominal.models.ambitos import (
        AmbitosConcurrenciaCaso,
    )
    from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
    from app.domains.vigilancia_nominal.models.sujetos import ViajesCiudadano


class Provincia(BaseModel, table=True):
    """Provincias argentinas con código INDEC."""

    __tablename__ = "provincia"
    __table_args__ = (
        Index("idx_provincia_geometria", "geometria", postgresql_using="gist"),
        {"extend_existing": True},
    )

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
    latitud: Optional[float] = Field(
        None, description="Latitud del centroide geográfico"
    )
    longitud: Optional[float] = Field(
        None, description="Longitud del centroide geográfico"
    )

    # Geometría para mapa coroplético (polígono de la provincia)
    geometria: Optional[str] = Field(
        default=None,
        sa_column=Column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False)),
        description="Geometría de la provincia (MultiPolygon en WGS84)",
    )

    # Metadatos de la fuente
    fuente_geometria: Optional[str] = Field(
        None, max_length=100, description="Fuente de la geometría (IGN, Georef, etc.)"
    )

    # Relaciones
    departamentos: Mapped[List["Departamento"]] = Relationship(
        back_populates="provincia"
    )


class Departamento(BaseModel, table=True):
    """Departamentos/Partidos con código INDEC."""

    __tablename__ = "departamento"
    __table_args__ = (
        # Constraint UNIQUE compuesta: el código de departamento solo es único dentro de cada provincia
        # Ej: Buenos Aires (prov 6) y Chubut (prov 26) pueden tener ambas un departamento con código 7
        UniqueConstraint(
            "id_provincia_indec",
            "id_departamento_indec",
            name="uq_departamento_provincia_departamento",
        ),
        Index("idx_departamento_geometria", "geometria", postgresql_using="gist"),
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
        description="ID de la provincia",
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
    latitud: Optional[float] = Field(
        None, description="Latitud del centroide geográfico"
    )
    longitud: Optional[float] = Field(
        None, description="Longitud del centroide geográfico"
    )

    # Geometría para mapa coroplético (polígono del departamento)
    geometria: Optional[str] = Field(
        default=None,
        sa_column=Column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False)),
        description="Geometría del departamento (MultiPolygon en WGS84)",
    )

    # Metadatos de la fuente
    fuente_geometria: Optional[str] = Field(
        None, max_length=100, description="Fuente de la geometría (IGN, Georef, etc.)"
    )

    # Relaciones
    provincia: Mapped["Provincia"] = Relationship(back_populates="departamentos")


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
    # Código INDEC del departamento (para JOINs con tabla departamento)
    id_departamento_indec: Optional[int] = Field(
        None,
        index=True,
        description="Código INDEC del departamento",
    )

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
    establecimientos: Mapped[List["Establecimiento"]] = Relationship(
        back_populates="localidad_establecimiento"
    )
    # Nota: CiudadanoDomicilio no tiene FK a Localidad, la relación es indirecta via Domicilio
    domicilios: Mapped[List["Domicilio"]] = Relationship(back_populates="localidad")
    viajes: Mapped[List["ViajesCiudadano"]] = Relationship(back_populates="localidad")
    ambitos_concurrencia: Mapped[List["AmbitosConcurrenciaCaso"]] = Relationship(
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
    - CasoEpidemiologicos apuntan al domicilio donde ocurrió el caso
    - Personas tienen historial temporal de domicilios (PersonaDomicilio)
    - Análisis de clusters (múltiples casos en mismo edificio)
    """

    __tablename__ = "domicilio"
    __table_args__ = (
        # UNIQUE constraint: misma dirección = mismo domicilio
        UniqueConstraint(
            "calle", "numero", "id_localidad_indec", name="uq_domicilio_direccion"
        ),
    )

    # Campos de dirección (solo los que existen en el CSV y tienen datos)
    calle: Optional[str] = Field(
        None, max_length=150, index=True, description="Nombre de la calle"
    )
    numero: Optional[str] = Field(None, max_length=10, description="Número de calle")

    # Localidad (FK)
    id_localidad_indec: int = Field(
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        index=True,
        description="ID INDEC de la localidad",
    )

    # Coordenadas geográficas (geocodificadas)
    latitud: Optional[Decimal] = Field(
        None,
        sa_column=Column(Numeric(precision=10, scale=8)),
        description="Latitud GPS (geocodificada)",
    )
    longitud: Optional[Decimal] = Field(
        None,
        sa_column=Column(Numeric(precision=11, scale=8)),
        description="Longitud GPS (geocodificada)",
    )

    # Metadata de geocodificación
    estado_geocodificacion: EstadoGeocodificacion = Field(
        default=EstadoGeocodificacion.PENDIENTE,
        description="Estado del proceso de geocodificación",
    )
    proveedor_geocoding: Optional[str] = Field(
        None, max_length=50, description="Proveedor usado (mapbox, google, etc.)"
    )
    confidence_geocoding: Optional[float] = Field(
        None, description="Score de confianza de la geocodificación (0-1)"
    )
    intentos_geocodificacion: int = Field(
        default=0, description="Número de intentos de geocodificación realizados"
    )
    ultimo_error_geocodificacion: Optional[str] = Field(
        None,
        max_length=500,
        description="Último mensaje de error si falló la geocodificación",
    )

    # Relaciones
    localidad: Mapped["Localidad"] = Relationship(back_populates="domicilios")
    casos: Mapped[List["CasoEpidemiologico"]] = Relationship(back_populates="domicilio")
    # personas_historico: Mapped[List["PersonaDomicilio"]] = Relationship(back_populates="domicilio")
