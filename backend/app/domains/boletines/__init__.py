"""
Módulo de boletines epidemiológicos
"""

from app.domains.boletines.models import (
    BoletinInstance,
    BoletinTemplate,
    QueryDefinition,
)

__all__ = ["BoletinTemplate", "BoletinInstance", "QueryDefinition"]
