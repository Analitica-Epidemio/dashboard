"""
Charts router - Dynamic charts endpoints
"""

from fastapi import APIRouter

from .get_dashboard import get_dashboard_charts
from .get_disponibles import get_charts_disponibles
from .get_indicadores import get_indicadores

router = APIRouter(prefix="/charts", tags=["Charts"])

# Get dashboard charts endpoint
router.add_api_route(
    "/dashboard",
    get_dashboard_charts,
    methods=["GET"]
)

# Get indicadores endpoint
router.add_api_route(
    "/indicadores",
    get_indicadores,
    methods=["GET"]
)

# Get available charts endpoint
router.add_api_route(
    "/disponibles",
    get_charts_disponibles,
    methods=["GET"]
)