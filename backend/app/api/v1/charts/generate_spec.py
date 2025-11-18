"""
Generate Chart Spec Endpoints
Genera especificaciones universales de charts con datos REALES de la BD
Estas specs pueden usarse tanto en frontend (renderizado interactivo) como en backend (reportes)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.schemas.chart_spec import ChartSpecRequest, ChartSpecResponse, UniversalChartSpec
from app.services.chart_spec_generator import ChartSpecGenerator

router = APIRouter()


@router.post("/spec", response_model=ChartSpecResponse)
async def generate_chart_spec(
    *,
    db: AsyncSession = Depends(get_async_session),
    request: ChartSpecRequest,
) -> ChartSpecResponse:
    """
    Genera la especificación universal para un chart con datos REALES

    El spec puede ser usado tanto por el frontend (para renderizar interactivamente)
    como por el backend (para generar reportes server-side)
    """
    try:
        generator = ChartSpecGenerator(db)
        spec = await generator.generate_spec(
            chart_code=request.chart_code,
            filters=request.filters,
            config=request.config,
        )

        return ChartSpecResponse(
            spec=spec,
            generated_at=spec.generated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
