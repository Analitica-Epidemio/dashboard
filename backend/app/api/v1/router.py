"""Router principal de la API v1"""

from typing import Any, Dict

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.estrategias import router as estrategias_router
from app.api.v1.eventos import router as eventos_router
from app.api.v1.hello import router as hello_router
from app.api.v1.uploads import router as uploads_router

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(hello_router)
api_router.include_router(uploads_router)
api_router.include_router(estrategias_router)
api_router.include_router(eventos_router)
api_router.include_router(analytics_router)


# Endpoint raíz de la API
@api_router.get("/")
async def api_root() -> Dict[str, Any]:
    """Endpoint raíz de la API v1"""
    return {"message": "API v1 funcionando correctamente"}
