"""
Get strategy endpoint
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.clasificacion.repositories import (
    EventStrategyRepository,
)
from app.domains.eventos_epidemiologicos.clasificacion.schemas import (
    EventStrategyResponse,
)

logger = logging.getLogger(__name__)


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