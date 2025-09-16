"""
Router principal para eventos epidemiológicos.
Organiza los endpoints por responsabilidad.
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse
from .get_detail import get_evento_detail, EventoDetailResponse
from .get_timeline import get_evento_timeline, EventoTimelineResponse
from .export import export_eventos
from .list import list_eventos, EventoListResponse

# Crear router principal
router = APIRouter(prefix="/eventos", tags=["Eventos"])

# Registrar endpoints de listado
router.add_api_route(
    "/",
    list_eventos,
    methods=["GET"],
    response_model=SuccessResponse[EventoListResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)

# Registrar endpoints de detalle
router.add_api_route(
    "/{evento_id}",
    get_evento_detail,
    methods=["GET"],
    response_model=SuccessResponse[EventoDetailResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Evento no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/{evento_id}/timeline",
    get_evento_timeline,
    methods=["GET"],
    response_model=SuccessResponse[EventoTimelineResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Evento no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Registrar endpoint de exportación
router.add_api_route(
    "/export",
    export_eventos,
    methods=["GET"],
    responses={
        200: {"description": "Archivo CSV/Excel con los eventos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)