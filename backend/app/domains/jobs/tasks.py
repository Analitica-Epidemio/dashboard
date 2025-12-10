"""
Celery tasks genéricas para el dominio de jobs.

Este módulo contiene:
- Task dispatcher genérico que usa el registry
- Tasks de mantenimiento (limpieza)
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from sqlmodel import and_, col, select

import app.domains.vigilancia_agregada.procesamiento  # noqa: F401

# IMPORTANTE: Importar módulos de procesamiento para registrar processors
import app.domains.vigilancia_nominal.procesamiento  # noqa: F401
from app.core.celery_app import file_processing_task, maintenance_task
from app.core.database import Session, engine
from app.domains.jobs.models import Job, JobStatus
from app.domains.jobs.registry import get_processor

logger = logging.getLogger(__name__)


def convert_numpy_types(obj: Any) -> Any:
    """Convierte tipos numpy/polars a tipos nativos de Python."""
    import numpy as np
    import polars as pl

    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pl.Series):
        return obj.to_list()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif hasattr(obj, "item"):
        try:
            return obj.item()
        except (ValueError, TypeError):
            return str(obj)
    return obj


@file_processing_task(name="app.domains.jobs.tasks.execute_job")
def execute_job(self, job_id: str) -> Dict[str, Any]:
    """
    Task genérica que ejecuta un job usando el processor del registry.
    """
    logger.info(f"Ejecutando job: {job_id}")

    job = None
    ruta_archivo_obj = None

    session = None
    try:
        with Session(engine) as session:
            statement = select(Job).where(col(Job.id) == job_id)
            job = session.exec(statement).first()

            if not job:
                raise Exception(f"Job {job_id} no encontrado")

            processor_type = job.processor_type
            if not processor_type:
                raise Exception(f"Job {job_id} no tiene processor_type definido")

            # Obtener datos de input en español
            ruta_archivo = job.get_input("ruta_archivo")
            nombre_hoja = job.get_input("nombre_hoja")
            file_type = job.get_input("file_type")  # Para agregada

            if not ruta_archivo:
                raise Exception(f"Job {job_id} no tiene ruta_archivo en input_data")

            ruta_archivo_obj = Path(ruta_archivo)

            def update_progress(percentage: int, message: str):
                try:
                    if job is not None:
                        job.update_progress(percentage, message)
                        session.add(job)
                        session.commit()
                        session.refresh(job)
                    self.update_state(
                        state="PROGRESS",
                        meta={"percentage": percentage, "step": message},
                    )
                except Exception as e:
                    logger.warning(f"Error actualizando progreso: {e}")

            processor_factory = get_processor(processor_type)
            processor = processor_factory(session, update_progress)

            # Pasar file_type si está disponible (para vigilancia_agregada)
            if file_type:
                result = processor.procesar_archivo(
                    ruta_archivo_obj,
                    nombre_hoja,
                    file_type=file_type,  # type: ignore[call-arg]
                )
            else:
                result = processor.procesar_archivo(ruta_archivo_obj, nombre_hoja)

            result_data = {
                "ruta_archivo": str(ruta_archivo),
                "tamano_archivo": ruta_archivo_obj.stat().st_size
                if ruta_archivo_obj.exists()
                else 0,
                **result,
            }

            if result.get("status") == "SUCCESS":
                job.mark_completed(**result_data)
                logger.info(f"Job exitoso: {job_id}")
            else:
                try:
                    session.rollback()
                except Exception:
                    pass

                with Session(engine) as new_session:
                    statement = select(Job).where(col(Job.id) == job_id)
                    job = new_session.exec(statement).first()
                    if job:
                        job.mark_failed(
                            result.get("error", "Error desconocido"),
                            json.dumps(result_data, default=str),
                        )
                        new_session.add(job)
                        new_session.commit()
                logger.error(f"Job falló: {job_id}")
                return convert_numpy_types(result_data)

            session.add(job)
            session.commit()

        return convert_numpy_types(result_data)

    except Exception as e:
        try:
            if session is not None:
                session.rollback()
        except Exception:
            pass

        error_msg = f"Error ejecutando job {job_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        if job:
            try:
                with Session(engine) as session:
                    statement = select(Job).where(col(Job.id) == job_id)
                    job = session.exec(statement).first()
                    if job:
                        job.mark_failed(
                            error_msg,
                            json.dumps({"error_type": type(e).__name__}, default=str),
                        )
                        session.add(job)
                        session.commit()
            except Exception as session_error:
                logger.error(f"Error actualizando estado del job: {session_error}")

        raise e

    finally:
        if ruta_archivo_obj and ruta_archivo_obj.exists():
            try:
                ruta_archivo_obj.unlink()
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


@maintenance_task(name="app.domains.jobs.tasks.cleanup_old_jobs")
def cleanup_old_jobs() -> Dict[str, Any]:
    """Limpia jobs antiguos."""
    logger.info("Limpiando jobs antiguos")

    try:
        with Session(engine) as session:
            retention_policies = {
                JobStatus.COMPLETED: timedelta(days=30),
                JobStatus.FAILED: timedelta(days=7),
                JobStatus.CANCELLED: timedelta(days=3),
            }

            total_cleaned = 0

            for status, retention_time in retention_policies.items():
                cutoff_time = datetime.now(timezone.utc) - retention_time
                query = select(Job).where(
                    and_(col(Job.created_at) < cutoff_time, col(Job.status) == status)
                )
                jobs_to_clean = session.exec(query).all()
                for job in jobs_to_clean:
                    session.delete(job)
                    total_cleaned += 1

            session.commit()
            return {"status": "completed", "jobs_cleaned": total_cleaned}

    except Exception as e:
        logger.error(f"Error limpiando jobs: {e}")
        return {"status": "failed", "error": str(e)}


@maintenance_task(name="app.domains.jobs.tasks.cleanup_old_files")
def cleanup_old_files() -> Dict[str, Any]:
    """Limpia archivos temporales antiguos."""
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return {"status": "skipped", "reason": "Directorio de uploads no encontrado"}

    cutoff_time = datetime.now() - timedelta(hours=24)
    cleaned_count = 0
    total_size = 0

    try:
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_count += 1
                    total_size += file_size

        return {
            "status": "completed",
            "files_cleaned": cleaned_count,
            "size_freed_mb": total_size / (1024 * 1024),
        }
    except Exception as e:
        logger.error(f"Error limpiando archivos: {e}")
        return {"status": "failed", "error": str(e)}


@maintenance_task(name="app.domains.jobs.tasks.cleanup_temp_uploads")
def cleanup_temp_uploads() -> Dict[str, Any]:
    """Limpia archivos temporales de preview."""
    from app.scripts.cleanup_temp_uploads import cleanup_old_temp_files

    try:
        result = cleanup_old_temp_files(max_age_hours=1)
        return {
            "status": "completed",
            "files_cleaned": result["deleted_count"],
            "size_freed_mb": result["deleted_size_mb"],
            "errors": result["errors"],
        }
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {e}")
        return {"status": "failed", "error": str(e)}
