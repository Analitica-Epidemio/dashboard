"""
Get dashboard charts endpoint
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.features.dashboard.conditions import ChartConditionResolver
from app.features.dashboard.models import DashboardChart
from app.features.dashboard.processors import ChartDataProcessor

logger = logging.getLogger(__name__)


class ChartDataItem(BaseModel):
    """Modelo para un chart individual del dashboard"""

    codigo: str = Field(..., description="Código único del chart")
    nombre: str = Field(..., description="Nombre del chart")
    descripcion: Optional[str] = Field(None, description="Descripción del chart")
    tipo: str = Field(..., description="Tipo de visualización")
    data: Any = Field(..., description="Datos del chart")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuración adicional del chart")


class DashboardChartsResponse(BaseModel):
    """Response model para charts del dashboard"""

    charts: List[ChartDataItem] = Field(..., description="Lista de charts con sus datos")
    total: int = Field(..., description="Total de charts aplicables")
    filtros_aplicados: Dict[str, Any] = Field(..., description="Filtros que se aplicaron")


async def get_dashboard_charts(
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    evento_id: Optional[int] = Query(None, description="ID del evento seleccionado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (formato: YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD)"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[DashboardChartsResponse]:
    """
    Obtiene los charts aplicables y sus datos según los filtros

    Simple:
    1. Busca qué charts aplican según las condiciones
    2. Procesa los datos de cada chart
    3. Devuelve todo listo para renderizar
    """

    # Preparar filtros (convertir fechas a string para el procesador)
    filtros = {
        "grupo_id": grupo_id,
        "evento_id": evento_id,
        "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
        "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        "clasificaciones": clasificaciones
    }

    # Obtener charts aplicables
    query = select(DashboardChart).where(DashboardChart.activo == True).order_by(DashboardChart.orden)
    result = await db.execute(query)
    all_charts = result.scalars().all()

    # Resolver condiciones usando códigos estables
    condition_resolver = ChartConditionResolver(db)
    charts_config = await condition_resolver.get_applicable_charts(filtros, all_charts)

    logger.info(f"Charts totales: {len(all_charts)}, Charts aplicables: {len(charts_config)}")
    if len(charts_config) == 0:
        logger.warning(f"No hay charts aplicables para filtros: {filtros}")

    # Procesar cada chart aplicable
    processor = ChartDataProcessor(db)
    charts_data = []

    for chart_config in charts_config:

        # Procesar datos del chart
        try:
            logger.debug(f"Procesando chart {chart_config.codigo}")
            chart_data = await processor.process_chart(chart_config, filtros)

            charts_data.append(
                ChartDataItem(
                    codigo=chart_config.codigo,
                    nombre=chart_config.nombre,
                    descripcion=chart_config.descripcion,
                    tipo=chart_config.tipo_visualizacion,
                    data=chart_data,
                    config=chart_config.configuracion_chart or {}
                )
            )
        except Exception as e:
            # Log error pero continuar con otros charts
            logger.error(f"Error procesando chart {chart_config.codigo}: {e}")
            logger.error(f"Error tipo: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            continue

    response = DashboardChartsResponse(
        charts=charts_data,
        total=len(charts_data),
        filtros_aplicados=filtros
    )

    return SuccessResponse(data=response)