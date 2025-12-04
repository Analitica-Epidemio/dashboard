"""Modelos relacionados con diagnósticos, internaciones y tratamientos."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.atencion_medica.salud_models import MuestraEvento
    from app.domains.eventos_epidemiologicos.eventos.models import Evento
    from app.domains.territorio.establecimientos_models import Establecimiento


class DiagnosticoEvento(BaseModel, table=True):
    """
    Diagnósticos de eventos epidemiológicos.

    Almacena información sobre los diagnósticos realizados a ciudadanos
    durante eventos epidemiológicos, incluyendo clasificaciones manuales
    y automáticas, validaciones y referencias a establecimientos.
    """

    __tablename__ = "diagnostico_evento"
    __table_args__ = (
        UniqueConstraint('id_evento', name='uq_diagnostico_evento'),
        {"extend_existing": True}
    )

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
    # Agregado por Ignacio - Campo faltante del CSV epidemiológico
    validacion: Optional[str] = Field(
        None,
        max_length=500,
        description="Estado de validación del diagnóstico (usar 'Sin validar' si no se especifica)",
    )
    edad_diagnostico: Optional[int] = Field(
        None, description="Edad al momento del diagnóstico"
    )
    grupo_etario: Optional[str] = Field(
        None, max_length=150, description="Grupo etario"
    )
    # Agregado por Ignacio - Campos faltantes del CSV epidemiológico
    diagnostico_referido: Optional[str] = Field(
        None,
        max_length=150,
        description="Diagnóstico referido (usar 'No especificado' si no se conoce)",
    )
    fecha_diagnostico_referido: Optional[date] = Field(
        None, description="Fecha del diagnóstico referido"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    # Corregido por Ignacio - FK estaba mal mapeado a establecimiento
    id_establecimiento_diagnostico: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se realizó el diagnóstico",
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="diagnosticos")
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
    __table_args__ = (
        UniqueConstraint('id_evento', name='uq_internacion_evento'),
        {"extend_existing": True}
    )

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
    # Nota Ignacio - Este campo ya mapea ESTABLECIMIENTO_INTERNACION del CSV
    establecimiento_internacion: Optional[str] = Field(
        None,
        max_length=150,
        description="Establecimiento de internación (usar 'Desconocido' si no se especifica)",
    )
    fecha_alta_medica: Optional[date] = Field(None, description="Fecha de alta médica")
    es_fallecido: Optional[bool] = Field(None, description="Falleció")
    fecha_fallecimiento: Optional[date] = Field(
        None, description="Fecha de fallecimiento"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")

    # Relaciones
    evento: "Evento" = Relationship(back_populates="internaciones")


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
    id_muestra: int = Field(
        foreign_key="muestra_evento.id", description="ID de la muestra"
    )

    # Relaciones
    muestra_evento: "MuestraEvento" = Relationship(back_populates="estudios")


class TratamientoEvento(BaseModel, table=True):
    """
    Tratamientos médicos aplicados durante eventos epidemiológicos.

    Documenta los tratamientos administrados a pacientes, incluyendo
    establecimientos, duración y resultados del tratamiento.
    """

    __tablename__ = "tratamiento_evento"
    __table_args__ = (
        UniqueConstraint('id_evento', 'descripcion_tratamiento', 'fecha_inicio_tratamiento',
                        name='uq_tratamiento_evento'),
        {"extend_existing": True}
    )

    # Campos propios
    # TODO: Chequear con Luciano si estab_tto debería ser el FK directamente
    # o mantener ambos campos (texto libre + FK opcional)
    # NO TENER, ya que son campos libres, bah, doble-chequear
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
    resultado_tratamiento: Optional[str] = Field(
        None, description="Resultado del tratamiento"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    id_establecimiento_tratamiento: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se realizó el tratamiento",
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="tratamientos")
    establecimiento: Optional["Establecimiento"] = Relationship()
