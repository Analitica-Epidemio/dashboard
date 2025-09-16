"""
Generate report endpoint
"""

import logging
from datetime import datetime
from fastapi import Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.reports.playwright_generator import playwright_generator
from .schemas import ReportRequest

logger = logging.getLogger(__name__)


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