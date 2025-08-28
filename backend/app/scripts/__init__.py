"""
Scripts de mantenimiento y carga de datos del sistema.

Módulos disponibles:
- seed: Orquestador principal de seeds
- seeds/: Carpeta con todos los seeds específicos
"""

from app.scripts.seed import main as seed_all
from app.scripts.seeds import seed_strategies

__all__ = ["seed_all", "seed_strategies"]