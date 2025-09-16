"""
Endpoints modernos para procesamiento asíncrono de archivos.

Arquitectura sin legacy:
- Async processing con Celery
- Job tracking en tiempo real
- Repository pattern
- Error handling senior-level
"""

import logging
import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Depends
from fastapi.responses import JSONResponse

from app.core.schemas.response import ErrorDetail, ErrorResponse, SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.uploads.schemas import AsyncJobResponse, JobStatusResponse
from app.domains.uploads.services import async_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads Async"])


@router.post(
    "/csv",
    responses={
        202: {
            "model": SuccessResponse[AsyncJobResponse],
            "description": "Procesamiento asíncrono iniciado",
        },
        400: {"model": ErrorResponse, "description": "Archivo CSV no válido"},
        413: {"model": ErrorResponse, "description": "Archivo muy grande (máx 50MB)"},
    },
)
async def upload_csv_async(
    file: UploadFile = File(..., description="Archivo CSV epidemiológico"),
    original_filename: str = Form(..., description="Nombre del archivo Excel original"),
    sheet_name: str = Form(..., description="Nombre de la hoja convertida"),
    current_user: User = Depends(RequireAnyRole())
):
    """
    Procesamiento asíncrono de CSV con Celery.

    **Arquitectura moderna:**
    1. Cliente sube CSV convertido desde Excel
    2. Servidor crea job asíncrono
    3. Celery worker procesa en background
    4. Cliente hace polling del estado

    **Ventajas:**
    - No bloquea la UI
    - Procesa archivos grandes sin timeout
    - Progress tracking en tiempo real
    - Error handling robusto

    **Returns:** Job ID para seguimiento del progreso
    """

    logger.info(
        f"📤 Starting CSV upload - filename: {original_filename}, sheet: {sheet_name}, file type: {file.content_type}"
    )
    
    # Log Redis/Celery configuration at request time
    from app.core.celery_app import celery_app
    logger.info(f"🔍 Current Celery broker: {celery_app.conf.broker_url}")
    logger.info(f"🔍 Current Celery backend: {celery_app.conf.result_backend}")
    
    # Test Redis availability
    try:
        import redis
        from app.core.config import settings
        redis_url_parts = settings.REDIS_URL.replace('redis://', '').split(':')
        redis_host = redis_url_parts[0]
        redis_port_db = redis_url_parts[1].split('/')
        redis_port = int(redis_port_db[0])
        redis_db = int(redis_port_db[1]) if len(redis_port_db) > 1 else 0
        
        logger.info(f"🧪 Testing Redis connection to {redis_host}:{redis_port}, DB: {redis_db}")
        redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, socket_connect_timeout=2)
        redis_client.ping()
        logger.info("✅ Redis is accessible from upload endpoint")
    except Exception as redis_error:
        logger.error(f"❌ Redis connection test failed in upload endpoint: {str(redis_error)}")
        logger.error(f"❌ Redis error type: {type(redis_error).__name__}")

    try:
        # Log archivo details
        logger.info(
            f"📄 File details - size: {file.size if hasattr(file, 'size') else 'unknown'} bytes, content_type: {file.content_type}"
        )

        # Iniciar procesamiento asíncrono
        logger.info("🚀 Calling async_service.start_csv_processing")
        job = await async_service.start_csv_processing(
            file=file, original_filename=original_filename, sheet_name=sheet_name
        )

        logger.info(
            f"✅ Job created successfully - job_id: {job.id}, status: {job.status}"
        )

        # Respuesta con job ID
        response_data = AsyncJobResponse(
            job_id=job.id,
            status=job.status,
            message=f"Procesamiento iniciado para {original_filename}",
            polling_url=f"/api/v1/uploads/jobs/{job.id}/status",
        )

        logger.info(f"📤 Returning successful response - job_id: {job.id}")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=SuccessResponse(data=response_data).model_dump(),
        )

    except HTTPException as e:
        logger.warning(
            f"❌ HTTPException in upload_csv_async - status: {e.status_code}, detail: {e.detail}"
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=(
                    "CSV_VALIDATION_ERROR" if e.status_code == 400 else "FILE_TOO_LARGE"
                ),
                message=e.detail,
                field="file",
            )
        )

        return JSONResponse(
            status_code=e.status_code, content=error_response.model_dump()
        )

    except Exception as e:
        logger.error(f"💥 Unexpected error in upload_csv_async: {str(e)}")
        logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")

        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message=f"Error iniciando procesamiento asíncrono: {str(e)}",
                field=None,
            )
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.get(
    "/jobs/{job_id}/status",
    response_model=SuccessResponse[JobStatusResponse],
    responses={404: {"model": ErrorResponse, "description": "Job no encontrado"}},
)
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


@router.delete(
    "/jobs/{job_id}",
    responses={
        200: {"description": "Job cancelado exitosamente"},
        404: {
            "model": ErrorResponse,
            "description": "Job no encontrado o ya terminado",
        },
    },
)
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
