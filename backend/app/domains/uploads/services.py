"""
Servicios para procesamiento asíncrono de archivos CSV.

Arquitectura moderna sin legacy:
- Async processing con Celery
- Repository pattern para datos
- Status tracking avanzado
- Error handling robusto
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile
from celery.result import AsyncResult
import logging
import traceback

from app.domains.uploads.schemas import JobStatusResponse
from app.domains.uploads.models import ProcessingJob, JobStatus, JobPriority
from app.domains.uploads.repositories import job_repository
from app.core.celery_app import celery_app

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
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def validate_csv_file(self, file: UploadFile) -> None:
        """Validar archivo CSV con límites estrictos."""
        
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande. Máximo: {self.max_file_size / (1024*1024):.0f}MB"
            )
        
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Solo archivos CSV permitidos"
            )
    
    async def start_csv_processing(
        self,
        file: UploadFile,
        original_filename: str,
        sheet_name: str,
        priority: JobPriority = JobPriority.NORMAL
    ) -> ProcessingJob:
        """
        Iniciar procesamiento asíncrono de CSV.
        
        Returns:
            ProcessingJob: Job creado para tracking
        """
        
        logger.info(f"🚀 Starting CSV processing - original_filename: {original_filename}, sheet_name: {sheet_name}")
        
        try:
            # Validaciones previas
            logger.info("🔍 Validating CSV file...")
            self.validate_csv_file(file)
            logger.info("✅ File validation passed")
            
            # Crear job en base de datos
            logger.info("📝 Creating ProcessingJob object...")
            job = ProcessingJob(
                job_type="csv_processing",
                original_filename=original_filename,
                sheet_name=sheet_name,
                priority=priority,
                total_steps=3,  # save -> validate -> process
                job_metadata={
                    "file_size_bytes": getattr(file, 'size', 0),
                    "original_content_type": file.content_type
                }
            )
            logger.info(f"✅ ProcessingJob object created - job_type: {job.job_type}")
            
            # Persistir job
            logger.info("💾 Persisting job to database via job_repository.create...")
            created_job = await job_repository.create(job)
            logger.info(f"✅ Job persisted successfully - job_id: {created_job.id}")
            
            # Guardar archivo temporalmente
            logger.info("📁 Saving temporary file...")
            file_path = await self._save_temp_file(file, created_job.id, sheet_name)
            logger.info(f"✅ File saved to: {file_path}")
            
            created_job.file_path = str(file_path)
            logger.info("💾 Updating job with file_path...")
            await job_repository.update(created_job)
            logger.info("✅ Job updated with file_path")
            
            # Lanzar task asíncrona de Celery
            logger.info("🔥 Importing and launching Celery task...")
            from app.domains.uploads.tasks import process_csv_file
            logger.info("📦 process_csv_file imported successfully")
            
            celery_task = process_csv_file.delay(created_job.id, str(file_path))
            logger.info(f"✅ Celery task launched - task_id: {celery_task.id}")
            
            # Asociar task ID con job
            logger.info("🔗 Associating Celery task ID with job...")
            created_job.celery_task_id = celery_task.id
            created_job.mark_started(celery_task.id)
            await job_repository.update(created_job)
            logger.info(f"✅ Job updated with celery_task_id: {celery_task.id}")
            
            logger.info(f"🎉 CSV processing setup complete - job_id: {created_job.id}")
            return created_job
            
        except Exception as e:
            logger.error(f"💥 Error in start_csv_processing: {str(e)}")
            logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")
            raise
    
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
                "file_path": job.file_path
            } if job.status == JobStatus.COMPLETED else None
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
        self, 
        file: UploadFile, 
        job_id: str, 
        sheet_name: str
    ) -> Path:
        """Guardar archivo temporal para procesamiento."""
        
        # Nombre único para el archivo
        clean_sheet = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{job_id}_{clean_sheet}.csv"
        file_path = self.upload_dir / filename
        
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.debug(f"Archivo temporal guardado: {file_path}")
            return file_path
            
        except Exception as e:
            # Cleanup en caso de error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Error guardando archivo: {str(e)}"
            )
    
    async def _sync_with_celery(self, job: ProcessingJob) -> None:
        """Sincronizar estado del job con Celery."""
        
        if not job.celery_task_id:
            return
        
        try:
            # Obtener resultado de Celery
            celery_result = AsyncResult(job.celery_task_id, app=celery_app)
            
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
            
            elif celery_result.state == 'PROGRESS':
                # Actualizar progreso desde Celery
                progress_info = celery_result.info
                if isinstance(progress_info, dict):
                    if 'percentage' in progress_info:
                        job.progress_percentage = progress_info['percentage']
                    if 'step' in progress_info:
                        job.current_step = progress_info['step']
                    await job_repository.update(job)
                    
        except Exception as e:
            logger.error(f"Error sincronizando con Celery para job {job.id}: {str(e)}")


# Instancia singleton del servicio
async_service = AsyncFileProcessingService()