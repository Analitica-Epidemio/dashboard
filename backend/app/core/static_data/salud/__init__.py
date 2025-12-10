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
    # Áreas programáticas
    "TRELEW",
    "NORTE",
    "SUR",
    "ESQUEL",
    "AREAS_PROGRAMATICAS",
    "AP_TRELEW",
    "AP_NORTE",
    "AP_SUR",
    "AP_ESQUEL",
    "AP_DEPARTAMENTOS",
    "POBLACION_AREAS",
    # Parámetros
    "AJUSTE_HAB",
    "AJUSTE_100_HAB",
    "GRUPOS_ETARIOS",
    "SIN_DATO",
]
