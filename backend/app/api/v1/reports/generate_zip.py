"""
Generate ZIP report endpoint
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
from app.domains.reporteria.zip_generator import zip_generator

from .schemas import ReportRequest

logger = logging.getLogger(__name__)


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

        # Generate ZIP with PDFs in parallel (SERVER-SIDE)
        zip_content = await zip_generator.generate_zip_report(
            db=db,
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
