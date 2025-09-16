#!/usr/bin/env python
"""
Seed principal para cargar todos los datos iniciales del sistema.

Uso:
    python -m app.scripts.seed          # Ejecuta todos los seeds
    python -m app.scripts.seed --only strategies  # Solo estrategias
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

import argparse
import logging
import os

from app.scripts.seeds.charts import main as seed_charts
from app.scripts.seeds.strategies import main as seed_strategies
from app.scripts.seeds.seed_departamentos_chubut import main as seed_departamentos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Obtiene la URL de la base de datos desde las variables de entorno."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db"
    )


def run_all_seeds():
    """Ejecuta todos los seeds del sistema."""
    logger.info("🚀 Iniciando carga de datos iniciales...")

    seeds = [
        ("Departamentos Chubut", seed_departamentos),
        ("Estrategias", seed_strategies),
        ("Charts", seed_charts),
    ]

    for name, seed_func in seeds:
        try:
            logger.info(f"📦 Ejecutando seed: {name}")
            # Todos los seeds ahora manejan su propia sesión
            seed_func()
            logger.info(f"✅ {name} completado")
        except Exception as e:
            logger.error(f"❌ Error en {name}: {e}")
            raise
    
    logger.info("✨ Todos los seeds completados exitosamente")


def main():
    """Función principal del seeder."""
    parser = argparse.ArgumentParser(
        description="Seed de datos iniciales del sistema"
    )
    parser.add_argument(
        "--only",
        choices=["departamentos", "strategies", "charts", "all"],
        default="all",
        help="Ejecutar solo un seed específico"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar re-creación de datos (elimina existentes)"
    )
    
    args = parser.parse_args()

    if args.only == "departamentos":
        logger.info("Ejecutando solo seed de departamentos...")
        seed_departamentos()
    elif args.only == "strategies":
        logger.info("Ejecutando solo seed de estrategias...")
        seed_strategies()
    elif args.only == "charts":
        logger.info("Ejecutando solo seed de charts...")
        seed_charts()
    else:
        run_all_seeds()


if __name__ == "__main__":
    main()