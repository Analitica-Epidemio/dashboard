"""
Celery tasks para procesamiento de archivos epidemiológicos.

ENFOQUE SIMPLE: Normalizar, clasificar y guardar en BD.
Sin alertas ni métricas complejas.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from sqlmodel import and_, select

from app.core.celery_app import file_processing_task, maintenance_task
from app.core.database import Session, engine
from app.features.procesamiento_archivos.models import JobStatus, ProcessingJob
from app.features.procesamiento_archivos.processor import create_processor

logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
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


@file_processing_task(name="app.features.procesamiento_archivos.tasks.process_csv_file")
def process_csv_file(self, job_id: str, file_path: str) -> Dict[str, Any]:
    """
    Procesa archivo CSV de forma simple y eficiente.

    OBJETIVO:
    1. Validar y limpiar datos
    2. Clasificar eventos usando estrategias
    3. Normalizar y guardar en BD con bulk operations
    4. Reportar resultados básicos

    Args:
        job_id: ID del job
        file_path: Ruta del archivo

    Returns:
        Resultados básicos del procesamiento
    """
    logger.info(f"Procesando archivo - Job: {job_id}, File: {file_path}")

    job = None
    file_path_obj = Path(file_path)

    try:
        with Session(engine) as session:
            # Cargar job
            statement = select(ProcessingJob).where(ProcessingJob.id == job_id)
            job = session.exec(statement).first()

            if not job:
                raise Exception(f"Job {job_id} no encontrado")

            # El sheet_name está en el campo directo del job
            sheet_name = job.sheet_name

            # Actualizar total_steps basado en las operaciones que se realizarán
            # ~5 pasos iniciales + ~18 operaciones de BD
            job.total_steps = 23
            session.add(job)
            session.commit()

            # Callback de progreso simple
            def update_progress(percentage: int, message: str):
                try:
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

            # Crear procesador simple
            processor = create_processor(session, update_progress)

            # Procesar archivo
            result = processor.process_file(file_path_obj, sheet_name)

            # Preparar datos para el job
            result_data = {
                "file_path": str(file_path),
                "file_size": file_path_obj.stat().st_size
                if file_path_obj.exists()
                else 0,
                "total_rows": result["total_rows"],
                "processed_rows": result["processed_rows"],
                "entities_created": result.get("entities_created", 0),
                "ciudadanos_created": 0,
                "eventos_created": 0,
                "diagnosticos_created": 0,
                "processing_time_seconds": 0,
                "errors": result.get("errors", []),
            }

            # Actualizar job
            if result["status"] == "SUCCESS":
                job.mark_completed(**result_data)
                logger.info(f"Procesamiento exitoso - Job: {job_id}")
            else:
                # Si el procesador falló, la sesión puede estar corrupta
                # Hacer rollback y usar nueva sesión para actualizar el estado
                try:
                    session.rollback()
                except Exception:
                    pass

                # Usar nueva sesión para actualizar el job
                with Session(engine) as new_session:
                    statement = select(ProcessingJob).where(ProcessingJob.id == job_id)
                    job = new_session.exec(statement).first()
                    if job:
                        job.mark_failed(result.get("error", "Error desconocido"), json.dumps(result_data, default=str))
                        new_session.add(job)
                        new_session.commit()
                logger.error(f"Procesamiento falló - Job: {job_id}")
                return convert_numpy_types(result_data)

            session.add(job)
            session.commit()

        return convert_numpy_types(result_data)

    except Exception as e:
        # Rollback de la sesión en caso de error
        try:
            session.rollback()
        except Exception:
            pass
        error_msg = f"Error procesando job {job_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Actualizar job con error
        if job:
            try:
                with Session(engine) as session:
                    statement = select(ProcessingJob).where(ProcessingJob.id == job_id)
                    job = session.exec(statement).first()
                    if job:
                        job.mark_failed(error_msg, json.dumps({"error_type": type(e).__name__}, default=str))
                        session.add(job)
                        session.commit()
            except Exception as session_error:
                logger.error(f"Error updating job status: {session_error}")
                pass

        raise e

    finally:
        # Limpiar archivo temporal
        if file_path_obj.exists():
            try:
                file_path_obj.unlink()
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


@maintenance_task(name="app.features.procesamiento_archivos.tasks.cleanup_old_files")
def cleanup_old_files() -> Dict[str, Any]:
    """Limpia archivos temporales antiguos."""
    logger.info("Limpiando archivos antiguos")

    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return {"status": "skipped", "reason": "Upload directory not found"}

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


@maintenance_task(name="app.features.procesamiento_archivos.tasks.cleanup_old_jobs")
def cleanup_old_jobs() -> Dict[str, Any]:
    """Limpia jobs antiguos según políticas de retención."""
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
                cutoff_time = datetime.utcnow() - retention_time

                query = select(ProcessingJob).where(
                    and_(
                        ProcessingJob.created_at < cutoff_time,
                        ProcessingJob.status == status,
                    )
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


@maintenance_task(name="app.features.procesamiento_archivos.tasks.cleanup_temp_uploads")
def cleanup_temp_uploads() -> Dict[str, Any]:
    """
    Limpia archivos temporales de preview con más de 1 hora de antigüedad.

    Los archivos temporales en /tmp/epidemio_uploads son creados durante
    el proceso de preview de archivos Excel/CSV. Esta tarea los limpia para
    prevenir acumulación de archivos huérfanos.
    """
    from app.scripts.cleanup_temp_uploads import cleanup_old_temp_files

    logger.info("🧹 Iniciando limpieza de archivos temporales de preview")

    try:
        result = cleanup_old_temp_files(max_age_hours=1)

        return {
            "status": "completed",
            "files_cleaned": result["deleted_count"],
            "size_freed_mb": result["deleted_size_mb"],
            "errors": result["errors"]
        }

    except Exception as e:
        logger.error(f"❌ Error limpiando archivos temporales: {e}")
        return {"status": "failed", "error": str(e)}
