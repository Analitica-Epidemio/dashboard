"""
Handler para uploads de vigilancia agregada.

Usa la infraestructura genérica de core/uploads y crea jobs
específicos para procesamiento de datos agregados.

Soporta múltiples tipos de datos agregados.
"""

import logging
from typing import Literal, Optional

from fastapi import UploadFile

from app.core.uploads import file_validator, temp_storage
from app.domains.jobs.constants import JobPriority
from app.domains.jobs.models import Job
from app.domains.jobs.services import job_service

logger = logging.getLogger(__name__)

# Tipos de datos agregados soportados
TipoDatoAgregada = Literal["ira", "clinicos", "laboratorio", "camas"]


class AgregadaUploadHandler:
    """Handler para uploads de vigilancia agregada."""

    PROCESSOR_TYPE = "vigilancia_agregada"

    async def iniciar_procesamiento(
        self,
        archivo: UploadFile,
        nombre_archivo: str,
        tipo_dato: TipoDatoAgregada,
        nombre_hoja: Optional[str] = None,
        prioridad: JobPriority = JobPriority.NORMAL,
    ) -> Job:
        """
        Iniciar procesamiento de archivo de vigilancia agregada.

        Args:
            archivo: Archivo Excel/CSV
            nombre_archivo: Nombre original
            tipo_dato: Tipo de datos agregados (ira, clinicos, etc.)
            nombre_hoja: Hoja a procesar (para Excel)
            prioridad: Prioridad del job

        Returns:
            Job creado y lanzado
        """
        tamano_archivo = getattr(archivo, "size", 0)
        logger.info(f"Procesando agregada [{tipo_dato}]: {nombre_archivo}")

        # Validar archivo
        await file_validator.validar_planilla(archivo)

        # Crear job con tipo de datos específico
        job = await job_service.crear_job(
            tipo_job="file_processing",
            tipo_procesador=self.PROCESSOR_TYPE,
            datos_entrada={
                "nombre_archivo": nombre_archivo,
                "nombre_hoja": nombre_hoja,
                "tipo_dato": tipo_dato,
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

        logger.info(f"Job agregada [{tipo_dato}] {job.id} lanzado")
        return job


# Singleton
agregada_upload_handler = AgregadaUploadHandler()
