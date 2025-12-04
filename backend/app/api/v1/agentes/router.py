"""
Agentes Etiológicos router
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, PaginatedResponse

from .list import (
    AgenteEtiologicoInfo,
    AgentesCategoriasResponse,
    get_agentes_categorias,
    list_agentes,
)

router = APIRouter(prefix="/agentes", tags=["Agentes Etiológicos"])

# List agentes endpoint
router.add_api_route(
    "/",
    list_agentes,
    methods=["GET"],
    response_model=PaginatedResponse[AgenteEtiologicoInfo],
    summary="Listar agentes etiológicos",
    description="Lista todos los agentes etiológicos con estadísticas de eventos",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)

# Get categorías y grupos
router.add_api_route(
    "/categorias",
    get_agentes_categorias,
    methods=["GET"],
    response_model=AgentesCategoriasResponse,
    summary="Obtener categorías y grupos",
    description="Obtiene las categorías y grupos únicos de agentes para filtros",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)
