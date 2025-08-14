"""
Constantes del sistema de salud.

Incluye áreas programáticas y parámetros epidemiológicos.
"""

from .areas_programaticas import (
    TRELEW,
    NORTE,
    SUR,
    ESQUEL,
    AREAS_PROGRAMATICAS,
    AP_TRELEW,
    AP_NORTE,
    AP_SUR,
    AP_ESQUEL,
    AP_DEPARTAMENTOS,
    POBLACION_AREAS,
)

from .parametros_epidemiologicos import (
    AJUSTE_HAB,
    AJUSTE_100_HAB,
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
