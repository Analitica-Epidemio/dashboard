"""Seeds para el sistema de boletines v2."""

# Re-exportar funciones del seeds_module.py del nivel padre
from app.domains.boletines.seeds_module import (
    seed_boletin_sync,
    seed_boletin_template_config,
)

from .secciones_bloques import seed_secciones_y_bloques

__all__ = [
    "seed_boletin_sync",
    "seed_boletin_template_config",
    "seed_secciones_y_bloques",
]
