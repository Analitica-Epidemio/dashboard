"""
Tipos ENO router
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, PaginatedResponse
from .list import list_tipos_eno, TipoEnoInfo

router = APIRouter(prefix="/tiposEno", tags=["TiposENO"])

# List tipos ENO endpoint
router.add_api_route(
    "/",
    list_tipos_eno,
    methods=["GET"],
    response_model=PaginatedResponse[TipoEnoInfo],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)