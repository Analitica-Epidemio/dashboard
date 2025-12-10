"""
Charts router - UniversalChartSpec endpoints
100% migrado al nuevo sistema con datos REALES

NOTA: /charts/disponibles fue migrado a /boletines/charts-disponibles
"""

from fastapi import APIRouter

from .generate_spec import router as chart_spec_router
from .get_dashboard import get_dashboard_charts
from .get_indicadores import get_indicadores

router = APIRouter(prefix="/charts", tags=["Charts"])

# Get dashboard charts endpoint (migrado a UniversalChartSpec)
router.add_api_route("/dashboard", get_dashboard_charts, methods=["GET"])

# Get indicadores/metrics endpoint
router.add_api_route("/indicadores", get_indicadores, methods=["GET"])

# Include chart spec router (universal chart specification)
router.include_router(chart_spec_router)
