"""
Endpoint para triggear geocodificación manual.
"""

import logging

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlmodel import Session, func

from app.api.v1.geocoding.schemas import TriggerGeocodingResponse
from app.core.config import settings
from app.core.database import get_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.territorio.geografia_models import Domicilio, EstadoGeocodificacion

logger = logging.getLogger(__name__)


async def trigger_geocoding(
    batch_size: int = 500,
    current_user: User = Depends(RequireAnyRole()),
    session: Session = Depends(get_session),
) -> TriggerGeocodingResponse:
    """
    Triggea manualmente la geocodificación de domicilios pendientes.

    Args:
        batch_size: Número de domicilios a procesar por batch (default: 500)
        current_user: Usuario autenticado
        session: Sesión de base de datos

    Returns:
        Estadísticas y task_id de la tarea encolada
    """
    # Contar domicilios pendientes
    logger.info("🔍 [DEBUG] Iniciando conteo de domicilios pendientes...")
    stmt = select(func.count(Domicilio.id)).where(
        Domicilio.estado_geocodificacion.in_(
            [
                EstadoGeocodificacion.PENDIENTE,
                EstadoGeocodificacion.EN_COLA,
                EstadoGeocodificacion.FALLO_TEMPORAL,
            ]
        )
    )
    pending_count_result = session.exec(stmt).one()
    logger.info(
        f"🔍 [DEBUG] Resultado de query (tipo: {type(pending_count_result).__name__}): {pending_count_result}"
    )

    pending_count = pending_count_result[0]  # Extraer el valor del Row
    logger.info(
        f"🔍 [DEBUG] Valor extraído (tipo: {type(pending_count).__name__}): {pending_count}"
    )

    if pending_count == 0:
        return TriggerGeocodingResponse(
            message="No hay domicilios pendientes de geocodificar",
            pending_count=0,
            task_id=None,
        )

    # Encolar tarea de geocodificación
    from app.features.geocoding.tasks import geocode_pending_domicilios

    try:
        task_result = geocode_pending_domicilios.apply_async(
            kwargs={"batch_size": batch_size}, countdown=2
        )

        logger.info(
            f"🗺️  Geocodificación triggeada manualmente por {current_user.email}: "
            f"{pending_count} domicilios pendientes (task_id: {task_result.id})"
        )

        return TriggerGeocodingResponse(
            message=f"Geocodificación iniciada para {pending_count} domicilios",
            pending_count=pending_count,
            task_id=task_result.id,
            batch_size=batch_size,
            estimated_batches=(pending_count + batch_size - 1) // batch_size,
        )

    except Exception as e:
        logger.error(f"Error triggeando geocodificación: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al encolar tarea de geocodificación: {str(e)}",
        )
