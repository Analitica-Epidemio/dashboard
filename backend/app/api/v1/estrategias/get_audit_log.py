"""
Get strategy audit log endpoint
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.clasificacion.repositories import EventStrategyRepository
from app.domains.eventos_epidemiologicos.clasificacion.schemas import AuditLogResponse

logger = logging.getLogger(__name__)


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