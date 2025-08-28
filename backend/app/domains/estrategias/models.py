"""
Modelos para el sistema de estrategias de clasificación de eventos epidemiológicos.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import JSON, Column, Index, Text
from sqlmodel import Field, Relationship, SQLModel


class TipoFiltro(str, Enum):
    """Tipos de filtros soportados para clasificación"""

    CAMPO_IGUAL = "CAMPO_IGUAL"
    CAMPO_EN_LISTA = "CAMPO_EN_LISTA"
    CAMPO_CONTIENE = "CAMPO_CONTIENE"
    REGEX_EXTRACCION = "REGEX_EXTRACCION"
    CAMPO_EXISTE = "CAMPO_EXISTE"
    CAMPO_NO_NULO = "CAMPO_NO_NULO"
    CUSTOM_FUNCTION = "CUSTOM_FUNCTION"
    DETECTOR_TIPO_SUJETO = (
        "DETECTOR_TIPO_SUJETO"  # Detecta si es humano/animal/indeterminado
    )
    EXTRACTOR_METADATA = (
        "EXTRACTOR_METADATA"  # Extrae información adicional sin cambiar clasificación
    )


class TipoClasificacion(str, Enum):
    """Clasificaciones estándar de eventos epidemiológicos"""

    CONFIRMADOS = "CONFIRMADOS"
    SOSPECHOSOS = "SOSPECHOSOS"
    PROBABLES = "PROBABLES"
    EN_ESTUDIO = "EN_ESTUDIO"
    NEGATIVOS = "NEGATIVOS"
    DESCARTADOS = "DESCARTADOS"
    NOTIFICADOS = "NOTIFICADOS"
    CON_RESULTADO_MORTAL = "CON_RESULTADO_MORTAL"
    SIN_RESULTADO_MORTAL = "SIN_RESULTADO_MORTAL"
    REQUIERE_REVISION = (
        "REQUIERE_REVISION"  # Casos ambiguos que requieren revisión manual
    )


class EventStrategy(SQLModel, table=True):
    """
    Estrategia de procesamiento para un tipo de evento epidemiológico.

    Define cómo se clasifica y procesa un tipo específico de evento,
    incluyendo sus reglas de clasificación y gráficos disponibles.
    """

    __tablename__ = "event_strategy"
    __table_args__ = (
        Index("idx_event_strategy_tipo_eno", "tipo_eno_id"),
        Index("idx_event_strategy_active", "is_active"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identificación
    tipo_eno_id: int = Field(
        foreign_key="tipo_eno.id",
        unique=True,
        description="ID del tipo de ENO asociado",
    )
    name: str = Field(
        max_length=100,
        index=True,
        description="Nombre de la estrategia (ej: DengueEstrategia)",
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Descripción de la estrategia"
    )
    notas_admin: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Notas técnicas para administradores sobre decisiones de clasificación",
    )
    casos_especiales: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Documentación de casos especiales o ambiguos y cómo manejarlos",
    )

    # Configuración específica
    grupo_evento: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Grupo al que pertenece el evento (ej: IRA, Sífilis)",
    )
    usa_provincia_carga: bool = Field(
        default=False,
        description="Si usa PROVINCIA_CARGA en lugar de PROVINCIA_RESIDENCIA",
    )
    eventos_relacionados: List[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Lista de eventos relacionados que comparten estrategia",
    )

    # Visualizaciones disponibles
    graficos_disponibles: List[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Tipos de gráficos disponibles para este evento",
    )

    # Configuración adicional
    config: Optional[Dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Configuración adicional específica del evento",
    )

    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza para clasificación automática",
    )

    # Control de versiones
    version: int = Field(default=1, description="Versión de la estrategia")
    is_active: bool = Field(
        default=True, index=True, description="Si la estrategia está activa"
    )

    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, max_length=100)
    updated_by: Optional[str] = Field(default=None, max_length=100)

    # Relaciones
    classification_rules: List["ClassificationRule"] = Relationship(
        back_populates="strategy", cascade_delete=True
    )

    # Propiedades calculadas
    @property
    def active(self) -> bool:
        """Alias para compatibilidad con frontend."""
        return self.is_active

    @property
    def classification_rules_count(self) -> int:
        """Contador de reglas de clasificación."""
        return len(self.classification_rules) if self.classification_rules else 0

    def __init__(self, **data):
        super().__init__(**data)
        self._tipo_eno_name: Optional[str] = None

    @property
    def tipo_eno_name(self) -> Optional[str]:
        """Nombre del tipo de evento (poblado dinámicamente)."""
        return getattr(self, "_tipo_eno_name", None)

    @tipo_eno_name.setter
    def tipo_eno_name(self, value: Optional[str]):
        self._tipo_eno_name = value


class ClassificationRule(SQLModel, table=True):
    """
    Regla de clasificación para eventos epidemiológicos.

    Define cómo se clasifica un evento en categorías como
    confirmado, sospechoso, etc., basado en condiciones específicas.
    """

    __tablename__ = "classification_rule"
    __table_args__ = (
        Index("idx_classification_rule_strategy", "strategy_id", "classification"),
        Index("idx_classification_rule_priority", "priority"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con estrategia
    strategy_id: int = Field(
        foreign_key="event_strategy.id", description="ID de la estrategia padre"
    )

    # Clasificación objetivo
    classification: str = Field(
        description="Tipo de clasificación que aplica esta regla"
    )
    name: str = Field(max_length=100, description="Nombre descriptivo de la regla")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Descripción detallada de la regla"
    )
    justificacion: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Justificación epidemiológica de por qué se aplica esta regla",
    )
    ejemplos: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Ejemplos de casos que cumplen esta regla",
    )

    # Prioridad de evaluación (menor valor = mayor prioridad)
    priority: int = Field(
        default=100, description="Orden de evaluación (1 = máxima prioridad)"
    )

    # Estado
    is_active: bool = Field(default=True, description="Si la regla está activa")
    auto_approve: bool = Field(
        default=True,
        description="Si puede aprobarse automáticamente o requiere revisión manual",
    )
    required_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Nivel mínimo de confianza requerido para aplicar esta regla",
    )

    # Relaciones
    strategy: EventStrategy = Relationship(back_populates="classification_rules")
    filters: List["FilterCondition"] = Relationship(
        back_populates="rule", cascade_delete=True
    )


class FilterCondition(SQLModel, table=True):
    """
    Condición de filtro individual para una regla de clasificación.

    Define una condición específica que debe cumplirse para
    aplicar una clasificación a un evento.
    """

    __tablename__ = "filter_condition"
    __table_args__ = (
        Index("idx_filter_condition_rule", "rule_id"),
        Index("idx_filter_condition_strategy", "strategy_id"),
        Index("idx_filter_condition_field", "field_name"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con regla (para filtros de clasificación)
    rule_id: Optional[int] = Field(
        default=None,
        foreign_key="classification_rule.id",
        description="ID de la regla padre (para filtros de clasificación)",
    )

    # Relación directa con estrategia (para metadata extractors)
    strategy_id: Optional[int] = Field(
        default=None,
        foreign_key="event_strategy.id",
        description="ID de la estrategia (para metadata extractors)",
    )

    # Tipo de filtro
    filter_type: TipoFiltro = Field(description="Tipo de operación de filtrado")

    # Campo objetivo
    field_name: str = Field(
        max_length=100,
        index=True,
        description="Nombre del campo a evaluar (ej: CLASIFICACION_MANUAL)",
    )

    # Configuración completa del filtro en un solo campo JSON
    config: Dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Configuración completa del filtro (value, values, pattern, etc.)",
    )

    # Campo para metadata extraída
    extracted_metadata_field: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Campo donde guardar metadata extraída (ej: 'tipo_sujeto', 'fuente_contagio')",
    )
    """
    Ejemplo para extracción de rabia:
    {
        "extraction_fields": ["NOMBRE", "APELLIDO"],
        "normalization": {
            "muercielago": "murcielago",
            "tadarida": "murcielago"
        },
        "case_insensitive": true,
        "create_field": "fuente_contagio"
    }
    """

    # Operador lógico con siguiente condición
    logical_operator: str = Field(
        default="AND", description="Operador lógico con siguiente condición (AND/OR)"
    )

    # Orden de evaluación dentro de la regla
    order: int = Field(default=0, description="Orden de evaluación dentro de la regla")

    # Relaciones
    rule: Optional[ClassificationRule] = Relationship(back_populates="filters")


class StrategyChangeLog(SQLModel, table=True):
    """
    Log de auditoría para cambios en estrategias.

    Mantiene un historial completo de todos los cambios realizados
    en las estrategias para auditoría y rollback si es necesario.
    """

    __tablename__ = "strategy_change_log"
    __table_args__ = (
        Index("idx_strategy_change_log_strategy", "strategy_id"),
        Index("idx_strategy_change_log_date", "changed_at"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Estrategia afectada
    strategy_id: int = Field(
        foreign_key="event_strategy.id",
        index=True,
        description="ID de la estrategia modificada",
    )

    # Tipo de cambio
    change_type: str = Field(
        max_length=255,
        description="Tipo de cambio (CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE)",
    )

    # Detalle de cambios
    changes: Dict = Field(
        sa_column=Column(JSON),
        description="JSON con el detalle de los cambios realizados",
    )
    """
    Formato:
    {
        "old": {"field": "old_value"},
        "new": {"field": "new_value"}
    }
    """

    # Auditoría
    changed_by: str = Field(max_length=100, description="Usuario que realizó el cambio")
    changed_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Fecha y hora del cambio",
    )
    reason: Optional[str] = Field(
        default=None, max_length=500, description="Razón o justificación del cambio"
    )

    # IP y contexto adicional
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Dirección IP desde donde se realizó el cambio",
    )
    user_agent: Optional[str] = Field(
        default=None, max_length=500, description="User agent del navegador/cliente"
    )


class EventClassificationAudit(SQLModel, table=True):
    """
    Auditoría de clasificaciones aplicadas a eventos epidemiológicos.

    Registra cada vez que se clasifica un evento, incluyendo metadata
    extraída, confianza de la detección y cualquier revisión manual.
    """

    __tablename__ = "event_classification_audit"
    __table_args__ = (
        Index("idx_event_classification_audit_evento", "id_evento"),
        Index("idx_event_classification_audit_strategy", "strategy_id"),
        Index("idx_event_classification_audit_date", "classified_at"),
        Index("idx_event_classification_audit_confidence", "confidence_score"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con evento y estrategia
    id_evento: int = Field(
        foreign_key="evento.id", index=True, description="ID del evento clasificado"
    )
    strategy_id: int = Field(
        foreign_key="event_strategy.id",
        index=True,
        description="ID de la estrategia utilizada",
    )

    # Resultados de la clasificación
    clasificacion_aplicada: str = Field(
        description="Clasificación epidemiológica aplicada"
    )
    rule_id_applied: Optional[int] = Field(
        default=None,
        foreign_key="classification_rule.id",
        description="ID de la regla específica que se aplicó",
    )

    # Detección de tipo de sujeto
    tipo_sujeto_detectado: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Tipo detectado: humano, animal, indeterminado",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Puntuación de confianza de la detección (0.0 a 1.0)",
    )

    # Metadata extraída
    metadata_extraida: Optional[Dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Metadata extraída durante la clasificación (fuente_contagio, especie, etc.)",
    )
    """
    Ejemplo:
    {
        "fuente_contagio": "murcielago",
        "tipo_sujeto": "animal",
        "especie_detectada": "TADARIDA BRASILIENSIS",
        "taxonomia": {
            "genero": "TADARIDA",
            "especie": "BRASILIENSIS"
        },
        "confidence": 0.85,
        "metodos_deteccion": ["patron_taxonomico", "sexo_indeterminado"]
    }
    """

    # Estado de revisión
    requiere_revision_manual: bool = Field(
        default=False, description="Si requiere revisión manual por ambigüedad"
    )
    revision_completada: bool = Field(
        default=False, description="Si ya fue revisado manualmente"
    )
    revisado_por: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Usuario que realizó la revisión manual",
    )
    fecha_revision: Optional[datetime] = Field(
        default=None, description="Fecha de revisión manual"
    )

    # Cambios posteriores a revisión
    clasificacion_original: Optional[str] = Field(
        default=None, description="Clasificación original antes de revisión manual"
    )
    tipo_sujeto_original: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Tipo de sujeto original antes de revisión manual",
    )
    metadata_original: Optional[Dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Metadata original antes de revisión manual",
    )

    # Notas y justificaciones
    notas_revision: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Notas del revisor sobre cambios realizados",
    )
    razon_ambiguedad: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Razón por la cual el caso fue marcado como ambiguo",
    )

    # Auditoría temporal
    classified_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Fecha y hora de la clasificación automática",
    )

    # Información del CSV original (para casos ambiguos)
    datos_csv_originales: Optional[Dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Datos originales del CSV para referencia en casos ambiguos",
    )

    # Procesamiento adicional
    procesamiento_version: str = Field(
        default="1.0",
        max_length=10,
        description="Versión del algoritmo de procesamiento utilizado",
    )
    tiempo_procesamiento_ms: Optional[int] = Field(
        default=None, description="Tiempo de procesamiento en milisegundos"
    )
