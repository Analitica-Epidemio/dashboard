"""
Dashboard router
"""

from fastapi import APIRouter

from .get_resumen import get_dashboard_resumen

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Get dashboard resumen endpoint
router.add_api_route(
    "/resumen",
    get_dashboard_resumen,
    methods=["GET"]
)
