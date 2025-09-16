"""
Endpoint para exportación de eventos epidemiológicos.
"""

import io
import logging
from datetime import date, datetime
from typing import Optional

import pandas as pd
from fastapi import Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def export_eventos(
    # Mismos filtros que el listado
    tipo_eno_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    clasificacion: Optional[str] = None,
    formato: str = Query("csv", description="Formato de exportación (csv/excel)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
):
    """
    Exporta eventos filtrados a CSV o Excel.

    **Limitaciones:**
    - Máximo 10,000 registros por exportación
    - Incluye solo datos básicos (no relaciones completas)
    """

    logger.info(f"📤 Exportando eventos a {formato} - usuario: {current_user.email}")

    try:
        # Reutilizar lógica de filtrado del listado
        # (código similar al endpoint de listado pero sin paginación)

        # Por brevedad, simulamos con datos básicos
        output = io.BytesIO()

        # TODO: Implementar exportación real con pandas
        df = pd.DataFrame(
            {
                "ID Evento": [1, 2, 3],
                "Tipo": ["Dengue", "COVID", "Rabia"],
                "Fecha": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )

        if formato == "csv":
            df.to_csv(output, index=False)
            media_type = "text/csv"
            filename = f"eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            df.to_excel(output, index=False)
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            filename = f"eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        output.seek(0)

        logger.info(f"✅ Exportación completada: {filename}")

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"💥 Error exportando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exportando eventos: {str(e)}",
        )