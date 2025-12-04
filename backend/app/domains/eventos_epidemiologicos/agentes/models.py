"""
Modelos para Agentes Etiológicos.

Los agentes etiológicos son patógenos (virus, bacterias, parásitos) que causan
enfermedades y pueden detectarse en múltiples tipos de eventos epidemiológicos.

Ejemplo:
- VSR puede detectarse en UC-IRAG y en Sospecha de virus emergente
- STEC O157 puede detectarse en SUH, Diarrea aguda y Brote ETA

Este modelo permite:
1. Catálogo centralizado de agentes
2. Configuración flexible de cómo extraer cada agente del CSV
3. Relación N:M entre eventos y agentes (soporta coinfecciones)
4. Queries por agente independiente del tipo de evento
"""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Column, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.eventos_epidemiologicos.eventos.models import Evento, TipoEno


class CategoriaAgente:
    """Categorías de agentes etiológicos"""
    VIRUS = "virus"
    BACTERIA = "bacteria"
    PARASITO = "parasito"
    HONGO = "hongo"
    PRION = "prion"
    OTRO = "otro"


class GrupoAgente:
    """Grupos funcionales de agentes (para filtrado en gráficos)"""
    RESPIRATORIO = "respiratorio"
    ENTERICO = "enterico"
    VECTORIAL = "vectorial"
    ZOONOTICO = "zoonotico"
    TRANSMISION_SEXUAL = "transmision_sexual"
    OTRO = "otro"


class AgenteEtiologico(BaseModel, table=True):
    """
    Catálogo de agentes etiológicos (patógenos).

    Representa virus, bacterias, parásitos y otros agentes causantes
    de enfermedades que se detectan en el laboratorio.

    Ejemplos:
    - VSR (Virus Sincicial Respiratorio)
    - Influenza A
    - STEC O157
    - Salmonella spp.
    - Rotavirus
    """

    __tablename__ = "agente_etiologico"
    __table_args__ = (
        Index("idx_agente_categoria", "categoria"),
        Index("idx_agente_grupo", "grupo"),
        Index("idx_agente_activo", "activo"),
    )

    # Identificación
    codigo: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Código único kebab-case (ej: 'vsr', 'stec-o157', 'influenza-a')"
    )
    nombre: str = Field(
        max_length=200,
        description="Nombre completo (ej: 'Virus Sincicial Respiratorio')"
    )
    nombre_corto: str = Field(
        max_length=50,
        description="Nombre corto para gráficos (ej: 'VSR', 'STEC O157')"
    )

    # Clasificación
    categoria: str = Field(
        max_length=50,
        index=True,
        description="Categoría: virus, bacteria, parasito, hongo, prion, otro"
    )
    grupo: str = Field(
        max_length=50,
        index=True,
        description="Grupo funcional: respiratorio, enterico, vectorial, zoonotico, etc."
    )

    # Metadata
    descripcion: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Descripción del agente y relevancia epidemiológica"
    )

    # Estado
    activo: bool = Field(
        default=True,
        index=True,
        description="Si el agente está activo para extracción"
    )

    # Relaciones
    configs_extraccion: List["AgenteExtraccionConfig"] = Relationship(
        back_populates="agente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    eventos_agente: List["EventoAgente"] = Relationship(
        back_populates="agente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class AgenteExtraccionConfig(BaseModel, table=True):
    """
    Configuración de extracción de agentes desde el CSV.

    Define CÓMO detectar un agente específico en un tipo de evento,
    incluyendo qué campos buscar y qué valores indican positivo.

    Ejemplo para VSR en UC-IRAG:
    - campo_busqueda: "DETERMINACION"
    - patron_busqueda: "VSR|Sincicial"
    - campo_resultado: "RESULTADO"
    - valores_positivos: ["Positivo", "Detectable"]

    Ejemplo para STEC en Diarrea aguda:
    - campo_busqueda: "CLASIFICACION_MANUAL"
    - patron_busqueda: "STEC|O157"
    - campo_resultado: None (la clasificación ya indica positivo)
    - valores_positivos: None
    """

    __tablename__ = "agente_extraccion_config"
    __table_args__ = (
        UniqueConstraint(
            "id_agente", "id_tipo_eno", "campo_busqueda",
            name="uq_agente_tipo_eno_campo"
        ),
        Index("idx_config_agente", "id_agente"),
        Index("idx_config_tipo_eno", "id_tipo_eno"),
        Index("idx_config_activo", "activo"),
    )

    # Relaciones
    id_agente: int = Field(
        foreign_key="agente_etiologico.id",
        description="ID del agente a extraer"
    )
    id_tipo_eno: int = Field(
        foreign_key="tipo_eno.id",
        description="ID del tipo de evento donde buscar"
    )

    # Configuración de búsqueda
    campo_busqueda: str = Field(
        max_length=100,
        description="Campo del CSV donde buscar (ej: 'DETERMINACION', 'CLASIFICACION_MANUAL')"
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

    # Configuración de resultado (opcional - algunos agentes se detectan solo por clasificación)
    campo_resultado: Optional[str] = Field(
        None,
        max_length=100,
        description="Campo donde verificar resultado positivo (ej: 'RESULTADO'). NULL si no aplica."
    )
    valores_positivos: Optional[List[str]] = Field(
        None,
        sa_column=Column(JSON),
        description="Valores que indican resultado positivo (ej: ['Positivo', 'Detectable'])"
    )

    # Método de detección (para registro)
    metodo_deteccion_default: Optional[str] = Field(
        None,
        max_length=100,
        description="Método de detección por defecto (ej: 'PCR', 'cultivo', 'serologia')"
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

    # Notas
    notas: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Notas sobre esta configuración de extracción"
    )

    # Relaciones
    agente: "AgenteEtiologico" = Relationship(back_populates="configs_extraccion")
    tipo_eno: "TipoEno" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[AgenteExtraccionConfig.id_tipo_eno]"}
    )
    eventos_extraidos: List["EventoAgente"] = Relationship(
        back_populates="config_usada",
        sa_relationship_kwargs={"foreign_keys": "[EventoAgente.id_config_usada]"}
    )


class ResultadoDeteccion(str, Enum):
    """Estados posibles de detección de un agente"""
    POSITIVO = "POSITIVO"
    NEGATIVO = "NEGATIVO"
    INDETERMINADO = "INDETERMINADO"
    NO_REALIZADO = "NO_REALIZADO"


class EventoAgente(BaseModel, table=True):
    """
    Relación N:M entre Evento y AgenteEtiologico.

    Registra qué agentes fueron buscados/detectados en cada evento,
    incluyendo tanto positivos como negativos.

    Esto permite:
    - Saber qué agentes se confirmaron (positivo)
    - Saber qué agentes se descartaron (negativo)
    - Diagnóstico diferencial
    - Análisis de qué se está testeando

    Soporta coinfecciones: un evento puede tener múltiples agentes positivos.
    """

    __tablename__ = "evento_agente"
    __table_args__ = (
        UniqueConstraint(
            "id_evento", "id_agente",
            name="uq_evento_agente"
        ),
        Index("idx_evento_agente_evento", "id_evento"),
        Index("idx_evento_agente_agente", "id_agente"),
        Index("idx_evento_agente_fecha", "fecha_deteccion"),
        Index("idx_evento_agente_resultado", "resultado"),
    )

    # Relaciones principales
    id_evento: int = Field(
        foreign_key="evento.id",
        description="ID del evento epidemiológico"
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
        description="Método de detección usado (ej: 'PCR', 'cultivo', 'serologia')"
    )
    resultado_raw: Optional[str] = Field(
        None,
        max_length=200,
        description="Valor original del resultado (ej: 'Positivo (+)', 'Negativo')"
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
        description="Config que extrajo este agente (trazabilidad)"
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
    evento: "Evento" = Relationship(
        back_populates="agentes_detectados",
        sa_relationship_kwargs={"foreign_keys": "evento_agente.c.id_evento"}
    )
    agente: "AgenteEtiologico" = Relationship(back_populates="eventos_agente")
    config_usada: Optional["AgenteExtraccionConfig"] = Relationship(
        back_populates="eventos_extraidos",
        sa_relationship_kwargs={"foreign_keys": "evento_agente.c.id_config_usada"}
    )
