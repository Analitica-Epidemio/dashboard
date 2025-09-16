"""
Activate strategy endpoint
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireSuperadmin
from app.domains.autenticacion.models import User
from app.domains.estrategias.repositories import EventStrategyRepository
from app.domains.estrategias.schemas import EventStrategyResponse

logger = logging.getLogger(__name__)


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