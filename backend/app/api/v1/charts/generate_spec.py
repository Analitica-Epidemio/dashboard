"""
Generate Chart Spec Endpoints
Genera especificaciones universales de charts con datos REALES de la BD
Estas specs pueden usarse tanto en frontend (renderizado interactivo) como en backend (reportes)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.charts.schemas import SolicitudSpecGrafico, RespuestaSpecGrafico
from app.domains.charts.services.spec_generator import ChartSpecGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/spec", response_model=RespuestaSpecGrafico)
async def generate_chart_spec(
    *,
    db: AsyncSession = Depends(get_async_session),
    request: SolicitudSpecGrafico,
) -> RespuestaSpecGrafico:
    """
    Genera la especificación universal para un chart con datos REALES

    El spec puede ser usado tanto por el frontend (para renderizar interactivamente)
    como por el backend (para generar reportes server-side)
    """
    try:
        generator = ChartSpecGenerator(db)
        spec = await generator.generar_spec(
            codigo_grafico=request.codigo_grafico,
            filtros=request.filtros,
            configuracion=request.configuracion,
        )

        return RespuestaSpecGrafico(
            spec=spec,
            generado_en=spec.generado_en,
        )

    except ValueError as e:
        logger.warning(f"ValueError en generate_chart_spec: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generando chart spec: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generando chart spec: {str(e)}"
        )


@router.get("/available", response_model=list[str])
async def get_available_charts() -> list[str]:
    """
    Retorna la lista de códigos de charts disponibles con datos REALES
    """
    return [
        "casos_por_semana",
        "corredor_endemico",
        "piramide_edad",
        "mapa_chubut",
        "estacionalidad",
        "casos_edad",
        "distribucion_clasificacion",
    ]
