"""
Router principal para personas (ciudadanos y animales).
Organiza los endpoints por responsabilidad - Vista centrada en personas (PERSON-CENTERED).
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse

from .get_detail import PersonaDetailResponse, get_persona_detail
from .get_timeline import PersonaTimelineResponse, get_persona_timeline
from .list import PersonaListResponse, list_personas

# Crear router principal
router = APIRouter(prefix="/personas", tags=["Personas"])

# Registrar endpoint de listado
router.add_api_route(
    "/",
    list_personas,
    methods=["GET"],
    response_model=SuccessResponse[PersonaListResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)

# Registrar endpoints de detalle
router.add_api_route(
    "/{tipo_sujeto}/{persona_id}",
    get_persona_detail,
    methods=["GET"],
    response_model=SuccessResponse[PersonaDetailResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Persona no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/{tipo_sujeto}/{persona_id}/timeline",
    get_persona_timeline,
    methods=["GET"],
    response_model=SuccessResponse[PersonaTimelineResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Persona no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
