"""Modelos relacionados con diagnósticos, internaciones y tratamientos."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.core.shared.enums import ResultadoTratamiento

if TYPE_CHECKING:
    from app.domains.establecimientos.models import Establecimiento
    from app.domains.eventos.models import CiudadanoEvento


class DiagnosticoEvento(BaseModel, table=True):
    """
    Diagnósticos de eventos epidemiológicos.

    Almacena información sobre los diagnósticos realizados a ciudadanos
    durante eventos epidemiológicos, incluyendo clasificaciones manuales
    y automáticas, validaciones y referencias a establecimientos.
    """

    __tablename__ = "diagnostico_evento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    clasificacion_manual: str = Field(
        ..., max_length=150, description="Clasificación manual del diagnóstico"
    )
    clasificacion_automatica: Optional[str] = Field(
        None, max_length=150, description="Clasificación automática"
    )
    clasificacion_algoritmo: Optional[str] = Field(
        None, max_length=150, description="Algoritmo de clasificación"
    )
    validacion: Optional[str] = Field(
        None, max_length=150, description="Estado de validación"
    )
    edad_diagnostico: Optional[int] = Field(
        None, description="Edad al momento del diagnóstico"
    )
    grupo_etario: Optional[str] = Field(
        None, max_length=150, description="Grupo etario"
    )
    diagnostico_referido: Optional[str] = Field(
        None, max_length=150, description="Diagnóstico referido"
    )
    fecha_diagnostico_referido: Optional[date] = Field(
        None, description="Fecha del diagnóstico referido"
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )
    id_diagnostico: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento de diagnóstico",
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="diagnosticos")
    establecimiento: Optional["Establecimiento"] = Relationship(
        back_populates="diagnosticos"
    )


class InternacionEvento(BaseModel, table=True):
    """
    Registro de internaciones hospitalarias durante eventos epidemiológicos.

    Rastrea el estado de internación de pacientes, incluyendo fechas,
    cuidados intensivos, altas médicas y fallecimientos.
    """

    __tablename__ = "internacion_evento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    fue_internado: Optional[bool] = Field(None, description="Fue internado")
    fue_curado: Optional[bool] = Field(None, description="Fue curado")
    requirio_cuidado_intensivo: Optional[bool] = Field(
        None, description="Requirió cuidado intensivo"
    )
    fecha_internacion: Optional[date] = Field(None, description="Fecha de internación")
    fecha_cuidados_intensivos: Optional[date] = Field(
        None, description="Fecha de ingreso a cuidados intensivos"
    )
    establecimiento_internacion: Optional[str] = Field(
        None, max_length=150, description="Establecimiento de internación"
    )
    fecha_alta_medica: Optional[date] = Field(None, description="Fecha de alta médica")
    es_fallecido: Optional[bool] = Field(None, description="Falleció")
    fecha_fallecimiento: Optional[date] = Field(
        None, description="Fecha de fallecimiento"
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="internaciones")


class EstudioEvento(BaseModel, table=True):
    """
    Estudios y análisis clínicos realizados durante eventos epidemiológicos.

    Registra estudios de laboratorio, determinaciones, técnicas utilizadas
    y resultados obtenidos para el diagnóstico y seguimiento de casos.
    """

    __tablename__ = "estudio_evento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
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
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="estudios")


class TratamientoEvento(BaseModel, table=True):
    """
    Tratamientos médicos aplicados durante eventos epidemiológicos.

    Documenta los tratamientos administrados a pacientes, incluyendo
    establecimientos, duración y resultados del tratamiento.
    """

    __tablename__ = "tratamiento_evento"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    # TODO: Chequear con Luciano si estab_tto debería ser el FK directamente
    # o mantener ambos campos (texto libre + FK opcional)
    establecimiento_tratamiento: Optional[str] = Field(
        None, max_length=150, description="Establecimiento de tratamiento (texto libre)"
    )
    descripcion_tratamiento: Optional[str] = Field(
        None, max_length=150, description="Descripción del tratamiento"
    )
    fecha_inicio_tratamiento: Optional[date] = Field(
        None, description="Fecha de inicio del tratamiento"
    )
    fecha_fin_tratamiento: Optional[date] = Field(
        None, description="Fecha de fin del tratamiento"
    )
    resultado_tratamiento: Optional[ResultadoTratamiento] = Field(
        None, description="Resultado del tratamiento"
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )
    id_establecimiento_tratamiento: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se realizó el tratamiento",
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="tratamientos")
    establecimiento: Optional["Establecimiento"] = Relationship()
