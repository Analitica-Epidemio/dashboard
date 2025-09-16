"""
Endpoints para gestión de estrategias de clasificación de eventos epidemiológicos.

Arquitectura moderna:
- Repository pattern
- Async SQLAlchemy
- Validación con Pydantic
- Error handling robusto
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.core.security import RequireAnyRole, RequireSuperadmin
from app.domains.auth.models import User
from app.domains.estrategias.repositories import EventStrategyRepository
from app.domains.estrategias.schemas import (
    AuditLogResponse,
    EventStrategyCreate,
    EventStrategyResponse,
    EventStrategyUpdate,
    StrategyTestRequest,
    StrategyTestResponse,
)
from app.domains.estrategias.services import EventClassificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estrategias", tags=["Estrategias"])


@router.get(
    "/",
    response_model=SuccessResponse[List[EventStrategyResponse]],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)
async def list_strategies(
    active_only: Optional[bool] = None,
    tipo_eno_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[List[EventStrategyResponse]]:
    """
    Listar todas las estrategias de clasificación.

    **Filtros opcionales:**
    - `active_only`: Solo estrategias activas
    - `tipo_eno_id`: Filtrar por tipo de evento específico

    **Returns:** Lista de estrategias con metadatos
    """

    logger.info(
        f"📋 Listing strategies - active_only: {active_only}, tipo_eno_id: {tipo_eno_id}"
    )

    try:
        repo = EventStrategyRepository(db)
        strategies = await repo.get_all(
            active_only=active_only, tipo_eno_id=tipo_eno_id
        )

        strategy_responses = [
            EventStrategyResponse.from_orm(strategy) for strategy in strategies
        ]

        logger.info(f"✅ Found {len(strategy_responses)} strategies")
        return SuccessResponse(data=strategy_responses)

    except Exception as e:
        logger.error(f"💥 Error listing strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estrategias: {str(e)}",
        )


@router.get(
    "/{strategy_id}",
    response_model=SuccessResponse[EventStrategyResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[EventStrategyResponse]:
    """
    Obtener una estrategia específica por ID.

    **Returns:** Estrategia completa con reglas y metadatos
    """

    logger.info(f"🔍 Getting strategy with ID: {strategy_id}")

    try:
        repo = EventStrategyRepository(db)
        strategy = await repo.get_by_id(strategy_id)

        if not strategy:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        strategy_response = EventStrategyResponse.from_orm(strategy)

        logger.info(f"✅ Found strategy: {strategy.name}")
        return SuccessResponse(data=strategy_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error getting strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estrategia: {str(e)}",
        )


@router.post(
    "/",
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
async def create_strategy(
    strategy_data: EventStrategyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin())
) -> SuccessResponse[EventStrategyResponse]:
    """
    Crear nueva estrategia de clasificación.

    **Validaciones:**
    - Nombre único
    - Tipo de evento válido
    - Al menos una regla de clasificación
    - Prioridades de reglas consistentes

    **Returns:** Estrategia creada con ID asignado
    """

    logger.info(f"📝 Creating strategy: {strategy_data.name}")

    try:
        repo = EventStrategyRepository(db)

        # Verificar si ya existe estrategia para este tipo de evento
        existing = await repo.get_by_tipo_eno_id(strategy_data.tipo_eno_id)
        if existing:
            logger.warning(
                f"❌ Strategy already exists for tipo_eno_id: {strategy_data.tipo_eno_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una estrategia para el tipo de evento {strategy_data.tipo_eno_id}",
            )

        # Crear estrategia
        strategy = await repo.create(strategy_data)
        strategy_response = EventStrategyResponse.from_orm(strategy)

        logger.info(f"✅ Strategy created with ID: {strategy.id}")
        return SuccessResponse(data=strategy_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error creating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando estrategia: {str(e)}",
        )


@router.put(
    "/{strategy_id}",
    response_model=SuccessResponse[EventStrategyResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def update_strategy(
    strategy_id: int,
    strategy_data: EventStrategyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin()),
) -> SuccessResponse[EventStrategyResponse]:
    """
    Actualizar estrategia existente.

    **Funcionalidades:**
    - Actualización parcial (solo campos proporcionados)
    - Validación de reglas modificadas
    - Auditoría automática de cambios

    **Returns:** Estrategia actualizada
    """

    logger.info(f"📝 Updating strategy: {strategy_id}")

    try:
        repo = EventStrategyRepository(db)

        # Verificar que existe
        existing = await repo.get_by_id(strategy_id)
        if not existing:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        # Actualizar
        strategy = await repo.update(strategy_id, strategy_data)
        strategy_response = EventStrategyResponse.from_orm(strategy)

        logger.info(f"✅ Strategy updated: {strategy.name}")
        return SuccessResponse(data=strategy_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error updating strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando estrategia: {str(e)}",
        )


@router.delete(
    "/{strategy_id}",
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
async def delete_strategy(
    strategy_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin())
):
    """
    Eliminar estrategia.

    **Restricciones:**
    - No se pueden eliminar estrategias activas (usar force=true para anular)
    - Se eliminan también las reglas asociadas
    - Acción no reversible

    **Parámetros:**
    - `force`: Permitir eliminar estrategias activas
    """

    logger.info(f"🗑️ Deleting strategy: {strategy_id}, force: {force}")

    try:
        repo = EventStrategyRepository(db)

        # Verificar que existe
        existing = await repo.get_by_id(strategy_id)
        if not existing:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        # Verificar si está activa
        if existing.active and not force:
            logger.warning(f"❌ Cannot delete active strategy: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar una estrategia activa. Use force=true para anular.",
            )

        # Eliminar
        await repo.delete(strategy_id)

        logger.info(f"✅ Strategy deleted: {strategy_id}")
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error deleting strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando estrategia: {str(e)}",
        )


@router.post(
    "/{strategy_id}/activate",
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
async def activate_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin())
) -> SuccessResponse[EventStrategyResponse]:
    """
    Activar estrategia.

    **Funcionalidades:**
    - Desactiva automáticamente otras estrategias del mismo evento
    - Valida que la estrategia esté completa
    - Registra cambio en auditoría
    """

    logger.info(f"✅ Activating strategy: {strategy_id}")

    try:
        repo = EventStrategyRepository(db)

        # Verificar que existe
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        # Activar (el repositorio maneja la lógica de desactivar otras)
        activated_strategy = await repo.activate(strategy_id)
        strategy_response = EventStrategyResponse.from_orm(activated_strategy)

        logger.info(f"✅ Strategy activated: {activated_strategy.name}")
        return SuccessResponse(data=strategy_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error activating strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activando estrategia: {str(e)}",
        )


@router.post(
    "/{strategy_id}/test",
    response_model=SuccessResponse[StrategyTestResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        400: {"model": ErrorResponse, "description": "Datos de prueba inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def test_strategy(
    strategy_id: int,
    test_data: StrategyTestRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[StrategyTestResponse]:
    """
    Probar estrategia con datos de ejemplo.

    **Funcionalidades:**
    - Aplica la estrategia a datos CSV de prueba
    - Muestra resultados sin persistir
    - Útil para validar reglas antes de activar

    **Returns:** Resultados de clasificación simulados
    """

    logger.info(f"🧪 Testing strategy: {strategy_id}")

    try:
        repo = EventStrategyRepository(db)
        service = EventClassificationService(db)

        # Verificar que existe
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        # Convertir datos CSV a DataFrame y probar
        import io

        import pandas as pd

        df = pd.read_csv(io.StringIO(test_data.csv_data))
        result_df = await service.test_classification(df, strategy_id)

        # Convertir resultados a respuesta
        test_response = StrategyTestResponse(
            total_rows=len(result_df),
            classified_rows=len(result_df[result_df["clasificacion"] != "todos"]),
            results_preview=result_df.head(10).to_dict("records"),
            classification_summary=result_df["clasificacion"].value_counts().to_dict(),
        )

        logger.info(
            f"✅ Strategy test completed: {test_response.total_rows} rows processed"
        )
        return SuccessResponse(data=test_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error testing strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error probando estrategia: {str(e)}",
        )


@router.get(
    "/{strategy_id}/audit",
    response_model=SuccessResponse[List[AuditLogResponse]],
    responses={
        404: {"model": ErrorResponse, "description": "Estrategia no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def get_strategy_audit_log(
    strategy_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[List[AuditLogResponse]]:
    """
    Obtener historial de auditoría de una estrategia.

    **Returns:** Lista de cambios realizados ordenados por fecha
    """

    logger.info(f"📜 Getting audit log for strategy: {strategy_id}")

    try:
        repo = EventStrategyRepository(db)

        # Verificar que existe
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            logger.warning(f"❌ Strategy not found: {strategy_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia {strategy_id} no encontrada",
            )

        # Obtener log de auditoría
        audit_entries = await repo.get_audit_log(strategy_id, limit=limit)
        audit_responses = [AuditLogResponse.from_orm(entry) for entry in audit_entries]

        logger.info(f"✅ Found {len(audit_responses)} audit entries")
        return SuccessResponse(data=audit_responses)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error getting audit log for strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial de auditoría: {str(e)}",
        )
