"""
Geocoding router - Manual geocoding triggers and stats
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse

from .get_stats import get_geocoding_stats
from .schemas import GeocodingStatsResponse, TriggerGeocodingResponse
from .trigger_geocoding import trigger_geocoding

router = APIRouter(prefix="/geocoding", tags=["Geocoding"])

# Trigger geocoding endpoint
router.add_api_route(
    "/trigger",
    trigger_geocoding,
    methods=["POST"],
    response_model=TriggerGeocodingResponse,
    responses={
        200: {
            "description": "Geocodificación triggeada exitosamente",
        },
        400: {"model": ErrorResponse, "description": "Geocodificación deshabilitada"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

# Get geocoding stats endpoint
router.add_api_route(
    "/stats",
    get_geocoding_stats,
    methods=["GET"],
    response_model=GeocodingStatsResponse,
    responses={
        200: {
            "description": "Estadísticas de geocodificación",
        },
    },
)
