"""
Celery tasks para geocodificación de domicilios.

Estrategia:
- Cola dedicada 'geocoding' (baja prioridad)
- Procesamiento en batch (100 domicilios a la vez)
- Rate limiting para respetar límites de API
- Reintentos automáticos con backoff exponencial

Para ejecutar el worker de geocodificación:
    celery -A app.core.celery_app worker -Q geocoding -l info --concurrency=1

O para ejecutar todos los workers:
    celery -A app.core.celery_app worker -Q default,file_processing,geocoding,maintenance -l info

Flujo:
1. Al procesar archivo CSV, se crean Domicilios con estado=PENDIENTE
2. Si ENABLE_GEOCODING=true, se encola task geocode_pending_domicilios
3. Worker de geocoding procesa batches de 100 domicilios
4. Auto-encadenamiento: si quedan más domicilios pendientes, encola siguiente batch
5. Rate limiting: 2 segundos entre batches para respetar límites de Mapbox
"""

import logging
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlmodel import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import engine
from app.core.services.geocoding.sync_geocoding_service import SyncGeocodingService
from app.domains.territorio.geografia_models import Domicilio, EstadoGeocodificacion

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.features.geocoding.tasks.geocode_pending_domicilios",
    bind=True,
    queue="geocoding",
    max_retries=3,
    default_retry_delay=300,  # 5 minutos entre reintentos
)
def geocode_pending_domicilios(self, batch_size: int = 100, max_attempts: int = 3):
    """
    Geocodifica un batch de domicilios pendientes.

    Args:
        batch_size: Número de domicilios a procesar en este batch
        max_attempts: Máximo de intentos permitidos antes de marcar como FALLO_PERMANENTE

    Returns:
        Dict con estadísticas del procesamiento
    """
    if not settings.ENABLE_GEOCODING:
        logger.info("Geocodificación deshabilitada en settings")
        return {
            "processed": 0,
            "geocoded": 0,
            "failed": 0,
            "status": "disabled",
        }

    start_time = datetime.now()
    geocoded_count = 0
    failed_count = 0
    no_geocodificable_count = 0

    with Session(engine) as session:
        # Buscar domicilios pendientes de geocodificar
        stmt = (
            select(Domicilio)
            .where(
                Domicilio.estado_geocodificacion.in_([
                    EstadoGeocodificacion.PENDIENTE,
                    EstadoGeocodificacion.EN_COLA,
                    EstadoGeocodificacion.FALLO_TEMPORAL,
                ])
            )
            .where(Domicilio.intentos_geocodificacion < max_attempts)
            .limit(batch_size)
        )

        domicilios = session.exec(stmt).all()

        if not domicilios:
            logger.info("No hay domicilios pendientes de geocodificar")
            return {
                "processed": 0,
                "geocoded": 0,
                "failed": 0,
                "status": "no_pending",
            }

        logger.info(f"Geocodificando batch de {len(domicilios)} domicilios")

        # Inicializar servicio de geocodificación
        geocoding_service = SyncGeocodingService(session)

        if not geocoding_service.adapter:
            # Marcar todos como DESHABILITADO si no hay adapter configurado
            for domicilio in domicilios:
                domicilio.estado_geocodificacion = EstadoGeocodificacion.DESHABILITADO
                domicilio.ultimo_error_geocodificacion = "Geocodificación deshabilitada - no hay API key configurada"
            session.commit()

            return {
                "processed": len(domicilios),
                "geocoded": 0,
                "failed": 0,
                "no_geocodificable": 0,
                "disabled": len(domicilios),
                "status": "no_api_key",
            }

        # Procesar cada domicilio
        for domicilio in domicilios:
            try:
                # Marcar como PROCESANDO
                domicilio.estado_geocodificacion = EstadoGeocodificacion.PROCESANDO
                domicilio.intentos_geocodificacion += 1
                session.commit()

                # Verificar si tiene datos suficientes
                if not domicilio.calle and not domicilio.numero:
                    domicilio.estado_geocodificacion = EstadoGeocodificacion.NO_GEOCODIFICABLE
                    domicilio.ultimo_error_geocodificacion = "Dirección incompleta: sin calle ni número"
                    session.commit()
                    no_geocodificable_count += 1
                    continue

                # Geocodificar
                result = geocoding_service.geocode_address(
                    calle=domicilio.calle,
                    numero=domicilio.numero,
                    id_localidad_indec=domicilio.id_localidad_indec,
                )

                if result and result.latitud and result.longitud:
                    # Éxito!
                    domicilio.latitud = result.latitud
                    domicilio.longitud = result.longitud
                    domicilio.estado_geocodificacion = EstadoGeocodificacion.GEOCODIFICADO
                    domicilio.proveedor_geocoding = result.proveedor
                    domicilio.confidence_geocoding = result.confidence
                    domicilio.ultimo_error_geocodificacion = None
                    geocoded_count += 1
                    logger.debug(f"Geocodificado domicilio ID {domicilio.id}: {result.latitud}, {result.longitud}")
                else:
                    # No se encontraron resultados
                    if domicilio.intentos_geocodificacion >= max_attempts:
                        domicilio.estado_geocodificacion = EstadoGeocodificacion.FALLO_PERMANENTE
                        domicilio.ultimo_error_geocodificacion = "No se encontraron resultados después de múltiples intentos"
                    else:
                        domicilio.estado_geocodificacion = EstadoGeocodificacion.FALLO_TEMPORAL
                        domicilio.ultimo_error_geocodificacion = "No se encontraron resultados - reintentando más tarde"
                    failed_count += 1

                session.commit()

            except Exception as e:
                logger.error(f"Error geocodificando domicilio ID {domicilio.id}: {e}")

                # Marcar como fallo temporal o permanente según el número de intentos
                if domicilio.intentos_geocodificacion >= max_attempts:
                    domicilio.estado_geocodificacion = EstadoGeocodificacion.FALLO_PERMANENTE
                else:
                    domicilio.estado_geocodificacion = EstadoGeocodificacion.FALLO_TEMPORAL

                domicilio.ultimo_error_geocodificacion = str(e)[:500]  # Limitar longitud
                session.commit()
                failed_count += 1

        # Cerrar servicio
        geocoding_service.close()

    elapsed = (datetime.now() - start_time).total_seconds()
    result = {
        "processed": len(domicilios),
        "geocoded": geocoded_count,
        "failed": failed_count,
        "no_geocodificable": no_geocodificable_count,
        "elapsed_seconds": elapsed,
        "status": "completed",
    }

    logger.info(
        f"Batch geocoding completado: {geocoded_count} éxitos, {failed_count} fallos, "
        f"{no_geocodificable_count} no geocodificables en {elapsed:.2f}s"
    )

    # Si quedan más domicilios pendientes, encolar otro batch
    # (con un pequeño delay para respetar rate limits)
    with Session(engine) as session:
        remaining = session.exec(
            select(Domicilio)
            .where(
                Domicilio.estado_geocodificacion.in_([
                    EstadoGeocodificacion.PENDIENTE,
                    EstadoGeocodificacion.EN_COLA,
                    EstadoGeocodificacion.FALLO_TEMPORAL,
                ])
            )
            .where(Domicilio.intentos_geocodificacion < max_attempts)
            .limit(1)
        ).first()

        if remaining:
            logger.info(f"Encolando siguiente batch de geocodificación...")
            # Encolar con delay de 2 segundos para rate limiting
            geocode_pending_domicilios.apply_async(
                kwargs={"batch_size": batch_size, "max_attempts": max_attempts},
                countdown=2,
            )

    return result
