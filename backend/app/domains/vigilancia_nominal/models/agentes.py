"""
Modelos para detección de Agentes en casos de vigilancia nominal.

El catálogo de AgenteEtiologico está en app.domains.catalogos.agentes/
Aquí solo están los modelos de detección/extracción:
- CasoAgente: Relación N:M entre caso y agente (qué agentes se detectaron)
- AgenteExtraccionConfig: Configuración de extracción desde CSV
- ResultadoDeteccion: Enum de estados posibles
"""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Column, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.catalogos.agentes.models import AgenteEtiologico
    from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad
    from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico


class AgenteExtraccionConfig(BaseModel, table=True):
    """
    Configuración de extracción de agentes desde el CSV.

    Define CÓMO detectar un agente específico en un tipo de ENO,
    incluyendo qué campos buscar y qué valores indican positivo.

    Ejemplo para VSR en UC-IRAG:
    - campo_busqueda: "DETERMINACION"
    - patron_busqueda: "VSR|Sincicial"
    - campo_resultado: "RESULTADO"
    - valores_positivos: ["Positivo", "Detectable"]
    """

    __tablename__ = "agente_extraccion_config"
    __table_args__ = (
        UniqueConstraint(
            "id_agente", "id_enfermedad", "campo_busqueda",
            name="uq_agente_enfermedad_campo"
        ),
        Index("idx_config_agente", "id_agente"),
        Index("idx_config_enfermedad", "id_enfermedad"),
        Index("idx_config_activo", "activo"),
    )

    # FKs
    id_agente: int = Field(
        foreign_key="agente_etiologico.id",
        description="ID del agente a extraer"
    )
    id_enfermedad: int = Field(
        foreign_key="enfermedad.id",
        description="ID de la enfermedad donde buscar este agente"
    )

    # Configuración de búsqueda
    campo_busqueda: str = Field(
        max_length=100,
        description="Campo del CSV donde buscar (ej: 'DETERMINACION')"
    )
    patron_busqueda: str = Field(
        max_length=500,
        description="Patrón regex o texto para buscar (ej: 'VSR|Sincicial')"
    )
    es_regex: bool = Field(
        default=True,
        description="Si patron_busqueda es regex (True) o texto exacto (False)"
    )
    case_sensitive: bool = Field(
        default=False,
        description="Si la búsqueda es sensible a mayúsculas/minúsculas"
    )

    # Configuración de resultado
    campo_resultado: Optional[str] = Field(
        None,
        max_length=100,
        description="Campo donde verificar resultado positivo. NULL si no aplica."
    )
    valores_positivos: Optional[List[str]] = Field(
        None,
        sa_column=Column(JSON),
        description="Valores que indican resultado positivo"
    )

    # Método de detección
    metodo_deteccion_default: Optional[str] = Field(
        None,
        max_length=100,
        description="Método de detección por defecto (ej: 'PCR', 'cultivo')"
    )

    # Prioridad y estado
    prioridad: int = Field(
        default=100,
        description="Prioridad de evaluación (menor = más prioritario)"
    )
    activo: bool = Field(
        default=True,
        index=True,
        description="Si esta config está activa"
    )

    notas: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Notas sobre esta configuración"
    )

    # Relaciones
    agente: "AgenteEtiologico" = Relationship()
    enfermedad: "Enfermedad" = Relationship()
    casos_extraidos: List["CasoAgente"] = Relationship(
        back_populates="config_usada",
        sa_relationship_kwargs={"foreign_keys": "[CasoAgente.id_config_usada]"}
    )


class ResultadoDeteccion(str, Enum):
    """Estados posibles de detección de un agente."""
    POSITIVO = "POSITIVO"
    NEGATIVO = "NEGATIVO"
    INDETERMINADO = "INDETERMINADO"
    NO_REALIZADO = "NO_REALIZADO"


class CasoAgente(BaseModel, table=True):
    """
    Relación N:M entre CasoEpidemiologico y AgenteEtiologico.

    Registra qué agentes fueron buscados/detectados en cada caso,
    incluyendo tanto positivos como negativos.

    Soporta coinfecciones: un caso puede tener múltiples agentes positivos.
    """

    __tablename__ = "caso_agente"
    __table_args__ = (
        UniqueConstraint("id_caso", "id_agente", name="uq_caso_agente"),
        Index("idx_caso_agente_caso", "id_caso"),
        Index("idx_caso_agente_agente", "id_agente"),
        Index("idx_caso_agente_fecha", "fecha_deteccion"),
        Index("idx_caso_agente_resultado", "resultado"),
    )

    # FKs principales
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id",
        description="ID del caso epidemiológico"
    )
    id_agente: int = Field(
        foreign_key="agente_etiologico.id",
        description="ID del agente buscado/detectado"
    )

    # Resultado de la detección
    resultado: ResultadoDeteccion = Field(
        default=ResultadoDeteccion.POSITIVO,
        index=True,
        description="Resultado: positivo, negativo, indeterminado, no_realizado"
    )

    # Metadata de la detección
    metodo_deteccion: Optional[str] = Field(
        None,
        max_length=100,
        description="Método de detección usado (ej: 'PCR', 'cultivo')"
    )
    resultado_raw: Optional[str] = Field(
        None,
        max_length=200,
        description="Valor original del resultado"
    )
    fecha_deteccion: Optional[date] = Field(
        None,
        index=True,
        description="Fecha de la detección/resultado"
    )

    # Trazabilidad
    id_config_usada: Optional[int] = Field(
        None,
        foreign_key="agente_extraccion_config.id",
        description="Config que extrajo este agente"
    )
    campo_origen: Optional[str] = Field(
        None,
        max_length=100,
        description="Campo del CSV de donde se extrajo"
    )
    valor_origen: Optional[str] = Field(
        None,
        max_length=500,
        description="Valor original del campo que matcheó"
    )

    # Relaciones
    caso: "CasoEpidemiologico" = Relationship(
        back_populates="agentes_detectados",
        sa_relationship_kwargs={"foreign_keys": "caso_agente.c.id_caso"}
    )
    agente: "AgenteEtiologico" = Relationship()
    config_usada: Optional["AgenteExtraccionConfig"] = Relationship(
        back_populates="casos_extraidos",
        sa_relationship_kwargs={"foreign_keys": "caso_agente.c.id_config_usada"}
    )
