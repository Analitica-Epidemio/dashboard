"""Schemas comunes para respuestas estándar de la API."""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detalle de un error."""
    
    code: str = Field(..., description="Código único del error")
    message: str = Field(..., description="Mensaje descriptivo del error")
    field: Optional[str] = Field(None, description="Campo asociado al error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")


class StandardResponse(BaseModel, Generic[T]):
    """Respuesta estándar de la API."""
    
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    data: Optional[T] = Field(None, description="Datos de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Lista de errores si los hay")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "message": "Operación exitosa",
                "errors": None,
                "metadata": {"timestamp": "2024-01-01T00:00:00Z"}
            }
        }