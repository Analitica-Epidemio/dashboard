"""
Get charts disponibles endpoint
"""

from typing import Any, Dict, List, Optional

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.features.dashboard.models import DashboardChart


class ChartDisponibleItem(BaseModel):
    """Modelo para un chart disponible en el catálogo"""

    id: int = Field(..., description="ID del chart")
    codigo: str = Field(..., description="Código único del chart")
    nombre: str = Field(..., description="Nombre del chart")
    descripcion: Optional[str] = Field(None, description="Descripción del chart")
    tipo_visualizacion: str = Field(..., description="Tipo de visualización")
    condiciones: Optional[Dict[str, Any]] = Field(None, description="Condiciones de aplicación")


class ChartsDisponiblesResponse(BaseModel):
    """Response model para charts disponibles"""

    charts: List[ChartDisponibleItem] = Field(..., description="Lista de charts disponibles")
    total: int = Field(..., description="Total de charts disponibles")


async def get_charts_disponibles(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[ChartsDisponiblesResponse]:
    """
    Lista todos los charts disponibles sin procesar datos
    Útil para configuración y preview
    """
    query = select(DashboardChart).where(
        DashboardChart.activo == True
    ).order_by(DashboardChart.orden)

    result = await db.execute(query)
    charts = result.scalars().all()

    charts_list = [
        ChartDisponibleItem(
            id=chart.id,
            codigo=chart.codigo,
            nombre=chart.nombre,
            descripcion=chart.descripcion,
            tipo_visualizacion=chart.tipo_visualizacion,
            condiciones=chart.condiciones_display
        )
        for chart in charts
    ]

    response = ChartsDisponiblesResponse(
        charts=charts_list,
        total=len(charts_list)
    )

    return SuccessResponse(data=response)