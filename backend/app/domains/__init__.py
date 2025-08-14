"""
Dominios de la aplicación - Arquitectura por dominios cohesivos.

Cada dominio contiene todos los componentes relacionados:
- models.py - Modelos de datos
- repository.py - Acceso a datos
- service.py - Lógica de negocio
"""

# Importar todos los dominios disponibles
from . import (
    ciudadanos,
    diagnosticos,
    establecimientos,
    eventos,
    investigaciones,
    localidades,
    salud,
)

__all__ = [
    "ciudadanos",
    "localidades",
    "eventos",
    "salud",
    "establecimientos",
    "diagnosticos",
    "investigaciones",
]
