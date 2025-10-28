"""Modelos para capas GIS del Instituto Geográfico Nacional (IGN).

Almacena información geoespacial complementaria útil para análisis epidemiológico:
- Cursos de agua (vectores de enfermedades)
- Áreas urbanas (densidad poblacional)
"""

from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Column, Index
from sqlmodel import Field

from app.core.models import BaseModel


class CapaHidrografia(BaseModel, table=True):
    """
    Capa de cursos de agua de Argentina (IGN).

    Útil para análisis de enfermedades transmitidas por vectores
    que se reproducen en cuerpos de agua (dengue, zika, etc.).
    """

    __tablename__ = "capa_hidrografia"

    # Identificación
    nombre: Optional[str] = Field(
        None, max_length=200, description="Nombre del curso de agua"
    )
    tipo: Optional[str] = Field(
        None,
        max_length=50,
        description="Tipo: río, arroyo, canal, laguna, etc."
    )

    # Geometría - spatial_index=False para crear index explícito
    # Usa MULTILINESTRING porque los datos del IGN pueden tener múltiples segmentos
    geometria: Optional[str] = Field(
        default=None,
        sa_column=Column(Geometry("MULTILINESTRING", srid=4326, spatial_index=False)),
        description="Geometría del curso de agua (MultiLineString en WGS84)"
    )

    # Metadatos
    fuente: Optional[str] = Field(
        default="IGN", max_length=100, description="Fuente de los datos"
    )

    # Configuración de la tabla con índice espacial explícito
    __table_args__ = (
        Index("idx_capa_hidrografia_geometria", "geometria", postgresql_using="gist"),
        {"extend_existing": True},
    )


class CapaAreaUrbana(BaseModel, table=True):
    """
    Capa de áreas urbanas de Argentina (IGN).

    Útil para análisis de densidad poblacional y distribución
    de eventos epidemiológicos en zonas urbanas vs rurales.
    """

    __tablename__ = "capa_area_urbana"

    # Identificación
    nombre: Optional[str] = Field(
        None, max_length=200, description="Nombre del área urbana"
    )

    # Relación geográfica
    id_departamento_indec: Optional[int] = Field(
        None,
        description="Código INDEC del departamento al que pertenece"
    )
    id_departamento: Optional[int] = Field(
        None,
        foreign_key="departamento.id",
        description="ID del departamento (FK)"
    )

    # Datos poblacionales
    poblacion: Optional[int] = Field(
        None, description="Población estimada del área urbana"
    )

    # Geometría - spatial_index=False para crear index explícito
    # Usa MULTIPOLYGON porque los datos del IGN pueden tener múltiples polígonos
    geometria: Optional[str] = Field(
        default=None,
        sa_column=Column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False)),
        description="Geometría del área urbana (MultiPolygon en WGS84)"
    )

    # Metadatos
    fuente: Optional[str] = Field(
        default="IGN", max_length=100, description="Fuente de los datos"
    )

    # Configuración de la tabla con índice espacial explícito
    __table_args__ = (
        Index("idx_capa_area_urbana_geometria", "geometria", postgresql_using="gist"),
        {"extend_existing": True},
    )
