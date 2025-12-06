"""
Dominio de Vigilancia Nominal.

Maneja casos epidemiologicos individuales (caso por caso),
a diferencia de vigilancia_agregada que maneja conteos semanales.

Modelos principales:
- Enfermedad: Catalogo de ENO
- GrupoDeEnfermedades: Agrupaciones para reportes
- CasoEpidemiologico: Caso individual notificado
"""

from app.domains.vigilancia_nominal.constants import (
    GravedadEnfermedad,
    ModalidadVigilancia,
)
from app.domains.vigilancia_nominal.models import (
    CasoEpidemiologico,
    CasoGrupoEnfermedad,
    Enfermedad,
    GrupoDeEnfermedades,
    EnfermedadGrupo,
)

__all__ = [
    # Enfermedades (ENO)
    "Enfermedad",
    "GrupoDeEnfermedades",
    "EnfermedadGrupo",
    # Casos
    "CasoEpidemiologico",
    "CasoGrupoEnfermedad",
    # Constants
    "ModalidadVigilancia",
    "GravedadEnfermedad",
]
