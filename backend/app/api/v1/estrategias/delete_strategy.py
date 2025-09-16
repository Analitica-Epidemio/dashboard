"""
Delete strategy endpoint
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import RequireSuperadmin
from app.domains.auth.models import User
from app.domains.estrategias.repositories import EventStrategyRepository

logger = logging.getLogger(__name__)


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