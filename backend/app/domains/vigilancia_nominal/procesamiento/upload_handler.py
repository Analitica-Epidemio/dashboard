"""
Handler para uploads de vigilancia nominal.

Usa la infraestructura genérica de core/uploads y crea jobs
específicos para procesamiento de datos nominales.
"""

import logging
from typing import Optional

from fastapi import UploadFile

from app.core.uploads import file_validator, temp_storage
from app.domains.jobs.constants import JobPriority
from app.domains.jobs.models import Job
from app.domains.jobs.services import job_service

logger = logging.getLogger(__name__)


class NominalUploadHandler:
    """Handler para uploads de vigilancia nominal."""

    PROCESSOR_TYPE = "vigilancia_nominal"

    async def iniciar_procesamiento(
        self,
        archivo: UploadFile,
        nombre_archivo: str,
        nombre_hoja: Optional[str] = None,
        prioridad: JobPriority = JobPriority.NORMAL,
    ) -> Job:
        """
        Iniciar procesamiento de archivo de vigilancia nominal.

        Args:
            archivo: Archivo Excel/CSV
            nombre_archivo: Nombre original
            nombre_hoja: Hoja a procesar (para Excel)
            prioridad: Prioridad del job

        Returns:
            Job creado y lanzado
        """
        tamano_archivo = getattr(archivo, "size", 0)
        logger.info(
            f"Procesando nominal: {nombre_archivo} ({tamano_archivo / 1024 / 1024:.1f} MB)"
        )

        # Validar archivo
        await file_validator.validar_planilla(archivo)

        # Crear job
        job = await job_service.crear_job(
            tipo_job="file_processing",
            tipo_procesador=self.PROCESSOR_TYPE,
            datos_entrada={
                "nombre_archivo": nombre_archivo,
                "nombre_hoja": nombre_hoja,
                "tamano_archivo_bytes": tamano_archivo,
                "tipo_contenido": archivo.content_type,
            },
            prioridad=prioridad,
        )

        # Guardar archivo temporal
        ruta_archivo = await temp_storage.guardar(archivo, job.id, nombre_hoja)
        job.set_input("ruta_archivo", str(ruta_archivo))

        from app.domains.jobs.repositories import job_repository

        await job_repository.update(job)

        # Lanzar job
        job = await job_service.iniciar_job(job)

        logger.info(f"Job nominal {job.id} lanzado")
        return job


# Singleton
nominal_upload_handler = NominalUploadHandler()
