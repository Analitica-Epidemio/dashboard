"""Seeds para el sistema de boletines v2."""

# Re-exportar funciones del seeds.py del nivel padre
# (Python prioriza el directorio sobre el archivo con el mismo nombre)
from app.domains.boletines.seeds_module import (
    seed_boletin_sync,
    seed_boletin_template_config,
)

from .secciones_bloques import seed_secciones_y_bloques

__all__ = [
    "seed_secciones_y_bloques",
    "seed_boletin_template_config",
    "seed_boletin_sync",
]
