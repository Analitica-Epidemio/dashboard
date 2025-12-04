"""
Schemas de Pydantic para las estrategias de clasificación.

Definiciones para:
- Request/Response DTOs
- Validación de datos
- Serialización API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domains.eventos_epidemiologicos.clasificacion.models import (
    TipoClasificacion,
    TipoFiltro,
)


class FilterConditionRequest(BaseModel):
    """Request DTO para condiciones de filtro."""

    filter_type: TipoFiltro = Field(..., description="Tipo de filtro")
    field_name: str = Field(..., min_length=1, description="Nombre del campo a filtrar")
    value: Optional[str] = Field(None, description="Valor para filtros de valor único")
    values: Optional[List[str]] = Field(
        None, description="Lista de valores para filtros múltiples"
    )
    logical_operator: str = Field("AND", description="Operador lógico (AND/OR)")
    order: int = Field(0, ge=0, description="Orden de aplicación del filtro")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Configuración adicional específica del filtro"
    )
    extracted_metadata_field: Optional[str] = Field(
        None, description="Campo donde guardar metadata extraída"
    )

    @field_validator("logical_operator")
    @classmethod
    def validate_logical_operator(cls, v):
        if v not in ["AND", "OR"]:
            raise ValueError("logical_operator debe ser AND o OR")
        return v

    @field_validator("value", "values")
    @classmethod
    def validate_filter_values(cls, v, info):
        field_name = info.field_name
        values = info.data
        filter_type = values.get("filter_type")

        if filter_type in [TipoFiltro.CAMPO_IGUAL, TipoFiltro.CAMPO_CONTIENE]:
            if field_name == "value" and not v:
                raise ValueError(f"value es requerido para filtro tipo {filter_type}")

        elif filter_type == TipoFiltro.CAMPO_EN_LISTA:
            if field_name == "values" and (not v or len(v) == 0):
                raise ValueError("values es requerido para filtro tipo campo_en_lista")

        return v


class FilterConditionResponse(FilterConditionRequest):
    """Response DTO para condiciones de filtro."""

    id: Optional[int] = Field(None, description="ID del filtro")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(
        None, description="Fecha de última actualización"
    )

    class Config:
        from_attributes = True


class ClassificationRuleRequest(BaseModel):
    """Request DTO para reglas de clasificación."""

    classification: TipoClasificacion = Field(
        ..., description="Tipo de clasificación resultante"
    )
    priority: int = Field(
        ..., ge=1, le=100, description="Prioridad de la regla (1 = mayor prioridad)"
    )
    is_active: bool = Field(True, description="Si la regla está activa")
    auto_approve: bool = Field(
        True, description="Si los casos se aprueban automáticamente"
    )
    required_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confianza mínima requerida (0.0-1.0)"
    )
    filters: List[FilterConditionRequest] = Field(
        [], description="Lista de condiciones de filtro"
    )

    @field_validator("filters")
    @classmethod
    def validate_at_least_one_filter(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Debe tener al menos un filtro")

        # También validar órdenes únicos
        orders = [f.order for f in v]
        if len(set(orders)) != len(orders):
            raise ValueError("Los órdenes de filtros deben ser únicos")
        return v


class ClassificationRuleResponse(ClassificationRuleRequest):
    """Response DTO para reglas de clasificación."""

    id: Optional[int] = Field(None, description="ID de la regla")
    filters: List[FilterConditionResponse] = Field([], description="Lista de filtros")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(
        None, description="Fecha de última actualización"
    )

    class Config:
        from_attributes = True


class EventStrategyBase(BaseModel):
    """Base DTO para estrategias."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre de la estrategia"
    )
    tipo_eno_id: int = Field(..., description="ID del tipo de evento epidemiológico")
    active: bool = Field(True, description="Si la estrategia está activa")
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Umbral de confianza general"
    )
    description: Optional[str] = Field(
        None, description="Descripción completa de la estrategia"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Configuración adicional (filtros geográficos, etc.)"
    )
    valid_from: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha desde cuando la estrategia es válida"
    )
    valid_until: Optional[datetime] = Field(
        None, description="Fecha hasta cuando la estrategia es válida (None = sin fin)"
    )

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until(cls, v, info):
        """Valida que valid_until sea posterior a valid_from."""
        values = info.data
        valid_from = values.get("valid_from")
        if v is not None and valid_from is not None and v <= valid_from:
            raise ValueError("valid_until debe ser posterior a valid_from")
        return v


class EventStrategyCreate(EventStrategyBase):
    """Request DTO para crear estrategia."""

    classification_rules: List[ClassificationRuleRequest] = Field(
        [], description="Reglas de clasificación"
    )
    metadata_extractors: List[FilterConditionRequest] = Field(
        [], description="Extractores de metadata"
    )

    @field_validator("classification_rules")
    @classmethod
    def validate_rules(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Debe definir al menos una regla de clasificación")

        # Validar prioridades únicas
        priorities = [rule.priority for rule in v]
        if len(set(priorities)) != len(priorities):
            raise ValueError("Las prioridades de las reglas deben ser únicas")

        return v


class EventStrategyUpdate(BaseModel):
    """Request DTO para actualizar estrategia."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Nombre de la estrategia"
    )
    active: Optional[bool] = Field(None, description="Si la estrategia está activa")
    confidence_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Umbral de confianza general"
    )
    description: Optional[str] = Field(
        None, description="Descripción de la estrategia"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Configuración adicional"
    )
    valid_from: Optional[datetime] = Field(
        None, description="Fecha desde cuando la estrategia es válida"
    )
    valid_until: Optional[datetime] = Field(
        None, description="Fecha hasta cuando la estrategia es válida (None = sin fin)"
    )
    classification_rules: Optional[List[ClassificationRuleRequest]] = Field(
        None, description="Reglas de clasificación"
    )
    metadata_extractors: Optional[List[FilterConditionRequest]] = Field(
        None, description="Extractores de metadata"
    )

    @field_validator("classification_rules")
    @classmethod
    def validate_rules(cls, v):
        if v is not None:
            if len(v) == 0:
                raise ValueError("Debe definir al menos una regla de clasificación")

            # Validar prioridades únicas
            priorities = [rule.priority for rule in v]
            if len(set(priorities)) != len(priorities):
                raise ValueError("Las prioridades de las reglas deben ser únicas")

        return v


class EventStrategyResponse(EventStrategyBase):
    """Response DTO para estrategias."""

    id: int = Field(..., description="ID de la estrategia")
    tipo_eno_name: Optional[str] = Field(None, description="Nombre del tipo de evento")
    status: str = Field("active", description="Estado de la estrategia")
    classification_rules: List[ClassificationRuleResponse] = Field(
        [], description="Reglas de clasificación"
    )
    metadata_extractors: List[FilterConditionResponse] = Field(
        [], description="Extractores de metadata"
    )
    valid_from: datetime = Field(..., description="Fecha desde cuando la estrategia es válida")
    valid_until: Optional[datetime] = Field(None, description="Fecha hasta cuando la estrategia es válida")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    created_by: Optional[str] = Field(
        None, description="Usuario que creó la estrategia"
    )

    # Campos calculados
    classification_rules_count: Optional[int] = Field(
        None, description="Número de reglas activas"
    )

    @field_validator("status")
    @classmethod
    def determine_status(cls, v, info):
        """Determina el estado basado en los campos."""
        values = info.data
        if values.get("active"):
            return "active"
        elif values.get("classification_rules_count", 0) > 0:
            return "draft"
        else:
            return "pending_review"

    class Config:
        from_attributes = True


class StrategyTestRequest(BaseModel):
    """Request DTO para probar estrategia."""

    csv_data: str = Field(..., description="Datos CSV para probar")
    sample_size: Optional[int] = Field(
        None, ge=1, le=1000, description="Tamaño de muestra a procesar"
    )

    @field_validator("csv_data")
    @classmethod
    def validate_csv_data(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("csv_data no puede estar vacío")

        # Verificar que parece ser CSV válido
        lines = v.strip().split("\n")
        if len(lines) < 2:
            raise ValueError("CSV debe tener al menos header y una fila de datos")

        return v


class StrategyTestResponse(BaseModel):
    """Response DTO para resultados de prueba."""

    total_rows: int = Field(..., description="Total de filas procesadas")
    classified_rows: int = Field(..., description="Filas que fueron clasificadas")
    classification_summary: Dict[str, int] = Field(
        ..., description="Resumen de clasificaciones"
    )
    results_preview: List[Dict[str, Any]] = Field(
        ..., description="Muestra de resultados"
    )
    confidence_stats: Optional[Dict[str, float]] = Field(
        None, description="Estadísticas de confianza"
    )
    processing_time_seconds: Optional[float] = Field(
        None, description="Tiempo de procesamiento"
    )


class AuditAction(str, Enum):
    """Acciones de auditoría."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"


class AuditLogResponse(BaseModel):
    """Response DTO para entradas de auditoría."""

    id: int = Field(..., description="ID de la entrada de auditoría")
    strategy_id: int = Field(..., description="ID de la estrategia")
    strategy_name: str = Field(..., description="Nombre de la estrategia")
    action: AuditAction = Field(..., description="Acción realizada")
    field_changed: Optional[str] = Field(None, description="Campo modificado")
    old_value: Optional[str] = Field(None, description="Valor anterior")
    new_value: Optional[str] = Field(None, description="Nuevo valor")
    changed_by: str = Field(..., description="Usuario que realizó el cambio")
    changed_at: datetime = Field(..., description="Fecha y hora del cambio")
    ip_address: Optional[str] = Field(None, description="Dirección IP del usuario")
    user_agent: Optional[str] = Field(None, description="User agent del navegador")

    class Config:
        from_attributes = True


class ClassificationResultResponse(BaseModel):
    """Response DTO para resultados de clasificación."""

    ideventocaso: str = Field(..., description="ID del caso")
    clasificacion: str = Field(..., description="Clasificación asignada")
    es_positivo: bool = Field(..., description="Si es un caso positivo")
    confidence_score: Optional[float] = Field(
        None, description="Puntuación de confianza"
    )
    tipo_sujeto_detectado: Optional[str] = Field(
        None, description="Tipo de sujeto detectado"
    )
    metadata_extraida: Optional[Dict[str, Any]] = Field(
        None, description="Metadata adicional extraída"
    )
    requiere_revision: bool = Field(False, description="Si requiere revisión manual")
    regla_aplicada: Optional[str] = Field(
        None, description="Nombre de la regla que se aplicó"
    )


class BatchClassificationRequest(BaseModel):
    """Request DTO para clasificación en lote."""

    csv_data: str = Field(..., description="Datos CSV para clasificar")
    tipo_eno_id: int = Field(..., description="ID del tipo de evento")
    save_results: bool = Field(True, description="Si guardar los resultados")
    override_existing: bool = Field(
        False, description="Si sobrescribir clasificaciones existentes"
    )


class BatchClassificationResponse(BaseModel):
    """Response DTO para clasificación en lote."""

    job_id: str = Field(..., description="ID del job de procesamiento")
    total_rows: int = Field(..., description="Total de filas a procesar")
    estimated_time_seconds: Optional[int] = Field(
        None, description="Tiempo estimado de procesamiento"
    )
    polling_url: str = Field(..., description="URL para consultar el estado del job")
