"""
Get job status endpoint
"""

import logging
from fastapi import Depends, HTTPException, status

from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.uploads.schemas import JobStatusResponse
from app.domains.uploads.services import async_service

logger = logging.getLogger(__name__)


async def get_job_status(
    job_id: str,
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[JobStatusResponse]:
    """
    Obtener estado de un job de procesamiento.

    **Polling endpoint** para seguimiento en tiempo real:
    - Progreso percentage (0-100)
    - Paso actual de procesamiento
    - Errores si los hay
    - Resultado final cuando completa

    **Estados posibles:**
    - `pending`: En cola esperando
    - `in_progress`: Procesando activamente
    - `completed`: Completado exitosamente
    - `failed`: Error en procesamiento
    - `cancelled`: Cancelado por usuario
    """

    logger.info(f"🔍 Getting status for job: {job_id}")

    # Log Redis/Celery status when checking job
    from app.core.celery_app import celery_app
    logger.info(f"🔍 Celery broker for status check: {celery_app.conf.broker_url}")

    job_status = await async_service.get_job_status(job_id)

    if not job_status:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} no encontrado"
        )

    logger.info(f"✅ Job {job_id} found with status: {job_status.status}")
    logger.info(f"📊 Job progress: {job_status.progress_percentage}%")

    return SuccessResponse(data=job_status)