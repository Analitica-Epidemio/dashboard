"""
Servicio genérico para gestión de jobs.

Solo contiene gestión del ciclo de vida de jobs.
NO contiene lógica específica de archivos.
"""

import logging
from datetime import datetime
from typing import Optional

from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.domains.jobs.constants import JobPriority, JobStatus
from app.domains.jobs.models import Job
from app.domains.jobs.repositories import job_repository
from app.domains.jobs.schemas import JobStatusResponse

logger = logging.getLogger(__name__)


class JobService:
    """Servicio genérico para gestión de jobs."""

    async def crear_job(
        self,
        tipo_job: str,
        tipo_procesador: str,
        datos_entrada: dict,
        prioridad: JobPriority = JobPriority.NORMAL,
        creado_por: Optional[str] = None,
    ) -> Job:
        """Crear un nuevo job."""
        job = Job(
            job_type=tipo_job,
            processor_type=tipo_procesador,
            input_data=datos_entrada,
            priority=prioridad,
            created_by=creado_por,
        )

        job_creado = await job_repository.create(job)
        logger.info(f"Job creado: {job_creado.id} ({tipo_job}/{tipo_procesador})")
        return job_creado

    async def iniciar_job(self, job: Job) -> Job:
        """Iniciar la ejecución de un job via Celery."""
        from app.domains.jobs.tasks import execute_job

        celery_task = execute_job.delay(job.id)

        job.celery_task_id = celery_task.id
        job.mark_started(celery_task.id)
        await job_repository.update(job)

        logger.info(f"Job {job.id} iniciado con task {celery_task.id}")
        return job

    async def obtener_estado_job(self, job_id: str) -> Optional[JobStatusResponse]:
        """Obtener estado actual de un job."""
        job = await job_repository.get_by_id(job_id)
        if not job:
            return None

        if job.status == JobStatus.IN_PROGRESS and job.celery_task_id:
            await self._sincronizar_con_celery(job)

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
            result_data=job.output_data if job.status == JobStatus.COMPLETED else None,
        )

    async def cancelar_job(self, job_id: str) -> bool:
        """Cancelar un job en progreso."""
        job = await job_repository.get_by_id(job_id)
        if not job or job.is_finished:
            return False

        if job.celery_task_id:
            celery_app.control.revoke(job.celery_task_id, terminate=True)

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        await job_repository.update(job)

        logger.info(f"Job cancelado: {job_id}")
        return True

    async def _sincronizar_con_celery(self, job: Job) -> None:
        """Sincronizar estado del job con Celery."""
        if not job.celery_task_id:
            return

        try:
            celery_result = AsyncResult(job.celery_task_id, app=celery_app)

            if celery_result.ready():
                if celery_result.successful():
                    result_data = celery_result.result
                    job.mark_completed(**result_data)
                    await job_repository.update(job)
                else:
                    job.mark_failed(str(celery_result.info))
                    await job_repository.update(job)

            elif celery_result.state == "PROGRESS":
                progress_info = celery_result.info
                if isinstance(progress_info, dict):
                    if "percentage" in progress_info:
                        job.progress_percentage = progress_info["percentage"]
                    if "step" in progress_info:
                        job.current_step = progress_info["step"]
                    await job_repository.update(job)

        except Exception as e:
            logger.error(f"Error sincronizando con Celery para job {job.id}: {str(e)}")


job_service = JobService()
