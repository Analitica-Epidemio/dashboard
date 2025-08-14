# -*- coding: utf-8 -*-
"""
Endpoint Hello World simple para demostrar integración con OpenAPI y React Query.
"""
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas.errors import ErrorResponse

router = APIRouter(prefix="/hello", tags=["Hello World"])


class HelloResponse(BaseModel):
    """Modelo de respuesta para el endpoint Hello World."""
    
    message: str = Field(
        ..., 
        description="Mensaje de saludo",
        example="Hello, World!"
    )
    timestamp: datetime = Field(
        ..., 
        description="Timestamp del servidor",
        example="2024-01-15T10:30:00Z"
    )


@router.get(
    "",
    response_model=HelloResponse,
    summary="Obtener saludo simple",
    description="Retorna un mensaje de saludo simple con timestamp del servidor",
    responses={
        404: {
            "description": "Recurso no encontrado",
            "model": ErrorResponse
        },
        500: {
            "description": "Error interno del servidor",
            "model": ErrorResponse
        }
    }
)
async def get_hello() -> HelloResponse:
    """
    Obtiene un saludo simple del servidor.
    
    Este endpoint demuestra la integración básica con React Query
    y la generación automática de tipos TypeScript desde OpenAPI.
    """
    return HelloResponse(
        message="Hello, World!",
        timestamp=datetime.now()
    )