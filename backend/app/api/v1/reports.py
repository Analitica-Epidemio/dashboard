"""
API endpoints para generación de reportes
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import io

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.reports.playwright_generator import playwright_generator
from app.domains.reports.zip_generator import zip_generator
from app.api.v1.charts import get_dashboard_charts, get_indicadores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


class FilterCombination(BaseModel):
    """Modelo para una combinación de filtros"""
    id: str
    group_id: int | None = None
    group_name: str | None = None
    event_ids: List[int] = []
    event_names: List[str] = []
    clasificaciones: List[str] | None = None


class ReportRequest(BaseModel):
    """Request para generar un reporte"""
    date_range: Dict[str, str]  # {"from": "2024-01-01", "to": "2024-12-31"}
    combinations: List[FilterCombination]
    format: str = "pdf"  # solo PDF con Playwright



@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> Response:
    """
    Genera un reporte PDF usando Playwright para capturar la página del frontend.
    Esto asegura fidelidad exacta de la UI en los PDFs generados.
    """
    try:
        logger.info(f"Generando reporte PDF con Playwright para {len(request.combinations)} combinaciones")

        # Solo PDF es soportado
        if request.format.lower() != 'pdf':
            raise HTTPException(status_code=400, detail="Solo formato PDF es soportado")

        # Generar PDF usando Playwright
        pdf_content = await playwright_generator.generate_pdf_from_page(
            combinations=[
                {
                    'id': combo.id,
                    'group_id': combo.group_id,
                    'group_name': combo.group_name,
                    'event_ids': combo.event_ids,
                    'event_names': combo.event_names,
                    'clasificaciones': getattr(combo, 'clasificaciones', [])
                }
                for combo in request.combinations
            ],
            date_range=request.date_range
        )

        # Retornar PDF como respuesta
        filename = f"reporte_epidemiologico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generando reporte con Playwright: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")


@router.post("/generate-zip")
async def generate_zip_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> Response:
    """
    Generate ZIP report with multiple PDFs (one per combination) generated in parallel.
    Each PDF contains all charts for that combination.
    """
    try:
        logger.info(f"Generating ZIP report with {len(request.combinations)} combinations")

        if not request.combinations:
            raise HTTPException(status_code=400, detail="No combinations provided")

        # Generate ZIP with PDFs in parallel
        zip_content = await zip_generator.generate_zip_report(
            combinations=[
                {
                    'id': combo.id,
                    'group_id': combo.group_id,
                    'group_name': combo.group_name,
                    'event_ids': combo.event_ids,
                    'event_names': combo.event_names,
                    'clasificaciones': combo.clasificaciones or []
                }
                for combo in request.combinations
            ],
            date_range=request.date_range
        )

        # Return ZIP as response
        filename = f"reporte_epidemiologico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating ZIP report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando reporte ZIP: {str(e)}")


@router.post("/preview")
async def preview_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> Dict[str, Any]:
    """
    Obtiene los datos que se incluirían en el reporte sin generar el PDF
    Útil para preview en el frontend
    """
    try:
        processed_combinations = []

        for combination in request.combinations:
            # Preparar filtros
            fecha_desde = request.date_range.get('from')
            fecha_hasta = request.date_range.get('to')

            # Obtener indicadores
            indicadores_data = await get_indicadores(
                grupo_id=combination.group_id,
                evento_id=combination.event_ids[0] if combination.event_ids else None,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                clasificaciones=getattr(combination, 'clasificaciones', None),
                db=db
            )

            # Obtener charts
            charts_data = await get_dashboard_charts(
                grupo_id=combination.group_id,
                evento_id=combination.event_ids[0] if combination.event_ids else None,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                clasificaciones=getattr(combination, 'clasificaciones', None),
                db=db
            )

            processed_combinations.append({
                "id": combination.id,
                "group_name": combination.group_name,
                "event_names": combination.event_names,
                "indicadores": indicadores_data,
                "charts": charts_data.get('charts', []),
                "total_charts": len(charts_data.get('charts', []))
            })

        return {
            "date_range": request.date_range,
            "combinations": processed_combinations,
            "total_combinations": len(processed_combinations),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en preview de reporte: {e}")
        raise HTTPException(status_code=500, detail=f"Error en preview: {str(e)}")