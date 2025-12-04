"""
Get available date range endpoint - retorna el rango de fechas con datos
"""

import logging
from datetime import date
from typing import Optional

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.eventos.models import Evento

logger = logging.getLogger(__name__)


class DateRangeResponse(BaseModel):
    """Response con el rango de fechas disponibles"""
    fecha_minima: date
    fecha_maxima: date
    total_eventos: int


async def get_date_range(
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[DateRangeResponse]:
    """
    Endpoint para obtener el rango de fechas con datos disponibles.

    Retorna la fecha mínima y máxima de eventos en la base de datos,
    útil para configurar filtros de fecha dinámicamente.
    """

    # Query para obtener min, max y count
    stmt = select(
        func.min(Evento.fecha_minima_evento).label("fecha_min"),
        func.max(Evento.fecha_minima_evento).label("fecha_max"),
        func.count(Evento.id).label("total")
    )

    result = await db.execute(stmt)
    row = result.one()

    if not row.fecha_min or not row.fecha_max:
        # Si no hay datos, retornar fecha actual
        from datetime import date as dt
        today = dt.today()
        return SuccessResponse(data=DateRangeResponse(
            fecha_minima=today,
            fecha_maxima=today,
            total_eventos=0
        ))

    response = DateRangeResponse(
        fecha_minima=row.fecha_min,
        fecha_maxima=row.fecha_max,
        total_eventos=row.total
    )

    logger.info(f"Rango de fechas: {response.fecha_minima} - {response.fecha_maxima} ({response.total_eventos} eventos)")

    return SuccessResponse(data=response)
