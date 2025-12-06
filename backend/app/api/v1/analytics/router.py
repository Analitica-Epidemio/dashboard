"""
Analytics router
"""

from fastapi import APIRouter

from app.api.v1.analytics.calculate_changes import calculate_changes
from app.api.v1.analytics.get_analytics import get_analytics
from app.api.v1.analytics.get_date_range import DateRangeResponse, get_date_range
from app.api.v1.analytics.get_evento_details import get_evento_details
from app.api.v1.analytics.get_top_changes_by_group import get_top_changes_by_group
from app.api.v1.analytics.get_top_winners_losers import get_top_winners_losers
from app.api.v1.analytics.schemas import (
    AnalyticsResponse,
    CalculateChangesResponse,
    CasoEpidemiologicoDetailsResponse,
    TopChangesByGroupResponse,
    TopWinnersLosersResponse,
)
from app.core.schemas.response import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

router.add_api_route(
    "",
    get_analytics,
    methods=["GET"],
    response_model=SuccessResponse[AnalyticsResponse],
    name="get_analytics",
    summary="Obtiene métricas de analytics comparando dos períodos",
    responses={
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/top-winners-losers",
    get_top_winners_losers,
    methods=["GET"],
    response_model=SuccessResponse[TopWinnersLosersResponse],
    name="get_top_winners_losers",
    summary="Obtiene las entidades con mayor cambio (winners/losers)",
    responses={
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/date-range",
    get_date_range,
    methods=["GET"],
    response_model=SuccessResponse[DateRangeResponse],
    name="get_date_range",
    summary="Obtiene el rango de fechas con datos disponibles",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# ============================================================================
# Nuevos endpoints para sistema de boletines
# ============================================================================

router.add_api_route(
    "/top-changes-by-group",
    get_top_changes_by_group,
    methods=["GET"],
    response_model=SuccessResponse[TopChangesByGroupResponse],
    name="get_top_changes_by_group",
    summary="Obtiene top eventos con mayor crecimiento/decrecimiento por grupo epidemiológico",
    responses={
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/calculate-changes",
    calculate_changes,
    methods=["POST"],
    response_model=SuccessResponse[CalculateChangesResponse],
    name="calculate_changes",
    summary="Calcula cambios para eventos custom seleccionados manualmente",
    responses={
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

router.add_api_route(
    "/evento-details/{tipo_eno_id}",
    get_evento_details,
    methods=["GET"],
    response_model=SuccessResponse[CasoEpidemiologicoDetailsResponse],
    name="get_evento_details",
    summary="Obtiene detalles completos de un evento (para dialog)",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "CasoEpidemiologico no encontrado",
        },
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
