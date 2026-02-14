"""
Get dashboard charts endpoint
MIGRADO 100% a EspecificacionGraficoUniversal con datos REALES
"""

import logging
from datetime import date

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.charts.schemas import (
    CodigoGrafico,
    EspecificacionGraficoUniversal,
    FiltrosGrafico,
)
from app.domains.charts.services.spec_generator import ChartSpecGenerator
from app.domains.dashboard.conditions import ChartConditionResolver
from app.domains.dashboard.models import DashboardChart

logger = logging.getLogger(__name__)


class DashboardChartsResponse(BaseModel):
    """Response model para charts del dashboard usando EspecificacionGraficoUniversal"""

    charts: list[EspecificacionGraficoUniversal] = Field(
        ..., description="Lista de charts como EspecificacionGraficoUniversal"
    )
    total: int = Field(..., description="Total de charts aplicables")
    filtros_aplicados: FiltrosGrafico = Field(
        ..., description="Filtros que se aplicaron"
    )


# Mapeo de códigos de BD (funcion_procesamiento) → CodigoGrafico canónico
CHART_CODE_MAPPING: dict[str, CodigoGrafico] = {
    "curva_epidemiologica": CodigoGrafico.CASOS_POR_SEMANA,
    "corredor_endemico": CodigoGrafico.CORREDOR_ENDEMICO,
    "piramide_poblacional": CodigoGrafico.PIRAMIDE_EDAD,
    "mapa_geografico": CodigoGrafico.MAPA_CHUBUT,
    "estacionalidad": CodigoGrafico.ESTACIONALIDAD,
    "casos_edad": CodigoGrafico.CASOS_EDAD,
    "distribucion_clasificacion": CodigoGrafico.DISTRIBUCION_CLASIFICACION,
}


async def get_dashboard_charts(
    grupo_id: int | None = Query(None, description="ID del grupo seleccionado"),
    tipo_eno_ids: list[int] | None = Query(
        None, description="IDs de los eventos a filtrar"
    ),
    fecha_desde: date | None = Query(
        None, description="Fecha desde (formato: YYYY-MM-DD)"
    ),
    fecha_hasta: date | None = Query(
        None, description="Fecha hasta (formato: YYYY-MM-DD)"
    ),
    clasificaciones: list[str] | None = Query(
        None, description="Filtrar por clasificaciones estratégicas"
    ),
    provincia_id: int | None = Query(
        None,
        description="Código INDEC de provincia (opcional, si no se envía muestra todas las provincias)",
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user: User | None = RequireAuthOrSignedUrl,
) -> SuccessResponse[DashboardChartsResponse]:
    """
    Obtiene los charts aplicables como EspecificacionGraficoUniversal con datos REALES

    Flujo:
    1. Busca qué charts aplican según las condiciones en BD
    2. Convierte filtros a FiltrosGrafico
    3. Usa ChartSpecGenerator para generar specs con datos REALES
    4. Devuelve EspecificacionGraficoUniversal listo para renderizar
    """

    # Convertir filtros a FiltrosGrafico
    fecha_desde_str: str | None = None
    if fecha_desde is not None:
        fecha_desde_str = fecha_desde.isoformat()

    fecha_hasta_str: str | None = None
    if fecha_hasta is not None:
        fecha_hasta_str = fecha_hasta.isoformat()

    filters = FiltrosGrafico(
        ids_grupo_eno=[grupo_id] if grupo_id else None,
        ids_tipo_eno=tipo_eno_ids,
        clasificacion=clasificaciones,
        id_provincia=[provincia_id] if provincia_id else None,
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str,
    )

    # Preparar filtros para condition resolver (formato viejo)
    filtros_dict = {
        "grupo_id": grupo_id,
        "tipo_eno_ids": tipo_eno_ids,
        "fecha_desde": fecha_desde_str,
        "fecha_hasta": fecha_hasta_str,
        "clasificaciones": clasificaciones,
        "provincia_id": provincia_id,
    }

    # Obtener charts aplicables desde BD
    query = (
        select(DashboardChart)
        .where(col(DashboardChart.activo).is_(True))
        .order_by(col(DashboardChart.orden))
    )
    result = await db.execute(query)
    all_charts = list(result.scalars().all())

    # Resolver condiciones
    condition_resolver = ChartConditionResolver(db)
    charts_config = await condition_resolver.obtener_graficos_aplicables(
        filtros_dict, all_charts
    )

    logger.info(
        f"Charts totales: {len(all_charts)}, Charts aplicables: {len(charts_config)}"
    )

    # Generar specs con datos REALES usando ChartSpecGenerator
    generator = ChartSpecGenerator(db)
    charts_specs = []

    for chart_config in charts_config:
        try:
            # Mapear código de BD a código del generador
            chart_code = CHART_CODE_MAPPING.get(chart_config.funcion_procesamiento)

            if not chart_code:
                logger.warning(
                    f"No hay mapeo para {chart_config.funcion_procesamiento}, saltando..."
                )
                continue

            logger.debug(f"Generando spec para {chart_code}")

            # Generar spec con datos REALES
            spec = await generator.generar_spec(
                codigo_grafico=chart_code,
                filtros=filters,
                configuracion={"height": 400},
            )

            # Actualizar título si viene de BD
            if chart_config.nombre:
                spec.titulo = chart_config.nombre

            # Actualizar descripción si viene de BD
            if chart_config.descripcion:
                spec.descripcion = chart_config.descripcion

            charts_specs.append(spec)

        except Exception as e:
            logger.error(f"Error generando spec para {chart_config.codigo}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise la excepción para que falle de forma visible
            raise

    response = DashboardChartsResponse(
        charts=charts_specs, total=len(charts_specs), filtros_aplicados=filters
    )

    return SuccessResponse(data=response)
