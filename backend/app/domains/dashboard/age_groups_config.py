"""
Configuración de grupos etarios para análisis epidemiológico

Este módulo define los grupos etarios utilizados en las pirámides poblacionales
y otros análisis por edad. La configuración es flexible y puede ser modificada
según las necesidades del análisis.

Grupos etarios estándar basados en:
- OMS/OPS recomendaciones
- Sistema Nacional de Vigilancia Epidemiológica (SNVS)
- Normativas del Ministerio de Salud de Argentina
"""

from dataclasses import dataclass
from typing import List


@dataclass
class GrupoEdad:
    """Representa un grupo etario"""
    etiqueta: str  # Etiqueta mostrada (ej: "0-4 años", "Neonato")
    edad_minima_anios: float  # Edad mínima en años (puede ser decimal para días/meses)
    edad_maxima_anios: float | None  # Edad máxima en años (None = sin límite superior)
    edad_minima_dias: int | None = None  # Edad mínima en días (para grupos neonatales)
    edad_maxima_dias: int | None = None  # Edad máxima en días (para grupos neonatales)
    descripcion: str = ""  # Descripción opcional del grupo


# =============================================================================
# CONFIGURACIÓN: Grupos Etarios Estándar (Quinquenales)
# =============================================================================

GRUPOS_EDAD_ESTANDAR: List[GrupoEdad] = [
    GrupoEdad(etiqueta="0-4", edad_minima_anios=0, edad_maxima_anios=4, descripcion="Primera infancia"),
    GrupoEdad(etiqueta="5-9", edad_minima_anios=5, edad_maxima_anios=9, descripcion="Niñez temprana"),
    GrupoEdad(etiqueta="10-14", edad_minima_anios=10, edad_maxima_anios=14, descripcion="Niñez tardía/Adolescencia temprana"),
    GrupoEdad(etiqueta="15-19", edad_minima_anios=15, edad_maxima_anios=19, descripcion="Adolescencia"),
    GrupoEdad(etiqueta="20-24", edad_minima_anios=20, edad_maxima_anios=24, descripcion="Adulto joven"),
    GrupoEdad(etiqueta="25-29", edad_minima_anios=25, edad_maxima_anios=29, descripcion="Adulto joven"),
    GrupoEdad(etiqueta="30-34", edad_minima_anios=30, edad_maxima_anios=34, descripcion="Adulto"),
    GrupoEdad(etiqueta="35-39", edad_minima_anios=35, edad_maxima_anios=39, descripcion="Adulto"),
    GrupoEdad(etiqueta="40-44", edad_minima_anios=40, edad_maxima_anios=44, descripcion="Adulto"),
    GrupoEdad(etiqueta="45-49", edad_minima_anios=45, edad_maxima_anios=49, descripcion="Adulto"),
    GrupoEdad(etiqueta="50-54", edad_minima_anios=50, edad_maxima_anios=54, descripcion="Adulto mayor temprano"),
    GrupoEdad(etiqueta="55-59", edad_minima_anios=55, edad_maxima_anios=59, descripcion="Adulto mayor temprano"),
    GrupoEdad(etiqueta="60-64", edad_minima_anios=60, edad_maxima_anios=64, descripcion="Adulto mayor"),
    GrupoEdad(etiqueta="65-69", edad_minima_anios=65, edad_maxima_anios=69, descripcion="Adulto mayor"),
    GrupoEdad(etiqueta="70-74", edad_minima_anios=70, edad_maxima_anios=74, descripcion="Adulto mayor"),
    GrupoEdad(etiqueta="75-79", edad_minima_anios=75, edad_maxima_anios=79, descripcion="Adulto mayor"),
    GrupoEdad(etiqueta="80+", edad_minima_anios=80, edad_maxima_anios=None, descripcion="Adulto mayor avanzado"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos Pediátricos Detallados
# =============================================================================

GRUPOS_EDAD_PEDIATRICOS: List[GrupoEdad] = [
    # Grupos neonatales (primeros 28 días de vida)
    GrupoEdad(
        etiqueta="Neonato precoz (0-6 días)",
        edad_minima_anios=0,
        edad_maxima_anios=0,
        edad_minima_dias=0,
        edad_maxima_dias=6,
        descripcion="Periodo neonatal precoz - primeros 7 días",
    ),
    GrupoEdad(
        etiqueta="Neonato (7-28 días)",
        edad_minima_anios=0,
        edad_maxima_anios=0,
        edad_minima_dias=7,
        edad_maxima_dias=28,
        descripcion="Periodo neonatal tardío",
    ),
    # Postneonatal y lactancia
    GrupoEdad(
        etiqueta="Postneonatal (29 días-11 meses)",
        edad_minima_anios=0,
        edad_maxima_anios=0,
        edad_minima_dias=29,
        edad_maxima_dias=365,
        descripcion="Lactante menor",
    ),
    GrupoEdad(etiqueta="1 año", edad_minima_anios=1, edad_maxima_anios=1, descripcion="Lactante mayor"),
    GrupoEdad(etiqueta="2-4 años", edad_minima_anios=2, edad_maxima_anios=4, descripcion="Preescolar"),
    GrupoEdad(etiqueta="5-9 años", edad_minima_anios=5, edad_maxima_anios=9, descripcion="Escolar"),
    GrupoEdad(etiqueta="10-14 años", edad_minima_anios=10, edad_maxima_anios=14, descripcion="Adolescente temprano"),
    GrupoEdad(etiqueta="15-19 años", edad_minima_anios=15, edad_maxima_anios=19, descripcion="Adolescente"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos Simplificados (Grandes grupos)
# =============================================================================

GRUPOS_EDAD_SIMPLIFICADOS: List[GrupoEdad] = [
    GrupoEdad(etiqueta="0-17", edad_minima_anios=0, edad_maxima_anios=17, descripcion="Menores de edad"),
    GrupoEdad(etiqueta="18-39", edad_minima_anios=18, edad_maxima_anios=39, descripcion="Adultos jóvenes"),
    GrupoEdad(etiqueta="40-59", edad_minima_anios=40, edad_maxima_anios=59, descripcion="Adultos"),
    GrupoEdad(etiqueta="60+", edad_minima_anios=60, edad_maxima_anios=None, descripcion="Adultos mayores"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos por Decenios
# =============================================================================

GRUPOS_EDAD_DECENALES: List[GrupoEdad] = [
    GrupoEdad(etiqueta="0-9", edad_minima_anios=0, edad_maxima_anios=9, descripcion="Niñez"),
    GrupoEdad(etiqueta="10-19", edad_minima_anios=10, edad_maxima_anios=19, descripcion="Adolescencia"),
    GrupoEdad(etiqueta="20-29", edad_minima_anios=20, edad_maxima_anios=29, descripcion="Adulto joven"),
    GrupoEdad(etiqueta="30-39", edad_minima_anios=30, edad_maxima_anios=39, descripcion="Adulto"),
    GrupoEdad(etiqueta="40-49", edad_minima_anios=40, edad_maxima_anios=49, descripcion="Adulto"),
    GrupoEdad(etiqueta="50-59", edad_minima_anios=50, edad_maxima_anios=59, descripcion="Adulto maduro"),
    GrupoEdad(etiqueta="60-69", edad_minima_anios=60, edad_maxima_anios=69, descripcion="Adulto mayor"),
    GrupoEdad(etiqueta="70+", edad_minima_anios=70, edad_maxima_anios=None, descripcion="Adulto mayor avanzado"),
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def generar_sql_case_when(grupos_edad: List[GrupoEdad]) -> str:
    """
    Genera la cláusula CASE WHEN de SQL para clasificar edades en grupos

    Args:
        grupos_edad: Lista de grupos etarios a usar

    Returns:
        String con la cláusula CASE WHEN completa

    Example:
        ```sql
        CASE
            WHEN edad_en_años < 5 THEN '0-4'
            WHEN edad_en_años < 10 THEN '5-9'
            ...
            ELSE '65+'
        END
        ```
    """
    cases = []

    for grupo in grupos_edad:
        # Para grupos con días (neonatales)
        if grupo.edad_minima_dias is not None and grupo.edad_maxima_dias is not None:
            # Calcular edad en días: (fecha_evento - fecha_nacimiento)
            condition = (
                f"EXTRACT(DAY FROM (e.fecha_minima_caso - e.fecha_nacimiento)) >= {grupo.edad_minima_dias} "
                f"AND EXTRACT(DAY FROM (e.fecha_minima_caso - e.fecha_nacimiento)) <= {grupo.edad_maxima_dias}"
            )
            cases.append(f"WHEN {condition} THEN '{grupo.etiqueta}'")

        # Para grupos con años
        else:
            age_expr = "EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento))"

            if grupo.edad_maxima_anios is None:
                # Último grupo sin límite superior
                condition = f"{age_expr} >= {grupo.edad_minima_anios}"
            else:
                condition = f"{age_expr} >= {grupo.edad_minima_anios} AND {age_expr} <= {grupo.edad_maxima_anios}"

            cases.append(f"WHEN {condition} THEN '{grupo.etiqueta}'")

    # Caso por defecto
    cases.append("ELSE 'Desconocido'")

    return "CASE\n    " + "\n    ".join(cases) + "\nEND"


def obtener_etiquetas_grupos_edad(grupos_edad: List[GrupoEdad]) -> List[str]:
    """Obtiene las etiquetas de los grupos en orden"""
    return [grupo.etiqueta for grupo in grupos_edad]


def obtener_configuracion_grupos_edad(nombre_config: str = "standard") -> List[GrupoEdad]:
    """
    Obtiene la configuración de grupos etarios por nombre

    Args:
        nombre_config: Nombre de la configuración
            - "standard": Grupos quinquenales estándar (default)
            - "pediatric": Grupos pediátricos detallados
            - "simple": Grupos simplificados
            - "decennial": Grupos por decenios

    Returns:
        Lista de grupos etarios
    """
    configs = {
        "standard": GRUPOS_EDAD_ESTANDAR,
        "pediatric": GRUPOS_EDAD_PEDIATRICOS,
        "simple": GRUPOS_EDAD_SIMPLIFICADOS,
        "decennial": GRUPOS_EDAD_DECENALES,
    }

    if nombre_config not in configs:
        raise ValueError(f"Configuración desconocida: {nombre_config}. Opciones: {list(configs.keys())}")

    return configs[nombre_config]


# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================

# Esta es la configuración que se usa por defecto en la aplicación
GRUPOS_EDAD_DEFECTO = GRUPOS_EDAD_ESTANDAR
