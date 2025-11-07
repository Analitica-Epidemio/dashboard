"""
Endpoint para obtener estadísticas de geocodificación.
"""

import logging
from typing import Any, Dict

from fastapi import Depends
from sqlalchemy import select
from sqlmodel import Session, func

from app.core.database import get_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.territorio.geografia_models import Domicilio, EstadoGeocodificacion

logger = logging.getLogger(__name__)


async def get_geocoding_stats(
    current_user: User = Depends(RequireAnyRole()),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de geocodificación de domicilios.

    Args:
        current_user: Usuario autenticado
        session: Sesión de base de datos

    Returns:
        Estadísticas detalladas por estado
    """
    # Contar domicilios por estado
    stats_query = (
        select(
            Domicilio.estado_geocodificacion,
            func.count(Domicilio.id).label("count"),
        )
        .group_by(Domicilio.estado_geocodificacion)
    )

    results = session.exec(stats_query).all()

    # Organizar resultados
    stats_by_estado = {
        estado.value: 0 for estado in EstadoGeocodificacion
    }

    total = 0
    for estado, count in results:
        if estado:
            stats_by_estado[estado.value] = count
            total += count

    # Calcular agregados útiles
    geocoded = stats_by_estado.get(EstadoGeocodificacion.GEOCODIFICADO.value, 0)
    pending = (
        stats_by_estado.get(EstadoGeocodificacion.PENDIENTE.value, 0)
        + stats_by_estado.get(EstadoGeocodificacion.EN_COLA.value, 0)
        + stats_by_estado.get(EstadoGeocodificacion.FALLO_TEMPORAL.value, 0)
    )
    failed = stats_by_estado.get(EstadoGeocodificacion.FALLO_PERMANENTE.value, 0)
    not_geocodable = stats_by_estado.get(EstadoGeocodificacion.NO_GEOCODIFICABLE.value, 0)
    processing = stats_by_estado.get(EstadoGeocodificacion.PROCESANDO.value, 0)

    # Calcular porcentaje completado
    percentage_geocoded = (geocoded / total * 100) if total > 0 else 0

    return {
        "total_domicilios": total,
        "geocoded": geocoded,
        "pending": pending,
        "processing": processing,
        "failed": failed,
        "not_geocodable": not_geocodable,
        "percentage_geocoded": round(percentage_geocoded, 2),
        "by_estado": stats_by_estado,
    }
