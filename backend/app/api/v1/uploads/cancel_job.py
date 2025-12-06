"""
Cancel job endpoint.
"""

import logging

from fastapi import Depends, status
from fastapi.responses import JSONResponse

from app.core.schemas.response import ErrorDetail, ErrorResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.jobs.services import job_service

logger = logging.getLogger(__name__)


async def cancel_job_endpoint(
    job_id: str, current_user: User = Depends(RequireAnyRole())
):
    """Cancel a running processing job."""
    try:
        cancelled = await job_service.cancelar_job(job_id)

        if not cancelled:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="JOB_NOT_CANCELLABLE",
                        message=f"Job {job_id} no se puede cancelar (no existe o ya terminó)",
                        field="job_id",
                    )
                ).model_dump(),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Job {job_id} cancelado exitosamente"},
        )

    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="Error cancelando job",
                    field=None,
                )
            ).model_dump(),
        )
