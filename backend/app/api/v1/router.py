"""Router principal de la API v1"""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.v1.agentes.router import router as agentes_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.boletines.router import router as boletines_router
from app.api.v1.charts.router import router as charts_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.api.v1.domicilios.router import router as domicilios_router
from app.api.v1.establecimientos.router import router as establecimientos_router
from app.api.v1.estrategias.router import router as estrategias_router
from app.api.v1.eventos.router import router as eventos_router
from app.api.v1.geocoding.router import router as geocoding_router
from app.api.v1.geografia.router import router as geografia_router
from app.api.v1.grupos_eno.router import router as grupos_router
from app.api.v1.personas.router import router as personas_router
from app.api.v1.reports.router import router as reports_router
from app.api.v1.tipos_eno.router import router as tipos_router
from app.api.v1.uploads.router import router as uploads_router
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(auth_router)
api_router.include_router(uploads_router)
api_router.include_router(geocoding_router)  # Router de geocodificación
api_router.include_router(dashboard_router)
api_router.include_router(domicilios_router)  # Router de domicilios
api_router.include_router(establecimientos_router)  # Router de establecimientos
api_router.include_router(estrategias_router)
api_router.include_router(eventos_router)
api_router.include_router(personas_router)  # Nuevo router de personas
api_router.include_router(tipos_router)
api_router.include_router(grupos_router)
api_router.include_router(charts_router)
api_router.include_router(reports_router)
api_router.include_router(analytics_router)  # Router de analytics
api_router.include_router(boletines_router)  # Router de boletines
api_router.include_router(geografia_router)  # Router de geografía (GeoJSON)
api_router.include_router(agentes_router)  # Router de agentes etiológicos


# Endpoint raíz de la API
@api_router.get("/")
async def api_root(current_user: User = Depends(RequireAnyRole())) -> Dict[str, Any]:
    """Endpoint raíz de la API v1"""
    return {
        "message": "API v1 funcionando correctamente",
        "authenticated_user": current_user.email,
        "version": "1.0.0",
    }
