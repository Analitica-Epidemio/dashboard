"""
Módulo de boletines epidemiológicos
"""

from app.domains.boletines.constants import TipoBloque, TipoVisualizacion
from app.domains.boletines.models import (
    BoletinBloque,
    BoletinInstance,
    BoletinSeccion,
    BoletinSnippet,
    BoletinTemplate,
    BoletinTemplateConfig,
    CapacidadHospitalaria,
    VirusRespiratorio,
)

__all__ = [
    # Constantes
    "TipoBloque",
    "TipoVisualizacion",
    # Modelos
    "BoletinTemplate",
    "BoletinInstance",
    "BoletinTemplateConfig",
    "BoletinSnippet",
    "CapacidadHospitalaria",
    "VirusRespiratorio",
    "BoletinSeccion",
    "BoletinBloque",
]
