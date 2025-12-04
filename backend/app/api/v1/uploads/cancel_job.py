"""
Cancel job endpoint
"""

from fastapi import Depends, status
from fastapi.responses import JSONResponse

from app.core.schemas.response import ErrorDetail, ErrorResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.features.procesamiento_archivos.services import async_service


async def cancel_job(
    job_id: str,
    current_user: User = Depends(RequireAnyRole())
):
    """
    Cancelar un job en progreso.

    **Funcionalidad:**
    - Revoca la task de Celery
    - Marca el job como cancelado
    - Limpia archivos temporales

    **Limitaciones:**
    - Solo jobs en estado `pending` o `in_progress`
    - Jobs completados no se pueden cancelar
    """

    try:
        cancelled = await async_service.cancel_job(job_id)

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
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR", message="Error cancelando job", field=None
            )
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
