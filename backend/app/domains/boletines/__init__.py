"""
Módulo de boletines epidemiológicos
"""

from app.domains.boletines.models import (
    BoletinInstance,
    BoletinTemplate,
    BoletinTemplateConfig,
    CapacidadHospitalaria,
    VirusRespiratorio,
)

__all__ = [
    "BoletinTemplate",
    "BoletinInstance",
    "BoletinTemplateConfig",
    "CapacidadHospitalaria",
    "VirusRespiratorio",
]
