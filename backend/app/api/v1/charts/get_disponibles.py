"""
Get available charts endpoint
Retorna lista de charts disponibles desde BD para selector de boletines
"""

import logging
from typing import List

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.dashboard.models import DashboardChart

logger = logging.getLogger(__name__)


class ChartDisponibleItem(BaseModel):
    """Chart disponible para insertar en boletines"""

    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    tipo_visualizacion: str
    funcion_procesamiento: str


class ChartsDisponiblesResponse(BaseModel):
    """Response con lista de charts disponibles"""

    charts: List[ChartDisponibleItem]
    total: int


async def get_charts_disponibles(
    db: AsyncSession = Depends(get_async_session),
    current_user: User | None = RequireAuthOrSignedUrl,
) -> SuccessResponse[ChartsDisponiblesResponse]:
    """
    Obtiene lista de charts disponibles desde BD
    Usado por el selector de charts en el editor de boletines
    """
    # Obtener charts activos de la BD
    query = (
        select(DashboardChart)
        .where(col(DashboardChart.activo).is_(True))
        .order_by(col(DashboardChart.orden))
    )
    result = await db.execute(query)
    charts = result.scalars().all()

    charts_items = [
        ChartDisponibleItem(
            id=chart.id,
            codigo=chart.codigo,
            nombre=chart.nombre,
            descripcion=chart.descripcion,
            tipo_visualizacion=chart.tipo_visualizacion,
            funcion_procesamiento=chart.funcion_procesamiento,
        )
        for chart in charts
        if chart.id is not None
    ]

    response = ChartsDisponiblesResponse(charts=charts_items, total=len(charts_items))

    return SuccessResponse(data=response)
