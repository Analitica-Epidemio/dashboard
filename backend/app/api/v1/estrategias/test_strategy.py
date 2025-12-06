"""
Test strategy endpoint
"""

import io
import logging

import pandas as pd
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.clasificacion.repositories import (
    EstrategiaClasificacionRepository,
)
from app.domains.vigilancia_nominal.clasificacion.schemas import (
    StrategyTestRequest,
    StrategyTestResponse,
)
from app.domains.vigilancia_nominal.clasificacion.services import (
    EventClassificationService,
)

logger = logging.getLogger(__name__)


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
        repo = EstrategiaClasificacionRepository(db)
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
