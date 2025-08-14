# -*- coding: utf-8 -*-
"""Router principal de la API v1"""
from fastapi import APIRouter
from typing import Dict, Any

api_router = APIRouter(prefix="/api/v1")

# api_router.include_router(some_router)

# Endpoint raíz de la API
@api_router.get("/")
async def api_root() -> Dict[str, Any]:
    """Endpoint raíz de la API v1"""
    return {"message": "API v1 funcionando correctamente"}
