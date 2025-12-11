"""
Modelos de vigilancia agregada (conteos semanales).
"""

from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal
from app.domains.vigilancia_agregada.models.catalogos import (
    RangoEtario,
    TipoCasoEpidemiologicoPasivo,
)
from app.domains.vigilancia_agregada.models.conteos import (
    ConteoCamasIRA,
    ConteoCasosClinicos,
    ConteoEstudiosLab,
)

__all__ = [
    # Cargas
    "NotificacionSemanal",
    # Catálogos
    "TipoCasoEpidemiologicoPasivo",
    "RangoEtario",
    # Conteos
    "ConteoCasosClinicos",
    "ConteoEstudiosLab",
    "ConteoCamasIRA",
]
