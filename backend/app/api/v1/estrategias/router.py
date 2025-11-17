"""
Estrategias router - Event classification strategies endpoints
"""

from typing import List

from fastapi import APIRouter, status

from app.core.schemas.response import ErrorResponse, PaginatedResponse, SuccessResponse
from app.domains.eventos_epidemiologicos.clasificacion.schemas import (
    AuditLogResponse,
    EventStrategyResponse,
    StrategyTestResponse,
)

from .activate_strategy import activate_strategy
from .create_strategy import create_strategy
from .delete_strategy import delete_strategy
from .get_audit_log import get_strategy_audit_log
from .get_strategy import get_strategy
from .list_strategies import list_strategies
from .test_strategy import test_strategy
from .update_strategy import update_strategy

router = APIRouter(prefix="/estrategias", tags=["Estrategias"])

# List strategies endpoint
router.add_api_route(
    "/",
    list_strategies,
    methods=["GET"],
    response_model=PaginatedResponse[EventStrategyResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)

# Get strategy endpoint
router.add_api_route(
    "/{strategy_id}",
    get_strategy,
    methods=["GET"],
    response_model=SuccessResponse[EventStrategyResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Create strategy endpoint
router.add_api_route(
    "/",
    create_strategy,
    methods=["POST"],
    response_model=SuccessResponse[EventStrategyResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        409: {
            "model": ErrorResponse,
            "description": "Estrategia ya existe para este tipo de evento",
        },
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Update strategy endpoint
router.add_api_route(
    "/{strategy_id}",
    update_strategy,
    methods=["PUT"],
    response_model=SuccessResponse[EventStrategyResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Delete strategy endpoint
router.add_api_route(
    "/{strategy_id}",
    delete_strategy,
    methods=["DELETE"],
    responses={
        204: {"description": "Estrategia eliminada exitosamente"},
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        409: {
            "model": ErrorResponse,
            "description": "No se puede eliminar estrategia activa",
        },
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Activate strategy endpoint
router.add_api_route(
    "/{strategy_id}/activate",
    activate_strategy,
    methods=["POST"],
    response_model=SuccessResponse[EventStrategyResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        409: {
            "model": ErrorResponse,
            "description": "Ya existe estrategia activa para este evento",
        },
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Test strategy endpoint
router.add_api_route(
    "/{strategy_id}/test",
    test_strategy,
    methods=["POST"],
    response_model=SuccessResponse[StrategyTestResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        400: {"model": ErrorResponse, "description": "Datos de prueba inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# Get audit log endpoint
router.add_api_route(
    "/{strategy_id}/audit",
    get_strategy_audit_log,
    methods=["GET"],
    response_model=SuccessResponse[List[AuditLogResponse]],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)