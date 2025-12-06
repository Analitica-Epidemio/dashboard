"""
Áreas programáticas de salud de Chubut.

División territorial sanitaria para gestión epidemiológica.
"""

from typing import Dict

from app.core.static_data.geografia.argentina import POBLACION_DEPARTAMENTOS

# NOMBRES DE ÁREAS PROGRAMÁTICAS
TRELEW = "Trelew"
NORTE = "Norte"
SUR = "Comodoro Rivadavia"  # zona sur
ESQUEL = "Esquel"

AREAS_PROGRAMATICAS = [TRELEW, NORTE, SUR, ESQUEL]

# DEPARTAMENTOS POR ÁREA PROGRAMÁTICA
AP_TRELEW = ["RAWSON", "GAIMAN", "FLORENTINO AMEGHINO", "MÁRTIRES", "PASO DE INDIOS"]
AP_NORTE = ["BIEDMA", "TELSEN", "GASTRE"]
AP_SUR = ["ESCALANTE", "SARMIENTO", "RÍO SENGUER"]
AP_ESQUEL = ["FUTALEUFÚ", "CUSHAMEN", "LANGUIÑEO", "TEHUELCHES"]

AP_DEPARTAMENTOS = {TRELEW: AP_TRELEW, NORTE: AP_NORTE, SUR: AP_SUR, ESQUEL: AP_ESQUEL}


# POBLACIÓN POR ÁREA PROGRAMÁTICA (CALCULADA)
def calcular_poblacion_areas() -> Dict[str, int]:
    """Calcula población por área programática."""
    poblaciones = {}
    for area, deptos in AP_DEPARTAMENTOS.items():
        poblaciones[area] = sum(POBLACION_DEPARTAMENTOS.get(d, 0) for d in deptos)
    return poblaciones


POBLACION_AREAS = calcular_poblacion_areas()
