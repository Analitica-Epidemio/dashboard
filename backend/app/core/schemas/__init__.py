"""Schemas del sistema siguiendo mejores prácticas."""

from .response import (
    DataResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
)

__all__ = [
    "DataResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "SuccessResponse",
]
