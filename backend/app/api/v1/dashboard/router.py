"""
Dashboard router
"""

from fastapi import APIRouter

from .get_departamentos_mapping import get_departamentos_mapping
from .get_mapa_topojson import get_topojson_data, get_topojson_info
from .get_resumen import get_dashboard_resumen

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Get dashboard resumen endpoint
router.add_api_route(
    "/resumen",
    get_dashboard_resumen,
    methods=["GET"]
)

# Get TopoJSON geospatial data with optimizations
router.add_api_route(
    "/mapa/topojson",
    get_topojson_data,
    methods=["GET"],
    response_description="Optimized TopoJSON geospatial data with compression and quantization"
)

# Get TopoJSON metadata and compression statistics
router.add_api_route(
    "/mapa/topojson/info",
    get_topojson_info,
    methods=["GET"],
    response_description="Information about available TopoJSON files and compression ratios"
)

# Get departamentos to INDEC IDs mapping for frontend
router.add_api_route(
    "/mapa/departamentos-mapping",
    get_departamentos_mapping,
    methods=["GET"],
    response_description="Mapping of departamentos to INDEC IDs for TopoJSON feature matching"
)
