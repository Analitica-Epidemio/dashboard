"""
Schemas de respuesta siguiendo mejores prácticas de la industria.

Basado en:
- Stripe API
- GitHub API
- Google JSON Style Guide
- JSON:API Specification
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Metadata de paginación con tipos específicos."""

    page: int = Field(..., description="Página actual (1-indexed)", ge=1)
    page_size: int = Field(..., description="Elementos por página", ge=1, le=100)
    total: int = Field(..., description="Total de elementos", ge=0)
    total_pages: int = Field(..., description="Total de páginas", ge=0)
    has_next: Optional[bool] = Field(
        default=None, description="Si hay página siguiente"
    )
    has_prev: Optional[bool] = Field(default=None, description="Si hay página anterior")


class ErrorDetail(BaseModel):
    """Detalle de un error específico."""

    code: str = Field(..., description="Código de error machine-readable")
    message: str = Field(..., description="Mensaje human-readable")
    field: Optional[str] = Field(default=None, description="Campo que causó el error")


class ErrorResponse(BaseModel):
    """
    Respuesta de error estándar.

    Se usa SOLO con códigos HTTP 4xx/5xx.
    Basado en Google JSON Style Guide.
    """

    error: ErrorDetail = Field(..., description="Detalle del error")
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Lista de errores adicionales (para validación múltiple)",
    )
    request_id: Optional[str] = Field(
        default=None, description="ID único para tracking"
    )


class SuccessResponse(BaseModel, Generic[T]):
    """
    Respuesta exitosa estándar.

    Se usa SOLO con códigos HTTP 2xx.
    El campo 'data' contiene el resultado.
    """

    data: T = Field(..., description="Datos de la respuesta")
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata opcional (paginación, etc)"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Respuesta paginada estándar.

    Para listados con paginación.
    """

    data: List[T] = Field(..., description="Lista de elementos")
    meta: PaginationMeta = Field(
        ...,
        description="Información de paginación con tipos específicos",
    )
    links: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Enlaces de navegación",
        example={
            "first": "/api/items?page=1",
            "prev": None,
            "next": "/api/items?page=2",
            "last": "/api/items?page=5",
        },
    )


# Aliases para compatibilidad y claridad
DataResponse = SuccessResponse  # Más claro que el dato es la respuesta
