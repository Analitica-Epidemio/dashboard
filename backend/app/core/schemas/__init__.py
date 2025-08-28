"""Schemas del sistema siguiendo mejores prácticas."""

from .response import (
    DataResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "DataResponse",
]
