"""
Dominio de Vigilancia Agregada (Pasiva).

Maneja conteos semanales de establecimientos (datos P26 del SNVS),
a diferencia de vigilancia_nominal que maneja casos individuales.

Datos que maneja:
- CLI_P26: Casos clínicos (ETI, Neumonía, etc.)
- LAB_P26: Estudios de laboratorio (estudiadas + positivas)
- CLI_P26_INT: Internaciones IRA (camas, UTI, ARM)
"""

from app.domains.vigilancia_agregada.constants import (
    EstadoNotificacion,
    OrigenDatosPasivos,
    Sexo,
)
from app.domains.vigilancia_agregada.models import (
    ConteoCamasIRA,
    ConteoCasosClinicos,
    ConteoEstudiosLab,
    NotificacionSemanal,
    RangoEtario,
    TipoCasoEpidemiologicoPasivo,
)

__all__ = [
    # Constants
    "EstadoNotificacion",
    "OrigenDatosPasivos",
    "Sexo",
    # Models
    "NotificacionSemanal",
    "TipoCasoEpidemiologicoPasivo",
    "RangoEtario",
    "ConteoCasosClinicos",
    "ConteoEstudiosLab",
    "ConteoCamasIRA",
]
