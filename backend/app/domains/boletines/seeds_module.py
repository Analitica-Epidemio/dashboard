"""
Seed de configuración del sistema de boletines epidemiológicos v2.

Este módulo carga las secciones y bloques configurables del boletín
usando el nuevo sistema basado en BD (BoletinSeccion, BoletinBloque).

Estructura basada en el Boletín Epidemiológico Semanal de Chubut SE 40 2025.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.domains.boletines.seeds.secciones_bloques import seed_secciones_y_bloques

logger = logging.getLogger(__name__)


async def seed_boletin_template_config(db: AsyncSession) -> None:
    """
    Crea las secciones y bloques del boletín (sistema v2).

    Este seed reemplaza el sistema anterior de templates JSON hardcodeados
    con tablas de BD editables (boletin_secciones, boletin_bloques).

    Args:
        db: Sesión de base de datos async
    """
    logger.info("=" * 70)
    logger.info("SEED: Sistema de Boletines v2 (Secciones y Bloques)")
    logger.info("=" * 70)

    # El nuevo seed usa sesión síncrona
    # Convertir la sesión async a síncrona para el seed
    sync_session = Session(bind=db.get_bind())

    try:
        seed_secciones_y_bloques(sync_session)  # type: ignore[arg-type]

        logger.info("")
        logger.info("  Secciones creadas (basadas en Boletín Epi Chubut SE 40 2025):")
        logger.info("    1. ENOs más frecuentes (NOMINAL)")
        logger.info("    2. Vigilancia de IRAs:")
        logger.info("       - Corredor ETI (CLI_P26)")
        logger.info("       - Corredor Neumonía (CLI_P26)")
        logger.info("    3. Bronquiolitis:")
        logger.info("       - Corredor Bronquiolitis (CLI_P26)")
        logger.info("       - Distribución por edad (CLI_P26)")
        logger.info("    4. Virus Respiratorios en Internados (NOMINAL)")
        logger.info("    5. Ocupación Hospitalaria (CLI_P26_INT)")
        logger.info("    6. Intoxicación por CO (NOMINAL)")
        logger.info("    7. Vigilancia de Diarreas:")
        logger.info("       - Corredor Diarrea (CLI_P26)")
        logger.info("       - Agentes entéricos (LAB_P26)")
        logger.info("    8. SUH (NOMINAL)")
        logger.info("")
        logger.info("✅ Secciones y bloques del boletín v2 cargados")

    finally:
        sync_session.close()


def seed_boletin_sync(session: Session) -> None:
    """
    Versión síncrona del seed para uso directo.

    Args:
        session: Sesión de base de datos síncrona
    """
    seed_secciones_y_bloques(session)  # type: ignore[arg-type]
