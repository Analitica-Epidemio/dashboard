"""
Servicios para procesamiento asíncrono de archivos CSV.

Arquitectura moderna sin legacy:
- Async processing con Celery
- Repository pattern para datos
- Status tracking avanzado
- Error handling robusto
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import magic
from celery.result import AsyncResult
from fastapi import HTTPException, UploadFile

from app.core.celery_app import celery_app
from app.features.procesamiento_archivos.models import (
    JobPriority,
    JobStatus,
    ProcessingJob,
)
from app.features.procesamiento_archivos.repositories import job_repository
from app.features.procesamiento_archivos.schemas import JobStatusResponse

logger = logging.getLogger(__name__)


class AsyncFileProcessingService:
    """
    Servicio moderno para procesamiento asíncrono de archivos.

    Sin código legacy - arquitectura clean:
    - Jobs asíncronos con Celery
    - Status tracking en tiempo real
    - Repository pattern
    - Error handling senior-level
    """

    # MIME types válidos para archivos permitidos
    VALID_MIME_TYPES = {
        "text/csv",
        "text/plain",  # Algunos CSV se detectan como text/plain
        "application/csv",
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    }

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB

    async def validate_file(self, file: UploadFile) -> bytes:
        """
        Validar archivo Excel o CSV con límites estrictos.

        Valida:
        - Tamaño máximo
        - Extensión permitida
        - MIME type real del contenido (magic bytes)

        Returns:
            bytes: Contenido del archivo para evitar leerlo múltiples veces
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

        # Validar extensión
        ext = file.filename.lower()
        if not (ext.endswith(".csv") or ext.endswith(".xlsx") or ext.endswith(".xls")):
            raise HTTPException(
                status_code=400,
                detail="Solo archivos CSV (.csv) o Excel (.xlsx, .xls) permitidos"
            )

        # Leer contenido para validar tamaño y MIME
        content = await file.read()
        await file.seek(0)  # Reset para uso posterior

        # Validar tamaño
        if len(content) > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande. Máximo: {self.max_file_size / (1024 * 1024):.0f}MB",
            )

        # Validar MIME type real usando magic bytes
        detected_mime = magic.from_buffer(content, mime=True)

        if detected_mime not in self.VALID_MIME_TYPES:
            logger.warning(
                f"MIME type inválido detectado: {detected_mime} para archivo {file.filename}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no válido. MIME detectado: {detected_mime}. "
                       f"Solo se permiten archivos CSV y Excel reales."
            )

        logger.debug(f"Archivo validado: {file.filename}, MIME: {detected_mime}, Size: {len(content)}")
        return content

    async def start_file_processing(
        self,
        file: UploadFile,
        original_filename: str,
        sheet_name: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> ProcessingJob:
        """
        Iniciar procesamiento asíncrono de archivo (CSV o Excel).

        Args:
            file: Archivo a procesar (CSV o Excel)
            original_filename: Nombre original del archivo
            sheet_name: Nombre de la hoja (solo para Excel, None para CSV)
            priority: Prioridad del job

        Returns:
            ProcessingJob: Job creado para tracking
        """

        file_size_mb = getattr(file, "size", 0) / 1024 / 1024
        file_type = "Excel" if file.filename and file.filename.endswith(('.xlsx', '.xls')) else "CSV"
        logger.info(f"Starting {file_type} processing: {original_filename} ({file_size_mb:.1f} MB)")

        try:
            # Validaciones previas (incluye MIME type check)
            await self.validate_file(file)

            # Crear y persistir job
            job = ProcessingJob(
                job_type="csv_processing",
                original_filename=original_filename,
                sheet_name=sheet_name,
                priority=priority,
                total_steps=3,  # save -> validate -> process
                job_metadata={
                    "file_size_bytes": getattr(file, "size", 0),
                    "original_content_type": file.content_type,
                },
            )
            created_job = await job_repository.create(job)

            # Guardar archivo temporalmente
            file_path = await self._save_temp_file(file, created_job.id, sheet_name)
            created_job.file_path = str(file_path)
            await job_repository.update(created_job)

            # Lanzar task asíncrona de Celery
            from app.features.procesamiento_archivos.tasks import process_csv_file
            celery_task = process_csv_file.delay(created_job.id, str(file_path))

            # Asociar task ID con job
            created_job.celery_task_id = celery_task.id
            created_job.mark_started(celery_task.id)
            await job_repository.update(created_job)

            logger.info(f"Job {created_job.id} enqueued with task {celery_task.id}")
            return created_job

        except Exception as e:
            logger.error(f"Error in start_file_processing: {str(e)}", exc_info=True)
            raise

    async def start_csv_processing(
        self,
        file: UploadFile,
        original_filename: str,
        sheet_name: str,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> ProcessingJob:
        """
        LEGACY: Mantener por backward compatibility.
        Usa start_file_processing internamente.
        """
        return await self.start_file_processing(
            file=file,
            original_filename=original_filename,
            sheet_name=sheet_name,
            priority=priority
        )

    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Obtener estado actual de un job.

        Args:
            job_id: UUID del job

        Returns:
            JobStatusResponse con estado actual
        """

        job = await job_repository.get_by_id(job_id)
        if not job:
            return None

        # Si está en progreso, sincronizar con Celery
        if job.status == JobStatus.IN_PROGRESS and job.celery_task_id:
            await self._sync_with_celery(job)

        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            total_steps=job.total_steps,
            completed_steps=job.completed_steps,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            duration_seconds=job.duration_seconds,
            error_message=job.error_message,
            result_data={
                "total_rows": job.total_rows,
                "columns": job.columns,
                "file_path": job.file_path,
            }
            if job.status == JobStatus.COMPLETED
            else None,
        )

    async def cancel_job(self, job_id: str) -> bool:
        """Cancelar un job en progreso."""

        job = await job_repository.get_by_id(job_id)
        if not job or job.is_finished:
            return False

        # Revocar task de Celery si existe
        if job.celery_task_id:
            celery_app.control.revoke(job.celery_task_id, terminate=True)

        # Marcar como cancelado
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        await job_repository.update(job)

        logger.info(f"Job cancelado: {job_id}")
        return True

    async def _save_temp_file(
        self, file: UploadFile, job_id: str, sheet_name: Optional[str]
    ) -> Path:
        """Guardar archivo temporal con la extensión correcta (CSV o Excel)."""

        # Detectar extensión del archivo original
        original_ext = Path(file.filename).suffix.lower() if file.filename else '.csv'

        # Nombre único para el archivo
        if sheet_name:
            clean_sheet = "".join(
                c for c in sheet_name if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            filename = f"{job_id}_{clean_sheet}{original_ext}"
        else:
            filename = f"{job_id}{original_ext}"

        file_path = self.upload_dir / filename

        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            logger.debug(f"Archivo guardado: {file_path} (formato: {original_ext})")
            return file_path

        except Exception as e:
            # Cleanup en caso de error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500, detail=f"Error guardando archivo: {str(e)}"
            )

    async def _sync_with_celery(self, job: ProcessingJob) -> None:
        """Sincronizar estado del job con Celery."""

        if not job.celery_task_id:
            return

        try:
            # Obtener resultado de Celery
            celery_result = AsyncResult(job.celery_task_id, app=celery_app)
            logger.debug(f"Syncing job {job.id}: Celery state={celery_result.state}, ready={celery_result.ready()}")

            if celery_result.ready():
                if celery_result.successful():
                    # Task completada exitosamente
                    result_data = celery_result.result
                    job.mark_completed(**result_data)
                    await job_repository.update(job)
                else:
                    # Task falló
                    error_info = str(celery_result.info)
                    job.mark_failed(error_info)
                    await job_repository.update(job)

            elif celery_result.state == "PROGRESS":
                # Actualizar progreso desde Celery
                progress_info = celery_result.info
                if isinstance(progress_info, dict):
                    if "percentage" in progress_info:
                        job.progress_percentage = progress_info["percentage"]
                    if "step" in progress_info:
                        job.current_step = progress_info["step"]
                    await job_repository.update(job)

        except Exception as e:
            logger.error(f"Error sincronizando con Celery para job {job.id}: {str(e)}")


# Instancia singleton del servicio
async_service = AsyncFileProcessingService()
