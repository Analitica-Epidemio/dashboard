"""
Analytics router
"""

from fastapi import APIRouter

from app.api.v1.analytics.get_analytics import get_analytics
from app.api.v1.analytics.get_top_winners_losers import get_top_winners_losers
from app.api.v1.analytics.schemas import AnalyticsResponse, TopWinnersLosersResponse
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
