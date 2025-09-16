"""
Grupos ENO router
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, PaginatedResponse

from .list import GrupoEnoInfo, list_grupos_eno

router = APIRouter(prefix="/gruposEno", tags=["GruposENO"])

# List grupos ENO endpoint
router.add_api_route(
    "/",
    list_grupos_eno,
    methods=["GET"],
    response_model=PaginatedResponse[GrupoEnoInfo],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)