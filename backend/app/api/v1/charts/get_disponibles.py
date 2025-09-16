"""
Get charts disponibles endpoint
"""

from typing import Dict, Any, List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.charts.models import DashboardChart


async def get_charts_disponibles(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> List[Dict[str, Any]]:
    """
    Lista todos los charts disponibles sin procesar datos
    Útil para configuración y preview
    """
    query = select(DashboardChart).where(
        DashboardChart.activo == True
    ).order_by(DashboardChart.orden)

    result = await db.execute(query)
    charts = result.scalars().all()

    return [
        {
            "id": chart.id,
            "codigo": chart.codigo,
            "nombre": chart.nombre,
            "descripcion": chart.descripcion,
            "tipo_visualizacion": chart.tipo_visualizacion,
            "condiciones": chart.condiciones_display
        }
        for chart in charts
    ]