"""Modelos para capas GIS del Instituto Geográfico Nacional (IGN).

Almacena información geoespacial complementaria útil para análisis epidemiológico:
- Cursos de agua (vectores de enfermedades)
- Áreas urbanas (densidad poblacional)
"""

from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger
from sqlmodel import Field

from app.core.models import BaseModel


class CapaHidrografia(BaseModel, table=True):
    """
    Capa de cursos de agua de Argentina (IGN).

    Útil para análisis de enfermedades transmitidas por vectores
    que se reproducen en cuerpos de agua (dengue, zika, etc.).
    """

    __tablename__ = "capa_hidrografia"
    __table_args__ = {"extend_existing": True}

    # Identificación
    nombre: Optional[str] = Field(
        None, max_length=200, description="Nombre del curso de agua"
    )
    tipo: Optional[str] = Field(
        None,
        max_length=50,
        description="Tipo: río, arroyo, canal, laguna, etc."
    )

    # Geometría
    geometria: Optional[str] = Field(
        None,
        sa_column_kwargs={"type_": Geometry("LINESTRING", srid=4326)},
        description="Geometría del curso de agua (LineString en WGS84)"
    )

    # Metadatos
    fuente: Optional[str] = Field(
        None, max_length=100, default="IGN", description="Fuente de los datos"
    )


class CapaAreaUrbana(BaseModel, table=True):
    """
    Capa de áreas urbanas de Argentina (IGN).

    Útil para análisis de densidad poblacional y distribución
    de eventos epidemiológicos en zonas urbanas vs rurales.
    """

    __tablename__ = "capa_area_urbana"
    __table_args__ = {"extend_existing": True}

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

    # Geometría
    geometria: Optional[str] = Field(
        None,
        sa_column_kwargs={"type_": Geometry("POLYGON", srid=4326)},
        description="Geometría del área urbana (Polygon en WGS84)"
    )

    # Metadatos
    fuente: Optional[str] = Field(
        None, max_length=100, default="IGN", description="Fuente de los datos"
    )
