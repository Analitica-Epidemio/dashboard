"""
Process file from preview - send original file directly to Celery (supports Excel & CSV)
"""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.features.procesamiento_archivos.schemas import AsyncJobResponse
from app.features.procesamiento_archivos.services import async_service

logger = logging.getLogger(__name__)

# Same temp directory as preview
TEMP_UPLOAD_DIR = Path(tempfile.gettempdir()) / "epidemio_uploads"


class ProcessFromPreviewRequest(BaseModel):
    """Request to process a previously uploaded file."""
    upload_id: str = Field(..., description="Upload ID from preview endpoint")
    sheet_name: str = Field(..., description="Name of sheet to process")


async def process_file_from_preview(
    request: ProcessFromPreviewRequest,
    current_user: User = Depends(RequireAnyRole())
):
    """
    Process a file that was previously uploaded and previewed.

    **Flow:**
    1. Find temp file by upload_id
    2. Load file into memory (keeps original format: Excel or CSV)
    3. Start async processing with Celery (processor handles both formats)
    4. Clean up temp file

    **Returns:** Job ID for progress tracking

    **Optimization:** No Excel→CSV conversion! Processor reads Excel directly with calamine (~4x faster).
    """

    logger.info(
        f"🚀 Process request - upload_id: {request.upload_id}, "
        f"sheet: {request.sheet_name}, user: {current_user.email}"
    )

    # Find uploaded file
    matching_files = list(TEMP_UPLOAD_DIR.glob(f"{request.upload_id}_*"))

    if not matching_files:
        logger.error(f"❌ Upload ID not found: {request.upload_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado. El preview pudo haber expirado."
        )

    temp_file_path = matching_files[0]
    original_filename = temp_file_path.name.replace(f"{request.upload_id}_", "")

    logger.info(f"📄 Found file: {temp_file_path}")

    try:
        file_ext = temp_file_path.suffix.lower()

        # Preparar archivo para procesamiento (sin conversión innecesaria)
        logger.info(f"📊 Preparing file for processing - format: {file_ext}")

        # Leer archivo en memoria
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()

        # Get file size
        file_size = os.path.getsize(temp_file_path)
        logger.info(f"📊 File size: {file_size / (1024*1024):.2f} MB")

        # Create UploadFile-like object
        from io import BytesIO

        from fastapi import UploadFile

        # Mantener el formato original (CSV o Excel)
        if file_ext == '.csv':
            filename = f"{request.sheet_name}.csv"
        else:
            filename = f"{request.sheet_name}.xlsx"

        upload_file = UploadFile(
            file=BytesIO(file_content),
            filename=filename,
            size=file_size
        )

        # Start async processing (el processor soporta Excel y CSV directamente)
        logger.info(f"🚀 Starting Celery job - will process {file_ext} directly")
        job = await async_service.start_file_processing(
            file=upload_file,
            original_filename=original_filename,
            sheet_name=request.sheet_name if file_ext != '.csv' else None
        )

        logger.info(f"✅ Job created - job_id: {job.id}")

        # NO eliminar archivo temporal - permite reintentos sin re-subir
        # El archivo se limpia automáticamente por cleanup_temp_uploads.py cada 24h
        logger.info(f"📌 Temp file retained for potential retry: {temp_file_path.name}")

        # Return job info
        response_data = AsyncJobResponse(
            job_id=job.id,
            status=job.status,
            message=f"Procesamiento iniciado para {request.sheet_name}",
            polling_url=f"/api/v1/uploads/jobs/{job.id}/status",
        )

        return SuccessResponse(data=response_data)

    except KeyError:
        logger.error(f"❌ Sheet '{request.sheet_name}' not found in file")
        # Mantener archivo para debugging - se limpia automáticamente
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hoja '{request.sheet_name}' no encontrada en el archivo"
        )

    except Exception as e:
        logger.error(f"❌ Error processing file: {str(e)}", exc_info=True)
        # Mantener archivo para reintentos - se limpia automáticamente
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )
