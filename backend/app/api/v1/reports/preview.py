"""
Preview report endpoint
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.charts.get_dashboard import get_dashboard_charts
from app.api.v1.charts.get_indicadores import get_indicadores
from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User

from .schemas import ReportRequest

logger = logging.getLogger(__name__)


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
                db=db,
                current_user=current_user
            )

            # Obtener charts
            charts_data = await get_dashboard_charts(
                grupo_id=combination.group_id,
                evento_id=combination.event_ids[0] if combination.event_ids else None,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                clasificaciones=getattr(combination, 'clasificaciones', None),
                db=db,
                current_user=current_user
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