"""
Get job status endpoint.
"""

import logging

from fastapi import Depends, HTTPException, status

from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.jobs.schemas import JobStatusResponse
from app.domains.jobs.services import job_service

logger = logging.getLogger(__name__)


async def get_job_status_endpoint(
    job_id: str,
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[JobStatusResponse]:
    """Get current status of a processing job."""
    logger.info(f"Getting status for job: {job_id}")

    job_status = await job_service.obtener_estado_job(job_id)

    if not job_status:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} no encontrado"
        )

    logger.info(f"Job {job_id} status: {job_status.status}, progress: {job_status.progress_percentage}%")
    return SuccessResponse(data=job_status)
