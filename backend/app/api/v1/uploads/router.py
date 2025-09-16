"""
Uploads router - Async file processing endpoints
"""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.features.procesamiento_archivos.schemas import (
    AsyncJobResponse,
    JobStatusResponse,
)

from .cancel_job import cancel_job
from .get_job_status import get_job_status
from .upload_csv import upload_csv_async

router = APIRouter(prefix="/uploads", tags=["Uploads Async"])

# Upload CSV endpoint
router.add_api_route(
    "/csv",
    upload_csv_async,
    methods=["POST"],
    responses={
        202: {
            "model": SuccessResponse[AsyncJobResponse],
            "description": "Procesamiento asíncrono iniciado",
        },
        400: {"model": ErrorResponse, "description": "Archivo CSV no válido"},
        413: {"model": ErrorResponse, "description": "Archivo muy grande (máx 50MB)"},
    },
)

# Get job status endpoint
router.add_api_route(
    "/jobs/{job_id}/status",
    get_job_status,
    methods=["GET"],
    response_model=SuccessResponse[JobStatusResponse],
    responses={404: {"model": ErrorResponse, "description": "Job no encontrado"}},
)

# Cancel job endpoint
router.add_api_route(
    "/jobs/{job_id}",
    cancel_job,
    methods=["DELETE"],
    responses={
        200: {"description": "Job cancelado exitosamente"},
        404: {
            "model": ErrorResponse,
            "description": "Job no encontrado o ya terminado",
        },
    },
)