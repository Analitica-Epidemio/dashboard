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
from typing import Optional

from app.scripts.seeds.strategies import main as seed_strategies

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_all_seeds():
    """Ejecuta todos los seeds del sistema."""
    logger.info("🚀 Iniciando carga de datos iniciales...")
    
    # Seeds a ejecutar en orden
    seeds = [
        ("Estrategias", seed_strategies),
        # Agregar más seeds aquí cuando se creen:
        # ("Establecimientos", seed_establecimientos),
        # ("Usuarios", seed_usuarios),
    ]
    
    for name, seed_func in seeds:
        try:
            logger.info(f"📦 Ejecutando seed: {name}")
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
        choices=["strategies", "all"],
        default="all",
        help="Ejecutar solo un seed específico"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar re-creación de datos (elimina existentes)"
    )
    
    args = parser.parse_args()
    
    if args.only == "strategies":
        logger.info("Ejecutando solo seed de estrategias...")
        seed_strategies()
    else:
        run_all_seeds()


if __name__ == "__main__":
    main()