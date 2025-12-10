"""
Catálogos y registros de salud para vigilancia nominal.

Incluye:
- Catálogos: Sintoma, Comorbilidad, Vacuna, Muestra, Determinacion, Tecnica
- Registros: MuestraCasoEpidemiologico, VacunasCiudadano, EstudioCasoEpidemiologico

Estos modelos están ligados a casos de vigilancia nominal.
"""

from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.vigilancia_nominal.models.caso import (
        CasoEpidemiologico,
        DetalleCasoSintomas,
    )
    from app.domains.vigilancia_nominal.models.sujetos import (
        Ciudadano,
        CiudadanoComorbilidades,
    )


# =============================================================================
# CATÁLOGOS
# =============================================================================


class Determinacion(BaseModel, table=True):
    """
    Catálogo de determinaciones para estudios de laboratorio.

    Define las determinaciones/análisis que pueden realizarse
    en muestras biológicas durante casos epidemiológicos.
    """

    __tablename__ = "determinacion"

    nombre: str = Field(..., max_length=200, description="Nombre de la determinación")
    codigo: Optional[str] = Field(
        None,
        max_length=255,
        unique=True,
        index=True,
        description="Código de la determinación",
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción de la determinación"
    )

    # Relaciones
    tecnicas: Mapped[List["Tecnica"]] = Relationship(back_populates="determinacion")


class Tecnica(BaseModel, table=True):
    """
    Catálogo de técnicas de laboratorio.

    Define las técnicas específicas que pueden utilizarse
    para realizar una determinación.
    """

    __tablename__ = "tecnica"

    nombre: str = Field(..., max_length=200, description="Nombre de la técnica")
    codigo: Optional[str] = Field(
        None,
        max_length=255,
        unique=True,
        index=True,
        description="Código de la técnica",
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción de la técnica"
    )

    # Foreign Keys
    id_determinacion: int = Field(
        foreign_key="determinacion.id", description="ID de la determinación"
    )

    # Relaciones
    determinacion: Mapped["Determinacion"] = Relationship(back_populates="tecnicas")
    resultados_tecnica: Mapped[List["ResultadoTecnica"]] = Relationship(
        back_populates="tecnica"
    )


class ResultadoTecnica(BaseModel, table=True):
    """
    Catálogo de resultados técnicos posibles.

    Define los posibles resultados que puede arrojar una técnica.
    """

    __tablename__ = "resultado_tecnica"

    nombre: str = Field(..., max_length=200, description="Nombre del resultado")
    codigo: Optional[str] = Field(
        None,
        max_length=255,
        unique=True,
        index=True,
        description="Código del resultado",
    )
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del resultado"
    )
    es_positivo: Optional[bool] = Field(
        None, description="Indica si es un resultado positivo"
    )

    # Foreign Keys
    id_tecnica: int = Field(foreign_key="tecnica.id", description="ID de la técnica")

    # Relaciones
    tecnica: Mapped["Tecnica"] = Relationship(back_populates="resultados_tecnica")


class Sintoma(BaseModel, table=True):
    """
    Catálogo de síntomas y signos clínicos.

    Define los posibles síntomas que pueden presentar los pacientes.
    """

    __tablename__ = "sintoma"
    __table_args__ = {"extend_existing": True}

    id_snvs_signo_sintoma: int = Field(
        unique=True, index=True, description="ID SNVS del síntoma"
    )
    signo_sintoma: Optional[str] = Field(
        None, max_length=150, description="Descripción del síntoma o signo"
    )

    # Relaciones
    detalle_casos: Mapped[List["DetalleCasoSintomas"]] = Relationship(
        back_populates="sintoma"
    )


class Comorbilidad(BaseModel, table=True):
    """
    Catálogo de comorbilidades.

    Define las condiciones médicas preexistentes que pueden afectar
    el curso o severidad de casos epidemiológicos.
    """

    __tablename__ = "comorbilidad"
    __table_args__ = (
        UniqueConstraint("descripcion", name="uq_comorbilidad_descripcion"),
    )

    descripcion: Optional[str] = Field(
        None, max_length=150, description="Descripción de la comorbilidad"
    )

    # Relaciones
    ciudadanos_comorbilidades: Mapped[List["CiudadanoComorbilidades"]] = Relationship(
        back_populates="comorbilidad"
    )


class Muestra(BaseModel, table=True):
    """
    Catálogo de tipos de muestras biológicas.

    Define los tipos de muestras que pueden tomarse para análisis.
    """

    __tablename__ = "muestra"
    __table_args__ = (UniqueConstraint("descripcion", name="uq_muestra_descripcion"),)

    descripcion: Optional[str] = Field(
        None, max_length=150, description="Descripción de muestra"
    )

    # Relaciones
    muestras_casos: Mapped[List["MuestraCasoEpidemiologico"]] = Relationship(
        back_populates="muestra"
    )


class Vacuna(BaseModel, table=True):
    """
    Catálogo de vacunas.

    Define las vacunas disponibles en el sistema de salud.
    """

    __tablename__ = "vacuna"
    __table_args__ = (UniqueConstraint("nombre", name="uq_vacuna_nombre"),)

    nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre de la vacuna"
    )

    # Relaciones
    vacunas_ciudadanos: Mapped[List["VacunasCiudadano"]] = Relationship(
        back_populates="vacuna"
    )


# =============================================================================
# REGISTROS DE MUESTRAS Y ESTUDIOS
# =============================================================================


class MuestraCasoEpidemiologico(BaseModel, table=True):
    """
    Registro de muestras tomadas durante casos epidemiológicos.

    Documenta las muestras biológicas recolectadas, fechas,
    pruebas realizadas y resultados obtenidos.
    """

    __tablename__ = "muestra_caso_epidemiologico"
    __table_args__ = (
        UniqueConstraint("id_snvs_muestra", "id_caso", name="uq_muestra_caso"),
    )

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
    id_snvs_caso_muestra: Optional[int] = Field(
        None, sa_type=BigInteger, description="ID SNVS del caso muestra"
    )
    id_snvs_prueba_muestra: Optional[int] = Field(
        None, sa_type=BigInteger, description="ID SNVS de la prueba muestra"
    )
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
    id_snvs_muestra: Optional[int] = Field(
        None, sa_type=BigInteger, index=True, description="ID SNVS de la muestra"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )
    id_establecimiento: int = Field(
        foreign_key="establecimiento.id", description="ID del establecimiento"
    )
    id_muestra: int = Field(
        foreign_key="muestra.id", description="ID del tipo de muestra"
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="muestras")
    establecimiento: Mapped["Establecimiento"] = Relationship(back_populates="muestras")
    muestra: Mapped["Muestra"] = Relationship(back_populates="muestras_casos")
    estudios: Mapped[List["EstudioCasoEpidemiologico"]] = Relationship(
        back_populates="muestra_caso"
    )


class EstudioCasoEpidemiologico(BaseModel, table=True):
    """
    Estudios y análisis clínicos realizados sobre muestras.

    Registra estudios de laboratorio, determinaciones, técnicas
    y resultados obtenidos.
    """

    __tablename__ = "estudio_caso_epidemiologico"
    __table_args__ = {"extend_existing": True}

    fecha_estudio: Optional[date] = Field(None, description="Fecha del estudio")
    determinacion: Optional[str] = Field(
        None, max_length=150, description="Determinación realizada"
    )
    tecnica: Optional[str] = Field(
        None, max_length=150, description="Técnica utilizada"
    )
    resultado: Optional[str] = Field(
        None, max_length=150, description="Resultado del estudio"
    )
    fecha_recepcion: Optional[date] = Field(None, description="Fecha de recepción")

    # Foreign Keys
    id_muestra: int = Field(
        foreign_key="muestra_caso_epidemiologico.id", description="ID de la muestra"
    )

    # Relaciones
    muestra_caso: Mapped["MuestraCasoEpidemiologico"] = Relationship(
        back_populates="estudios"
    )


class VacunasCiudadano(BaseModel, table=True):
    """
    Registro de vacunas aplicadas a ciudadanos.

    Documenta el historial de vacunación en el contexto
    de casos epidemiológicos.
    """

    __tablename__ = "vacunas_ciudadano"
    __table_args__ = (
        UniqueConstraint(
            "codigo_ciudadano",
            "id_vacuna",
            "fecha_aplicacion",
            "dosis",
            name="uq_vacuna_ciudadano",
        ),
    )

    dosis: Optional[str] = Field(
        None, max_length=150, description="Número o descripción de la dosis"
    )
    fecha_aplicacion: Optional[date] = Field(
        None, description="Fecha de aplicación de la vacuna"
    )

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_vacuna: int = Field(foreign_key="vacuna.id", description="ID de la vacuna")
    id_caso: Optional[int] = Field(
        None, foreign_key="caso_epidemiologico.id", description="ID del caso (opcional)"
    )

    # Relaciones
    ciudadano: Mapped["Ciudadano"] = Relationship(back_populates="vacunas")
    vacuna: Mapped["Vacuna"] = Relationship(back_populates="vacunas_ciudadanos")
    caso: Mapped[Optional["CasoEpidemiologico"]] = Relationship(
        back_populates="vacunas"
    )
