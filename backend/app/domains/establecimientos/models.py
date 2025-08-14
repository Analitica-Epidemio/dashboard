"""Modelos de establecimientos de salud y su participación en eventos epidemiológicos."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.diagnosticos.models import DiagnosticoEvento
    from app.domains.eventos.models import CiudadanoEvento
    from app.domains.localidades.models import Localidad
    from app.domains.salud.models import MuestraEvento


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


class EstablecimientoEvento(BaseModel, table=True):
    """
    Registro de establecimientos que intervienen en eventos epidemiológicos.

    Documenta qué establecimientos, provincias, regiones sanitarias y localidades
    participaron en la atención, investigación o seguimiento de un evento epidemiológico.
    """

    __tablename__ = "establecimiento_evento"

    # Campos propios
    # TODO: Chequear con Luciano:
    # 1. Si podemos normalizar estos campos a tablas relacionales
    # 2. O usar JSON fields (SQLAlchemy soporta JSON nativo en PostgreSQL/MySQL)
    #    - Ventajas JSON: Consultas estructuradas, validación de schema, indexación parcial
    #    - Desventajas JSON: Menos portable entre DBs, requiere PostgreSQL 9.2+ o MySQL 5.7+
    # 3. El campo id_origen parece ser un FK a establecimiento pero está comentado por que entiendo que hay datos que no tenemos????
    id_origen: Optional[int] = Field(None, description="ID de origen")
    establecimientos_que_intervienen: Optional[str] = Field(
        None,
        max_length=150,
        description="Establecimientos que intervienen (IDs separados por comas)",
    )
    provincias_que_intervienen: Optional[str] = Field(
        None,
        max_length=150,
        description="Provincias que intervienen (IDs separados por comas)",
    )
    regiones_sanitarias_que_intervienen: Optional[str] = Field(
        None,
        max_length=150,
        description="Regiones sanitarias que intervienen (IDs separados por comas)",
    )
    departamentos_que_intervienen: Optional[str] = Field(
        None,
        max_length=150,
        description="Departamentos que intervienen (IDs separados por comas)",
    )
    localidades_que_intervienen: Optional[str] = Field(
        None,
        max_length=150,
        description="Localidades que intervienen (IDs separados por comas)",
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(
        back_populates="establecimientos"
    )
