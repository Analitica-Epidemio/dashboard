"""
Get dashboard charts endpoint
"""

import logging
from typing import Any, Dict, List

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.features.dashboard.conditions import ChartConditionResolver
from app.features.dashboard.models import DashboardChart
from app.features.dashboard.processors import ChartDataProcessor

logger = logging.getLogger(__name__)


async def get_dashboard_charts(
    grupo_id: int = Query(None, description="ID del grupo seleccionado"),
    evento_id: int = Query(None, description="ID del evento seleccionado"),
    fecha_desde: str = Query(None, description="Fecha desde"),
    fecha_hasta: str = Query(None, description="Fecha hasta"),
    clasificaciones: List[str] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> Dict[str, Any]:
    """
    Obtiene los charts aplicables y sus datos según los filtros

    Simple:
    1. Busca qué charts aplican según las condiciones
    2. Procesa los datos de cada chart
    3. Devuelve todo listo para renderizar
    """

    # Preparar filtros
    filtros = {
        "grupo_id": grupo_id,
        "evento_id": evento_id,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "clasificaciones": clasificaciones
    }

    # Obtener charts aplicables
    query = select(DashboardChart).where(DashboardChart.activo == True).order_by(DashboardChart.orden)
    result = await db.execute(query)
    all_charts = result.scalars().all()

    # Resolver condiciones usando códigos estables
    condition_resolver = ChartConditionResolver(db)
    charts_config = await condition_resolver.get_applicable_charts(filtros, all_charts)

    # Procesar cada chart aplicable
    processor = ChartDataProcessor(db)
    charts_data = []

    for chart_config in charts_config:

        # Procesar datos del chart
        try:
            logger.debug(f"Procesando chart {chart_config.codigo}")
            chart_data = await processor.process_chart(chart_config, filtros)

            charts_data.append({
                "codigo": chart_config.codigo,
                "nombre": chart_config.nombre,
                "descripcion": chart_config.descripcion,
                "tipo": chart_config.tipo_visualizacion,
                "data": chart_data,
                "config": chart_config.configuracion_chart or {}
            })
        except Exception as e:
            # Log error pero continuar con otros charts
            logger.error(f"Error procesando chart {chart_config.codigo}: {e}")
            continue

    return {
        "charts": charts_data,
        "total": len(charts_data),
        "filtros_aplicados": filtros
    }