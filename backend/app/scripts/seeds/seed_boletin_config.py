"""
Script para ejecutar el seed de configuración de boletines.
Uso: python -m app.scripts.seeds.seed_boletin_config
"""

import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.boletines.seeds import seed_boletin_template_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Ejecuta el seed de configuración de boletines."""
    logger.info("=" * 70)
    logger.info("SEED: Configuración de Template de Boletines")
    logger.info("=" * 70)

    # Usar sesión síncrona ya que seed_boletin_template_config es sync
    engine = create_engine(str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg2"))
    with Session(engine) as session:
        try:
            seed_boletin_template_config(session)
            logger.info("=" * 70)
            logger.info("✅ Seed completado exitosamente")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"❌ Error ejecutando seed: {e}", exc_info=True)
            raise
    engine.dispose()


if __name__ == "__main__":
    main()
