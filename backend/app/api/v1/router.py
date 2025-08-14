# -*- coding: utf-8 -*-
"""Router principal de la API v1"""
from fastapi import APIRouter
from typing import Dict, Any

from app.api.v1.hello import router as hello_router

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(hello_router)

# Endpoint raíz de la API
@api_router.get("/")
async def api_root() -> Dict[str, Any]:
    """Endpoint raíz de la API v1"""
    return {"message": "API v1 funcionando correctamente"}
