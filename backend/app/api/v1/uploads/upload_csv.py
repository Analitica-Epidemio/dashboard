"""
Endpoint de carga de CSV para procesamiento asíncrono.
"""

import logging
import traceback

from fastapi import Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.schemas.response import ErrorDetail, ErrorResponse, SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.jobs.schemas import AsyncJobResponse
from app.domains.vigilancia_nominal.procesamiento.upload_handler import (
    nominal_upload_handler,
)

logger = logging.getLogger(__name__)


async def upload_csv_async(
    file: UploadFile = File(..., description="Archivo CSV epidemiológico"),
    original_filename: str = Form(..., description="Nombre del archivo Excel original"),
    sheet_name: str = Form(..., description="Nombre de la hoja convertida"),
    current_user: User = Depends(RequireAnyRole()),
):
    """
    Procesamiento asíncrono de CSV con Celery.

    **Arquitectura moderna:**
    1. Cliente sube CSV convertido desde Excel
    2. Servidor crea job asíncrono
    3. Celery worker procesa en background
    4. Cliente hace polling del estado

    **Ventajas:**
    - No bloquea la UI
    - Procesa archivos grandes sin timeout
    - Seguimiento de progreso en tiempo real
    - Manejo de errores robusto

    **Retorna:** Job ID para seguimiento del progreso
    """

    # Renombrar variables de negocio al español
    nombre_archivo = original_filename
    nombre_hoja = sheet_name

    logger.info(
        f"📤 Iniciando carga CSV - archivo: {nombre_archivo}, hoja: {nombre_hoja}, tipo: {file.content_type}"
    )

    # Loguear configuración de Redis/Celery al momento del request
    from app.core.celery_app import celery_app

    logger.info(f"🔍 Broker Celery actual: {celery_app.conf.broker_url}")
    logger.info(f"🔍 Backend Celery actual: {celery_app.conf.result_backend}")

    # Probar disponibilidad de Redis
    try:
        import redis

        from app.core.config import settings

        redis_url_parts = settings.REDIS_URL.replace("redis://", "").split(":")
        redis_host = redis_url_parts[0]
        redis_port_db = redis_url_parts[1].split("/")
        redis_port = int(redis_port_db[0])
        redis_db = int(redis_port_db[1]) if len(redis_port_db) > 1 else 0

        logger.info(
            f"🧪 Probando conexión Redis a {redis_host}:{redis_port}, DB: {redis_db}"
        )
        redis_client = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, socket_connect_timeout=2
        )
        redis_client.ping()
        logger.info("✅ Redis es accesible desde el endpoint de carga")
    except Exception as redis_error:
        logger.error(
            f"❌ Falló prueba de conexión Redis en endpoint: {redis_error!s}"
        )
        logger.error(f"❌ Tipo de error Redis: {type(redis_error).__name__}")

    try:
        # Loguear detalles del archivo
        logger.info(
            f"📄 Detalles del archivo - tamaño: {file.size if hasattr(file, 'size') else 'desconocido'} bytes, tipo_contenido: {file.content_type}"
        )

        # Iniciar procesamiento asíncrono
        logger.info("🚀 Llamando a nominal_upload_handler.iniciar_procesamiento")
        job = await nominal_upload_handler.iniciar_procesamiento(
            archivo=file,
            nombre_archivo=nombre_archivo,
            nombre_hoja=nombre_hoja,
        )

        logger.info(
            f"✅ Job creado exitosamente - job_id: {job.id}, estado: {job.status}"
        )

        # Respuesta con job ID
        datos_respuesta = AsyncJobResponse(
            job_id=job.id,
            status=job.status,
            message=f"Procesamiento iniciado para {nombre_archivo}",
            polling_url=f"/api/v1/uploads/jobs/{job.id}/status",
        )

        logger.info(f"📤 Retornando respuesta exitosa - job_id: {job.id}")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=SuccessResponse(data=datos_respuesta).model_dump(),
        )

    except HTTPException as e:
        logger.warning(
            f"❌ HTTPException en upload_csv_async - status: {e.status_code}, detalle: {e.detail}"
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=(
                    "CSV_VALIDATION_ERROR" if e.status_code == 400 else "FILE_TOO_LARGE"
                ),
                message=e.detail,
                field="file",
            )
        )

        return JSONResponse(
            status_code=e.status_code, content=error_response.model_dump()
        )

    except Exception as e:
        logger.error(f"💥 Error inesperado en upload_csv_async: {e!s}")
        logger.error(f"💥 Traceback completo:\n{traceback.format_exc()}")

        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message=f"Error iniciando procesamiento asíncrono: {e!s}",
                field=None,
            )
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
