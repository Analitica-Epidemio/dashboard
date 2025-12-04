"""
List strategies endpoint
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse, PaginationMeta
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.clasificacion.models import EventStrategy
from app.domains.eventos_epidemiologicos.clasificacion.repositories import (
    EventStrategyRepository,
)
from app.domains.eventos_epidemiologicos.clasificacion.schemas import (
    EventStrategyResponse,
)

logger = logging.getLogger(__name__)


async def list_strategies(
    active_only: Optional[bool] = None,
    tipo_eno_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[EventStrategyResponse]:
    """
    Listar todas las estrategias de clasificación con paginación.

    **Filtros opcionales:**
    - `active_only`: Solo estrategias activas
    - `tipo_eno_id`: Filtrar por tipo de evento específico
    - `page`: Número de página (default: 1)
    - `page_size`: Tamaño de página (default: 50, max: 100)

    **Returns:** Lista paginada de estrategias con metadatos
    """

    logger.info(
        f"📋 Listing strategies - page: {page}, page_size: {page_size}, "
        f"active_only: {active_only}, tipo_eno_id: {tipo_eno_id}"
    )

    try:
        repo = EventStrategyRepository(db)
        skip = (page - 1) * page_size

        # Obtener total count
        count_query = select(func.count(EventStrategy.id))
        if active_only is not None:
            count_query = count_query.where(EventStrategy.is_active == active_only)
        if tipo_eno_id is not None:
            count_query = count_query.where(EventStrategy.tipo_eno_id == tipo_eno_id)

        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Obtener estrategias
        strategies = await repo.get_all(
            active_only=active_only,
            tipo_eno_id=tipo_eno_id,
            skip=skip,
            limit=page_size,
        )

        strategy_responses = [
            EventStrategyResponse.from_orm(strategy) for strategy in strategies
        ]

        # Calcular metadata de paginación
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        logger.info(
            f"✅ Found {len(strategy_responses)} strategies (page {page}/{total_pages}, total: {total})"
        )

        return PaginatedResponse(
            data=strategy_responses,
            meta=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
            ),
        )

    except Exception as e:
        logger.error(f"💥 Error listing strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estrategias: {str(e)}",
        )
