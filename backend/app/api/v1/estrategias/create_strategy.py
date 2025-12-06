"""
Create strategy endpoint
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
    EstrategiaClasificacionCreate,
    EstrategiaClasificacionResponse,
)

logger = logging.getLogger(__name__)


async def create_strategy(
    strategy_data: EstrategiaClasificacionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireSuperadmin())
) -> SuccessResponse[EstrategiaClasificacionResponse]:
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
        repo = EstrategiaClasificacionRepository(db)

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
        strategy_response = EstrategiaClasificacionResponse.from_orm(strategy)

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
