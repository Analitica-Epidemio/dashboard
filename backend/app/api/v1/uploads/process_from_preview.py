"""
Procesar archivo desde vista previa.

Envía el archivo original directamente a Celery (soporta Excel y CSV).
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.jobs.schemas import AsyncJobResponse
from app.domains.vigilancia_agregada.procesamiento.upload_handler import (
    agregada_upload_handler,
)
from app.domains.vigilancia_nominal.procesamiento.upload_handler import (
    nominal_upload_handler,
)

logger = logging.getLogger(__name__)

# Mismo directorio temporal que la vista previa
DIRECTORIO_UPLOAD_TEMP = Path(tempfile.gettempdir()) / "epidemio_uploads"

# Tipos de archivo soportados
FileType = Literal["NOMINAL", "CLI_P26", "CLI_P26_INT", "LAB_P26"]


class ProcessFromPreviewRequest(BaseModel):
    """Request para procesar un archivo previamente subido."""

    upload_id: str = Field(..., description="ID de subida del endpoint de preview")
    sheet_name: str = Field(..., description="Nombre de la hoja a procesar")
    file_type: str = Field(
        ..., description="Tipo de archivo detectado (NOMINAL, CLI_P26, etc.)"
    )


async def process_file_from_preview(
    request: ProcessFromPreviewRequest, current_user: User = Depends(RequireAnyRole())
):
    """
    Procesar un archivo que fue previamente subido y previsualizado.

    **Flujo:**
    1. Buscar archivo temporal por upload_id
    2. Cargar archivo en memoria (mantiene formato original: Excel o CSV)
    3. Iniciar procesamiento asíncrono con Celery (el procesador maneja ambos formatos)
    4. Limpiar archivo temporal

    **Retorna:** Job ID para seguimiento del progreso

    **Optimización:** ¡Sin conversión Excel→CSV! El procesador lee Excel directamente con calamine (~4x más rápido).
    """

    # Variables de negocio en español
    id_subida = request.upload_id
    nombre_hoja = request.sheet_name

    logger.info(
        f"🚀 Solicitud de procesamiento - id_subida: {id_subida}, "
        f"hoja: {nombre_hoja}, usuario: {current_user.email}"
    )

    # Buscar archivo subido
    archivos_coincidentes = list(DIRECTORIO_UPLOAD_TEMP.glob(f"{id_subida}*"))

    if not archivos_coincidentes:
        logger.error(f"❌ ID de subida no encontrado: {id_subida}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado. El preview pudo haber expirado.",
        )

    ruta_archivo_temp = archivos_coincidentes[0]
    nombre_archivo_original = ruta_archivo_temp.stem  # Get filename without extension

    logger.info(f"📄 Archivo encontrado: {ruta_archivo_temp}")

    try:
        ext_archivo = ruta_archivo_temp.suffix.lower()

        # Preparar archivo para procesamiento (sin conversión innecesaria)
        logger.info(
            f"📊 Preparando archivo para procesamiento - formato: {ext_archivo}"
        )

        # Leer archivo en memoria
        with open(ruta_archivo_temp, "rb") as f:
            contenido_archivo = f.read()

        # Obtener tamaño del archivo
        tamano_archivo = os.path.getsize(ruta_archivo_temp)
        logger.info(f"📊 Tamaño del archivo: {tamano_archivo / (1024 * 1024):.2f} MB")

        # Crear objeto tipo UploadFile
        from io import BytesIO

        from fastapi import UploadFile

        # Mantener el formato original (CSV o Excel)
        if ext_archivo == ".csv":
            nombre_final = f"{nombre_hoja}.csv"
        else:
            nombre_final = f"{nombre_hoja}.xlsx"

        archivo_upload = UploadFile(
            file=BytesIO(contenido_archivo), filename=nombre_final, size=tamano_archivo
        )

        # Iniciar procesamiento asíncrono según tipo de archivo
        tipo_archivo = request.file_type
        logger.info(
            f"🚀 Iniciando job de Celery - tipo: {tipo_archivo}, formato: {ext_archivo}"
        )

        if tipo_archivo == "NOMINAL":
            # Vigilancia nominal
            job = await nominal_upload_handler.iniciar_procesamiento(
                archivo=archivo_upload,
                nombre_archivo=nombre_archivo_original,
                nombre_hoja=nombre_hoja if ext_archivo != ".csv" else None,
            )
        elif tipo_archivo in ("CLI_P26", "CLI_P26_INT", "LAB_P26"):
            # Vigilancia agregada
            # Mapear tipo a tipo_dato del handler
            tipo_dato_map = {
                "CLI_P26": "clinicos",
                "CLI_P26_INT": "camas",
                "LAB_P26": "laboratorio",
            }
            job = await agregada_upload_handler.iniciar_procesamiento(
                archivo=archivo_upload,
                nombre_archivo=nombre_archivo_original,
                tipo_dato=tipo_dato_map[tipo_archivo],  # type: ignore[arg-type]
                nombre_hoja=nombre_hoja if ext_archivo != ".csv" else None,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no soportado: {tipo_archivo}",
            )

        logger.info(f"✅ Job creado - job_id: {job.id}")

        # NO eliminar archivo temporal - permite reintentos sin re-subir
        # El archivo se limpia automáticamente por cleanup_temp_uploads.py cada 24h
        logger.info(
            f"📌 Archivo temporal retenido para posible reintento: {ruta_archivo_temp.name}"
        )

        # Retornar información del job
        datos_respuesta = AsyncJobResponse(
            job_id=job.id,
            status=job.status,
            message=f"Procesamiento iniciado para {nombre_hoja}",
            polling_url=f"/api/v1/uploads/jobs/{job.id}/status",
        )

        return SuccessResponse(data=datos_respuesta)

    except KeyError:
        logger.error(f"❌ Hoja '{nombre_hoja}' no encontrada en el archivo")
        # Mantener archivo para debugging - se limpia automáticamente
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hoja '{nombre_hoja}' no encontrada en el archivo",
        )

    except Exception as e:
        logger.error(f"❌ Error procesando archivo: {str(e)}", exc_info=True)
        # Mantener archivo para reintentos - se limpia automáticamente
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}",
        )
