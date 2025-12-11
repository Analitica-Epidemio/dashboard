"""
Generate report endpoint
100% SERVER-SIDE - Sin Playwright
"""

import io
import logging
from datetime import datetime

from fastapi import Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.reporteria.serverside_pdf_generator import serverside_pdf_generator

from .schemas import ReportRequest

logger = logging.getLogger(__name__)


async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> Response:
    """
    Genera un reporte PDF 100% SERVER-SIDE usando matplotlib + ReportLab
    Sin Playwright - Renderizado completo en el backend
    """
    try:
        logger.info(
            f"Generando reporte PDF SERVER-SIDE para {len(request.combinations)} combinaciones"
        )

        # Solo PDF es soportado
        if request.format.lower() != "pdf":
            raise HTTPException(status_code=400, detail="Solo formato PDF es soportado")

        # Si hay múltiples combinaciones, generar solo la primera por ahora
        # (el endpoint ZIP maneja múltiples combinaciones)
        if len(request.combinations) == 0:
            raise HTTPException(
                status_code=400, detail="No se proporcionaron combinaciones"
            )

        first_combo = request.combinations[0]

        # Generar PDF usando SERVER-SIDE generator
        pdf_content = await serverside_pdf_generator.generate_pdf(
            db=db,
            combination={
                "id": first_combo.id,
                "group_id": first_combo.group_id,
                "group_name": first_combo.group_name,
                "event_ids": first_combo.event_ids,
                "event_names": first_combo.event_names,
                "clasificaciones": getattr(first_combo, "clasificaciones", []),
            },
            date_range=request.date_range,
        )

        # Retornar PDF como respuesta
        filename = (
            f"reporte_epidemiologico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Error generando reporte SERVER-SIDE: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error generando reporte: {str(e)}"
        )
