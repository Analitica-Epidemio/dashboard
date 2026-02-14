"""
Update strategy endpoint
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireSuperadmin
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.clasificacion.repositories import (
    EstrategiaClasificacionRepository,
)
from app.domains.vigilancia_nominal.clasificacion.schemas import (
    EstrategiaClasificacionResponse,
    EstrategiaClasificacionUpdate,
)

logger = logging.getLogger(__name__)


async def update_strategy(
    strategy_id: int,
    strategy_data: EstrategiaClasificacionUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin()),
) -> SuccessResponse[EstrategiaClasificacionResponse]:
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
        repo = EstrategiaClasificacionRepository(db)

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
        strategy_response = EstrategiaClasificacionResponse.model_validate(strategy)

        logger.info(f"✅ Strategy updated: {strategy.name}")
        return SuccessResponse(data=strategy_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error updating strategy {strategy_id}: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando estrategia: {e!s}",
        ) from e
