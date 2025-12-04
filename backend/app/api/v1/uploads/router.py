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
from .preview_file import preview_uploaded_file
from .process_from_preview import process_file_from_preview
from .upload_csv import upload_csv_async

router = APIRouter(prefix="/uploads", tags=["Uploads Async"])

# Upload CSV endpoint
router.add_api_route(
    "/csv-async",
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

# Preview file endpoint (new modern flow)
router.add_api_route(
    "/preview",
    preview_uploaded_file,
    methods=["POST"],
    responses={
        200: {
            "description": "Preview generado exitosamente",
        },
        400: {"model": ErrorResponse, "description": "Formato de archivo no válido"},
    },
)

# Process from preview endpoint (new modern flow)
router.add_api_route(
    "/process",
    process_file_from_preview,
    methods=["POST"],
    responses={
        200: {
            "model": SuccessResponse[AsyncJobResponse],
            "description": "Procesamiento iniciado",
        },
        404: {"model": ErrorResponse, "description": "Upload ID no encontrado"},
    },
)