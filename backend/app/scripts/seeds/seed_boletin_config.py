"""
Script para ejecutar el seed de configuración de boletines.
Uso: python -m app.scripts.seeds.seed_boletin_config
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.database import get_async_session
from app.domains.boletines.seeds import seed_boletin_template_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Ejecuta el seed de configuración de boletines."""
    logger.info("=" * 70)
    logger.info("SEED: Configuración de Template de Boletines")
    logger.info("=" * 70)

    async for db in get_async_session():
        try:
            await seed_boletin_template_config(db)
            logger.info("=" * 70)
            logger.info("✅ Seed completado exitosamente")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"❌ Error ejecutando seed: {e}", exc_info=True)
            raise
        finally:
            break  # Solo queremos una sesión


if __name__ == "__main__":
    asyncio.run(main())
