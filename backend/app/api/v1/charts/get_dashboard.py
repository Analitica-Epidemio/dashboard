"""
Get dashboard charts endpoint
MIGRADO 100% a UniversalChartSpec con datos REALES
"""

import logging
from datetime import date
from typing import List, Optional

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
from app.schemas.chart_spec import ChartFilters, UniversalChartSpec
from app.services.chart_spec_generator import ChartSpecGenerator

logger = logging.getLogger(__name__)


class DashboardChartsResponse(BaseModel):
    """Response model para charts del dashboard usando UniversalChartSpec"""

    charts: List[UniversalChartSpec] = Field(..., description="Lista de charts como UniversalChartSpec")
    total: int = Field(..., description="Total de charts aplicables")
    filtros_aplicados: ChartFilters = Field(..., description="Filtros que se aplicaron")


# Mapeo de códigos de BD a códigos del generador
CHART_CODE_MAPPING = {
    "curva_epidemiologica": "casos_por_semana",
    "corredor_endemico": "corredor_endemico",
    "piramide_poblacional": "piramide_edad",
    "mapa_geografico": "mapa_chubut",
    "estacionalidad": "estacionalidad",
    "casos_edad": "casos_edad",
    "distribucion_clasificacion": "distribucion_clasificacion",
}


async def get_dashboard_charts(
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    tipo_eno_ids: Optional[List[int]] = Query(None, description="IDs de los eventos a filtrar"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (formato: YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD)"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    provincia_id: Optional[int] = Query(None, description="Código INDEC de provincia (opcional, si no se envía muestra todas las provincias)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[DashboardChartsResponse]:
    """
    Obtiene los charts aplicables como UniversalChartSpec con datos REALES

    Flujo:
    1. Busca qué charts aplican según las condiciones en BD
    2. Convierte filtros a ChartFilters
    3. Usa ChartSpecGenerator para generar specs con datos REALES
    4. Devuelve UniversalChartSpec listo para renderizar
    """

    # Convertir filtros a ChartFilters
    filters = ChartFilters(
        grupo_eno_ids=[grupo_id] if grupo_id else None,
        tipo_eno_ids=tipo_eno_ids,
        clasificacion=clasificaciones,
        provincia_id=[provincia_id] if provincia_id else None,
        fecha_desde=fecha_desde.isoformat() if fecha_desde else None,
        fecha_hasta=fecha_hasta.isoformat() if fecha_hasta else None,
    )

    # Preparar filtros para condition resolver (formato viejo)
    filtros_dict = {
        "grupo_id": grupo_id,
        "tipo_eno_ids": tipo_eno_ids,
        "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
        "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        "clasificaciones": clasificaciones,
        "provincia_id": provincia_id
    }

    # Obtener charts aplicables desde BD
    query = select(DashboardChart).where(DashboardChart.activo == True).order_by(DashboardChart.orden)
    result = await db.execute(query)
    all_charts = result.scalars().all()

    # Resolver condiciones
    condition_resolver = ChartConditionResolver(db)
    charts_config = await condition_resolver.get_applicable_charts(filtros_dict, all_charts)

    logger.info(f"Charts totales: {len(all_charts)}, Charts aplicables: {len(charts_config)}")

    # Generar specs con datos REALES usando ChartSpecGenerator
    generator = ChartSpecGenerator(db)
    charts_specs = []

    for chart_config in charts_config:
        try:
            # Mapear código de BD a código del generador
            chart_code = CHART_CODE_MAPPING.get(chart_config.funcion_procesamiento)

            if not chart_code:
                logger.warning(f"No hay mapeo para {chart_config.funcion_procesamiento}, saltando...")
                continue

            logger.debug(f"Generando spec para {chart_code}")

            # Generar spec con datos REALES
            spec = await generator.generate_spec(
                chart_code=chart_code,
                filters=filters,
                config={"height": 400}
            )

            # Actualizar título si viene de BD
            if chart_config.nombre:
                spec.title = chart_config.nombre

            # Actualizar descripción si viene de BD
            if chart_config.descripcion:
                spec.description = chart_config.descripcion

            charts_specs.append(spec)

        except Exception as e:
            logger.error(f"Error generando spec para {chart_config.codigo}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise la excepción para que falle de forma visible
            raise

    response = DashboardChartsResponse(
        charts=charts_specs,
        total=len(charts_specs),
        filtros_aplicados=filters
    )

    return SuccessResponse(data=response)
