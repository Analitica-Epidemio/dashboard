"""Modelos relacionados con aspectos de salud: síntomas, muestras, vacunas."""

from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.ciudadanos.models import CiudadanoComorbilidades
    from app.domains.establecimientos.models import Establecimiento
    from app.domains.eventos.models import Evento, DetalleEventoSintomas


class Determinacion(BaseModel, table=True):
    """
    Catálogo de determinaciones para estudios de laboratorio.
    
    Define las determinaciones/análisis que pueden realizarse
    en muestras biológicas durante eventos epidemiológicos.
    """

    __tablename__ = "determinacion"

    # Campos propios
    nombre: str = Field(..., max_length=200, description="Nombre de la determinación")
    codigo: Optional[str] = Field(
        None, max_length=50, unique=True, index=True, description="Código de la determinación"
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción de la determinación"
    )

    # Relaciones
    tecnicas: List["Tecnica"] = Relationship(back_populates="determinacion")


class Tecnica(BaseModel, table=True):
    """
    Catálogo de técnicas de laboratorio.
    
    Define las técnicas específicas que pueden utilizarse
    para realizar una determinación específica.
    """

    __tablename__ = "tecnica"

    # Campos propios
    nombre: str = Field(..., max_length=200, description="Nombre de la técnica")
    codigo: Optional[str] = Field(
        None, max_length=50, unique=True, index=True, description="Código de la técnica"
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción de la técnica"
    )

    # Foreign Keys
    id_determinacion: int = Field(
        foreign_key="determinacion.id", description="ID de la determinación"
    )

    # Relaciones
    determinacion: "Determinacion" = Relationship(back_populates="tecnicas")
    resultados_tecnica: List["ResultadoTecnica"] = Relationship(back_populates="tecnica")


class ResultadoTecnica(BaseModel, table=True):
    """
    Catálogo de resultados técnicos posibles.
    
    Define los posibles resultados que puede arrojar una técnica específica.
    """

    __tablename__ = "resultado_tecnica"

    # Campos propios
    nombre: str = Field(..., max_length=200, description="Nombre del resultado")
    codigo: Optional[str] = Field(
        None, max_length=50, unique=True, index=True, description="Código del resultado"
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del resultado"
    )
    es_positivo: Optional[bool] = Field(
        None, description="Indica si es un resultado positivo"
    )

    # Foreign Keys
    id_tecnica: int = Field(
        foreign_key="tecnica.id", description="ID de la técnica"
    )

    # Relaciones
    tecnica: "Tecnica" = Relationship(back_populates="resultados_tecnica")


class Sintoma(BaseModel, table=True):
    """
    Catálogo de síntomas y signos clínicos.

    Define los posibles síntomas y signos que pueden presentar los pacientes
    durante eventos epidemiológicos. Usa el ID del Sistema Nacional de
    Vigilancia en Salud (SNVS) como identificador único.
    """

    __tablename__ = "sintoma"
    __table_args__ = {"extend_existing": True}

    # ID SNVS único e indexado (no primary key)
    id_snvs_signo_sintoma: int = Field(
        unique=True, index=True, description="ID SNVS del síntoma"
    )

    # Campos propios
    signo_sintoma: Optional[str] = Field(
        None, max_length=150, description="Descripción del síntoma o signo"
    )

    # Relaciones
    detalle_eventos: List["DetalleEventoSintomas"] = Relationship(
        back_populates="sintoma"
    )


class Comorbilidad(BaseModel, table=True):
    """
    Catálogo de comorbilidades.

    Define las condiciones médicas preexistentes que pueden afectar
    el curso o severidad de eventos epidemiológicos.
    """

    __tablename__ = "comorbilidad"

    # Campos propios
    descripcion: Optional[str] = Field(
        None, max_length=150, description="Descripción de la comorbilidad"
    )

    # Relaciones
    ciudadanos_comorbilidades: List["CiudadanoComorbilidades"] = Relationship(
        back_populates="comorbilidad"
    )


class Muestra(BaseModel, table=True):
    """
    Catálogo de tipos de muestras biológicas.

    Define los tipos de muestras que pueden tomarse para análisis
    durante la investigación de eventos epidemiológicos.
    """

    __tablename__ = "muestra"

    # Campos propios
    descripcion: Optional[str] = Field(None, max_length=150, description="Descripción de muestra")

    # Relaciones
    muestras_eventos: List["MuestraEvento"] = Relationship(back_populates="muestra")


class Vacuna(BaseModel, table=True):
    """
    Catálogo de vacunas.

    Define las vacunas disponibles en el sistema de salud
    que pueden ser relevantes para eventos epidemiológicos.
    """

    __tablename__ = "vacuna"

    # Campos propios
    nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre de la vacuna"
    )

    # Relaciones
    vacunas_ciudadanos: List["VacunasCiudadano"] = Relationship(back_populates="vacuna")


class MuestraEvento(BaseModel, table=True):
    """
    Registro de muestras tomadas durante eventos epidemiológicos.

    Documenta las muestras biológicas recolectadas, incluyendo información
    sobre el establecimiento, fechas, pruebas realizadas y resultados obtenidos.
    Vincula muestras con eventos específicos de ciudadanos.
    """

    __tablename__ = "muestra_evento"

    # Campos propios
    fecha_toma_muestra: Optional[date] = Field(
        None, description="Fecha de toma de muestra"
    )
    semana_epidemiologica_muestra: Optional[int] = Field(
        None, description="Semana epidemiológica de la muestra"
    )
    anio_epidemiologico_muestra: Optional[int] = Field(
        None, description="Año epidemiológico de la muestra"
    )
    id_snvs_evento_muestra: Optional[int] = Field(
        None, 
        sa_type=BigInteger,
        description="ID SNVS del evento muestra"
    )
    id_snvs_prueba_muestra: Optional[int] = Field(
        None, 
        sa_type=BigInteger,
        description="ID SNVS de la prueba muestra"
    )
    # TODO: Campo "valor" - verificar dónde/cómo se usa según comentario original "DONDE?"
    valor: Optional[str] = Field(
        None, max_length=150, description="Valor del resultado"
    )
    id_snvs_usuario_interpretacion: Optional[int] = Field(
        None, description="ID del usuario que interpretó"
    )
    id_snvs_tipo_prueba: Optional[int] = Field(
        None, description="ID del tipo de prueba"
    )
    id_snvs_prueba: Optional[int] = Field(None, description="ID de la prueba")
    id_snvs_resultado: Optional[int] = Field(None, description="ID del resultado")
    fecha_papel: Optional[date] = Field(None, description="Fecha en papel")

    # Foreign Keys
    id_evento: int = Field(
        foreign_key="evento.id", description="ID del evento"
    )
    id_establecimiento: int = Field(
        foreign_key="establecimiento.id", description="ID del establecimiento"
    )
    id_muestra: int = Field(
        foreign_key="muestra.id", description="ID del tipo de muestra"
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="muestras")
    establecimiento: "Establecimiento" = Relationship(back_populates="muestras")
    muestra: "Muestra" = Relationship(back_populates="muestras_eventos")


class VacunasCiudadano(BaseModel, table=True):
    """
    Registro de vacunas aplicadas a ciudadanos.

    Documenta el historial de vacunación de ciudadanos en el contexto
    de eventos epidemiológicos, incluyendo tipo de vacuna, dosis y
    fecha de aplicación.
    """

    __tablename__ = "vacunas_ciudadano"

    # Campos propios
    dosis: Optional[str] = Field(
        None, max_length=150, description="Número o descripción de la dosis"
    )
    fecha_aplicacion: Optional[date] = Field(
        None, description="Fecha de aplicación de la vacuna"
    )

    # Foreign Keys
    id_evento: int = Field(
        foreign_key="evento.id", description="ID del evento"
    )
    id_vacuna: int = Field(foreign_key="vacuna.id", description="ID de la vacuna")

    # Relaciones
    evento: "Evento" = Relationship(back_populates="vacunas")
    vacuna: "Vacuna" = Relationship(back_populates="vacunas_ciudadanos")


