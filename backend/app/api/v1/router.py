"""Router principal de la API v1"""

from typing import Any, Dict

from fastapi import APIRouter

from app.api.v1.estrategias import router as estrategias_router
from app.api.v1.eventos import router as eventos_router
from app.api.v1.hello import router as hello_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.tipos_eno import router as tipos_router
from app.api.v1.grupos_eno import router as grupos_router
from app.api.v1.charts import router as charts_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(hello_router)
api_router.include_router(uploads_router)
api_router.include_router(estrategias_router)
api_router.include_router(eventos_router)
api_router.include_router(tipos_router)
api_router.include_router(grupos_router)
api_router.include_router(charts_router)
api_router.include_router(reports_router)


# Endpoint raíz de la API
@api_router.get("/")
async def api_root() -> Dict[str, Any]:
    """Endpoint raíz de la API v1"""
    return {"message": "API v1 funcionando correctamente"}
