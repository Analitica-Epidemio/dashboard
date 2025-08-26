"""
Celery tasks para procesamiento asíncrono de archivos.

Arquitectura senior-level:
- Progress tracking avanzado
- Error handling robusto
- Logging detallado
- Recovery mechanisms
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import traceback
from typing import Dict, Any

from app.core.celery_app import file_processing_task, maintenance_task
from app.domains.uploads.repositories import job_repository
from app.domains.uploads.models import JobStatus

logger = logging.getLogger(__name__)


@file_processing_task(name="app.domains.uploads.tasks.process_csv_file")
def process_csv_file(self, job_id: str, file_path: str) -> Dict[str, Any]:
    """
    Procesar archivo CSV de forma asíncrona.
    
    Args:
        job_id: UUID del job en la base de datos
        file_path: Ruta del archivo CSV a procesar
        
    Returns:
        Dict con resultados del procesamiento
        
    Raises:
        Exception: Si hay errores en el procesamiento
    """
    
    # Configurar contexto de logging
    logger = logging.getLogger(f"{__name__}.{job_id}")
    logger.info(f"Iniciando procesamiento de CSV: {file_path}")
    
    # Variables para tracking
    job = None
    file_path_obj = Path(file_path)
    
    try:
        # PASO 1: Cargar job desde base de datos
        logger.info("Paso 1: Cargando job desde base de datos")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        job = loop.run_until_complete(job_repository.get_by_id(job_id))
        if not job:
            raise Exception(f"Job {job_id} no encontrado en base de datos")
        
        # Actualizar progreso: 10%
        job.update_progress(10, "Iniciando validaciones", increment_completed_steps=True)
        loop.run_until_complete(job_repository.update(job))
        
        # Reportar progreso a Celery
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 10, 'step': 'Iniciando validaciones'}
        )
        
        # PASO 2: Validar archivo
        logger.info("Paso 2: Validando archivo CSV")
        if not file_path_obj.exists():
            raise Exception(f"Archivo no encontrado: {file_path}")
        
        file_size = file_path_obj.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise Exception(f"Archivo muy grande: {file_size / (1024*1024):.2f}MB")
        
        # Actualizar progreso: 25%
        job.update_progress(25, "Leyendo archivo CSV", increment_completed_steps=True)
        loop.run_until_complete(job_repository.update(job))
        
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 25, 'step': 'Leyendo archivo CSV'}
        )
        
        # PASO 3: Procesar CSV con pandas
        logger.info("Paso 3: Procesando CSV con pandas")
        
        # Leer CSV con configuración robusta
        try:
            df = pd.read_csv(
                file_path_obj,
                encoding='utf-8',
                na_filter=True,
                keep_default_na=True,
                dtype=str,  # Leer todo como string inicialmente
                low_memory=False
            )
        except UnicodeDecodeError:
            # Fallback a latin-1 encoding
            logger.warning("Error UTF-8, intentando latin-1")
            df = pd.read_csv(
                file_path_obj,
                encoding='latin-1',
                na_filter=True,
                keep_default_na=True,
                dtype=str,
                low_memory=False
            )
        
        # Actualizar progreso: 50%
        job.update_progress(50, "Validando datos", increment_completed_steps=True)
        loop.run_until_complete(job_repository.update(job))
        
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 50, 'step': 'Validando datos'}
        )
        
        # Obtener información del dataset
        total_rows = len(df)
        columns = df.columns.tolist()
        
        logger.info(f"CSV cargado exitosamente:")
        logger.info(f"  - Filas: {total_rows:,}")
        logger.info(f"  - Columnas: {len(columns)}")
        logger.info(f"  - Tamaño: {file_size / (1024*1024):.2f}MB")
        
        # Validaciones epidemiológicas específicas
        validation_errors = []
        
        # Verificar que no esté vacío
        if total_rows == 0:
            validation_errors.append("Archivo CSV está vacío")
        
        # Verificar columnas mínimas (ejemplo)
        if len(columns) < 3:
            validation_errors.append("Archivo debe tener al menos 3 columnas")
        
        # Verificar filas duplicadas
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            logger.warning(f"Encontradas {duplicates} filas duplicadas")
        
        # Actualizar progreso: 75%
        job.update_progress(75, "Finalizando procesamiento")
        loop.run_until_complete(job_repository.update(job))
        
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 75, 'step': 'Finalizando procesamiento'}
        )
        
        # Construir resultado
        result_data = {
            "total_rows": total_rows,
            "columns": columns,
            "file_path": str(file_path_obj),
            "file_size": file_size,
            "validation_errors": validation_errors,
            "duplicates_found": duplicates,
            "processing_metadata": {
                "pandas_version": pd.__version__,
                "processing_time": datetime.utcnow().isoformat(),
                "encoding_used": "utf-8"  # O latin-1 si fue fallback
            }
        }
        
        # Actualizar progreso: 100%
        job.update_progress(100, "Completado exitosamente")
        loop.run_until_complete(job_repository.update(job))
        
        logger.info(f"Procesamiento completado exitosamente para job {job_id}")
        return result_data
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        logger.error(f"Error procesando CSV para job {job_id}: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        
        # Si tenemos el job, marcarlo como fallido
        if job:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                job.mark_failed(error_msg, error_trace)
                loop.run_until_complete(job_repository.update(job))
            except Exception as update_error:
                logger.error(f"Error actualizando job fallido: {update_error}")
        
        # Re-raise la excepción para que Celery la maneje
        raise e
    
    finally:
        # Cleanup: remover archivo temporal si existe
        try:
            if file_path_obj and file_path_obj.exists():
                file_path_obj.unlink()
                logger.debug(f"Archivo temporal removido: {file_path_obj}")
        except Exception as cleanup_error:
            logger.warning(f"Error removiendo archivo temporal: {cleanup_error}")


@maintenance_task(name="app.domains.uploads.tasks.cleanup_old_files")
def cleanup_old_files() -> Dict[str, Any]:
    """
    Limpiar archivos temporales antiguos.
    
    Returns:
        Dict con estadísticas de limpieza
    """
    
    logger.info("Iniciando limpieza de archivos antiguos")
    
    # Directorio de uploads
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return {"status": "skipped", "reason": "Upload directory not found"}
    
    # Archivos más antiguos que 24 horas
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    cleaned_files = []
    total_size = 0
    
    try:
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                # Verificar si es antiguo
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_time < cutoff_time:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    # Remover archivo
                    file_path.unlink()
                    cleaned_files.append({
                        "name": file_path.name,
                        "size": file_size,
                        "age_hours": (datetime.now() - file_time).total_seconds() / 3600
                    })
        
        result = {
            "status": "completed",
            "files_cleaned": len(cleaned_files),
            "total_size_freed": total_size,
            "files": cleaned_files
        }
        
        logger.info(f"Limpieza completada: {len(cleaned_files)} archivos, {total_size / (1024*1024):.2f}MB liberados")
        return result
        
    except Exception as e:
        error_msg = f"Error en limpieza de archivos: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }


@maintenance_task(name="app.domains.uploads.tasks.cleanup_old_jobs")
def cleanup_old_jobs() -> Dict[str, Any]:
    """
    Limpiar jobs antiguos completados o fallidos.
    
    Returns:
        Dict con estadísticas de limpieza
    """
    
    logger.info("Iniciando limpieza de jobs antiguos")
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Limpiar jobs más antiguos que 7 días
        cleaned_count = loop.run_until_complete(job_repository.cleanup_old_jobs(days_old=7))
        
        result = {
            "status": "completed",
            "jobs_cleaned": cleaned_count
        }
        
        logger.info(f"Limpieza de jobs completada: {cleaned_count} jobs eliminados")
        return result
        
    except Exception as e:
        error_msg = f"Error en limpieza de jobs: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }