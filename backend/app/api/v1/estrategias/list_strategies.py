"""
List strategies endpoint
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.clasificacion.repositories import EventStrategyRepository
from app.domains.eventos_epidemiologicos.clasificacion.schemas import EventStrategyResponse

logger = logging.getLogger(__name__)


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