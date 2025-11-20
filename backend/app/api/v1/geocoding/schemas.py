"""
Schemas para la API de geocodificación.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class GeocodingStatsResponse(BaseModel):
    """Respuesta con estadísticas de geocodificación."""

    total_domicilios: int = Field(
        ..., description="Total de domicilios en el sistema"
    )
    geocoded: int = Field(..., description="Domicilios geocodificados exitosamente")
    pending: int = Field(..., description="Domicilios pendientes de geocodificar")
    processing: int = Field(..., description="Domicilios siendo procesados actualmente")
    failed: int = Field(..., description="Domicilios con fallo permanente")
    not_geocodable: int = Field(..., description="Domicilios no geocodificables")
    percentage_geocoded: float = Field(
        ..., description="Porcentaje de domicilios geocodificados"
    )
    by_estado: Dict[str, int] = Field(
        ..., description="Conteo de domicilios por cada estado de geocodificación"
    )


class TriggerGeocodingResponse(BaseModel):
    """Respuesta al triggear geocodificación manual."""

    message: str = Field(..., description="Mensaje descriptivo del resultado")
    pending_count: int = Field(..., description="Número de domicilios pendientes")
    task_id: Optional[str] = Field(
        None, description="ID de la tarea encolada (si se inició)"
    )
    batch_size: Optional[int] = Field(
        None, description="Tamaño del batch de procesamiento"
    )
    estimated_batches: Optional[int] = Field(
        None, description="Número estimado de batches a procesar"
    )
