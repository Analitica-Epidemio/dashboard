"""
Constantes del sistema de salud.

Incluye áreas programáticas y parámetros epidemiológicos.
"""

from .areas_programaticas import (
    AP_DEPARTAMENTOS,
    AP_ESQUEL,
    AP_NORTE,
    AP_SUR,
    AP_TRELEW,
    AREAS_PROGRAMATICAS,
    ESQUEL,
    NORTE,
    POBLACION_AREAS,
    SUR,
    TRELEW,
)
from .parametros_epidemiologicos import (
    AJUSTE_100_HAB,
    AJUSTE_HAB,
    GRUPOS_ETARIOS,
    SIN_DATO,
)

__all__ = [
    "AJUSTE_100_HAB",
    # Parámetros
    "AJUSTE_HAB",
    "AP_DEPARTAMENTOS",
    "AP_ESQUEL",
    "AP_NORTE",
    "AP_SUR",
    "AP_TRELEW",
    "AREAS_PROGRAMATICAS",
    "ESQUEL",
    "GRUPOS_ETARIOS",
    "NORTE",
    "POBLACION_AREAS",
    "SIN_DATO",
    "SUR",
    # Áreas programáticas
    "TRELEW",
]
