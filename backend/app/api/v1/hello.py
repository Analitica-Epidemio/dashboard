"""
Endpoint Hello World siguiendo mejores prácticas de la industria.

Principios:
- Errores estructurados y consistentes
- Códigos de error significativos
- Sin redundancia con HTTP status codes
- Retorno directo de JSONResponse para control total
"""

import random
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.schemas.response import ErrorDetail, ErrorResponse, SuccessResponse

router = APIRouter(prefix="/hello", tags=["Examples"])


class HelloData(BaseModel):
    """Datos del saludo."""

    message: str = Field(..., example="Hello, World!")
    timestamp: datetime = Field(..., example="2024-01-15T10:30:00Z")
    server: str = Field(default="epidemiologia-api", example="epidemiologia-api")


@router.get(
    "",
    responses={
        200: {"model": SuccessResponse[HelloData], "description": "Saludo exitoso"},
        503: {
            "model": ErrorResponse,
            "description": "Servicio temporalmente no disponible",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": "El servicio de saludo está temporalmente no disponible",
                            "field": None,
                        },
                        "request_id": "550e8400-e29b-41d4-a716",
                    }
                }
            },
        },
    },
)
async def get_hello():
    """
    Obtiene un saludo del servidor.

    Implementación CORRECTA con mejores prácticas:
    - JSONResponse directo para control total del status code
    - 50% probabilidad de éxito para testing
    - Errores estructurados con códigos significativos
    - Sin excepciones, retorno directo
    """

    # 50% de probabilidad de error para demostrar manejo de errores
    if random.random() < 0.5:
        # Error: Retornamos JSONResponse con status code correcto
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="El servicio de saludo está temporalmente no disponible",
            ),
            request_id="demo-" + str(datetime.now().timestamp()),
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(),
        )

    # Éxito: Retornamos JSONResponse con status 200
    success_response = SuccessResponse(
        data=HelloData(message="Hello, World!", timestamp=datetime.now())
    )

    # model_dump con mode='json' para serializar datetime correctamente
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=success_response.model_dump(mode="json")
    )
