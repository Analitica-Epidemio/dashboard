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
class AgeGroup:
    """Representa un grupo etario"""
    label: str  # Etiqueta mostrada (ej: "0-4 años", "Neonato")
    min_age_years: float  # Edad mínima en años (puede ser decimal para días/meses)
    max_age_years: float | None  # Edad máxima en años (None = sin límite superior)
    min_age_days: int | None = None  # Edad mínima en días (para grupos neonatales)
    max_age_days: int | None = None  # Edad máxima en días (para grupos neonatales)
    description: str = ""  # Descripción opcional del grupo


# =============================================================================
# CONFIGURACIÓN: Grupos Etarios Estándar (Quinquenales)
# =============================================================================

STANDARD_AGE_GROUPS: List[AgeGroup] = [
    AgeGroup(label="0-4", min_age_years=0, max_age_years=4, description="Primera infancia"),
    AgeGroup(label="5-9", min_age_years=5, max_age_years=9, description="Niñez temprana"),
    AgeGroup(label="10-14", min_age_years=10, max_age_years=14, description="Niñez tardía/Adolescencia temprana"),
    AgeGroup(label="15-19", min_age_years=15, max_age_years=19, description="Adolescencia"),
    AgeGroup(label="20-24", min_age_years=20, max_age_years=24, description="Adulto joven"),
    AgeGroup(label="25-29", min_age_years=25, max_age_years=29, description="Adulto joven"),
    AgeGroup(label="30-34", min_age_years=30, max_age_years=34, description="Adulto"),
    AgeGroup(label="35-39", min_age_years=35, max_age_years=39, description="Adulto"),
    AgeGroup(label="40-44", min_age_years=40, max_age_years=44, description="Adulto"),
    AgeGroup(label="45-49", min_age_years=45, max_age_years=49, description="Adulto"),
    AgeGroup(label="50-54", min_age_years=50, max_age_years=54, description="Adulto mayor temprano"),
    AgeGroup(label="55-59", min_age_years=55, max_age_years=59, description="Adulto mayor temprano"),
    AgeGroup(label="60-64", min_age_years=60, max_age_years=64, description="Adulto mayor"),
    AgeGroup(label="65-69", min_age_years=65, max_age_years=69, description="Adulto mayor"),
    AgeGroup(label="70-74", min_age_years=70, max_age_years=74, description="Adulto mayor"),
    AgeGroup(label="75-79", min_age_years=75, max_age_years=79, description="Adulto mayor"),
    AgeGroup(label="80+", min_age_years=80, max_age_years=None, description="Adulto mayor avanzado"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos Pediátricos Detallados
# =============================================================================

PEDIATRIC_AGE_GROUPS: List[AgeGroup] = [
    # Grupos neonatales (primeros 28 días de vida)
    AgeGroup(
        label="Neonato precoz (0-6 días)",
        min_age_years=0,
        max_age_years=0,
        min_age_days=0,
        max_age_days=6,
        description="Periodo neonatal precoz - primeros 7 días",
    ),
    AgeGroup(
        label="Neonato (7-28 días)",
        min_age_years=0,
        max_age_years=0,
        min_age_days=7,
        max_age_days=28,
        description="Periodo neonatal tardío",
    ),
    # Postneonatal y lactancia
    AgeGroup(
        label="Postneonatal (29 días-11 meses)",
        min_age_years=0,
        max_age_years=0,
        min_age_days=29,
        max_age_days=365,
        description="Lactante menor",
    ),
    AgeGroup(label="1 año", min_age_years=1, max_age_years=1, description="Lactante mayor"),
    AgeGroup(label="2-4 años", min_age_years=2, max_age_years=4, description="Preescolar"),
    AgeGroup(label="5-9 años", min_age_years=5, max_age_years=9, description="Escolar"),
    AgeGroup(label="10-14 años", min_age_years=10, max_age_years=14, description="Adolescente temprano"),
    AgeGroup(label="15-19 años", min_age_years=15, max_age_years=19, description="Adolescente"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos Simplificados (Grandes grupos)
# =============================================================================

SIMPLE_AGE_GROUPS: List[AgeGroup] = [
    AgeGroup(label="0-17", min_age_years=0, max_age_years=17, description="Menores de edad"),
    AgeGroup(label="18-39", min_age_years=18, max_age_years=39, description="Adultos jóvenes"),
    AgeGroup(label="40-59", min_age_years=40, max_age_years=59, description="Adultos"),
    AgeGroup(label="60+", min_age_years=60, max_age_years=None, description="Adultos mayores"),
]


# =============================================================================
# CONFIGURACIÓN: Grupos por Decenios
# =============================================================================

DECENNIAL_AGE_GROUPS: List[AgeGroup] = [
    AgeGroup(label="0-9", min_age_years=0, max_age_years=9, description="Niñez"),
    AgeGroup(label="10-19", min_age_years=10, max_age_years=19, description="Adolescencia"),
    AgeGroup(label="20-29", min_age_years=20, max_age_years=29, description="Adulto joven"),
    AgeGroup(label="30-39", min_age_years=30, max_age_years=39, description="Adulto"),
    AgeGroup(label="40-49", min_age_years=40, max_age_years=49, description="Adulto"),
    AgeGroup(label="50-59", min_age_years=50, max_age_years=59, description="Adulto maduro"),
    AgeGroup(label="60-69", min_age_years=60, max_age_years=69, description="Adulto mayor"),
    AgeGroup(label="70+", min_age_years=70, max_age_years=None, description="Adulto mayor avanzado"),
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def generate_sql_case_when(age_groups: List[AgeGroup]) -> str:
    """
    Genera la cláusula CASE WHEN de SQL para clasificar edades en grupos

    Args:
        age_groups: Lista de grupos etarios a usar

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

    for group in age_groups:
        # Para grupos con días (neonatales)
        if group.min_age_days is not None and group.max_age_days is not None:
            # Calcular edad en días: (fecha_evento - fecha_nacimiento)
            condition = (
                f"EXTRACT(DAY FROM (e.fecha_minima_evento - e.fecha_nacimiento)) >= {group.min_age_days} "
                f"AND EXTRACT(DAY FROM (e.fecha_minima_evento - e.fecha_nacimiento)) <= {group.max_age_days}"
            )
            cases.append(f"WHEN {condition} THEN '{group.label}'")

        # Para grupos con años
        else:
            age_expr = "EXTRACT(YEAR FROM AGE(e.fecha_minima_evento, e.fecha_nacimiento))"

            if group.max_age_years is None:
                # Último grupo sin límite superior
                condition = f"{age_expr} >= {group.min_age_years}"
            else:
                condition = f"{age_expr} >= {group.min_age_years} AND {age_expr} <= {group.max_age_years}"

            cases.append(f"WHEN {condition} THEN '{group.label}'")

    # Caso por defecto
    cases.append("ELSE 'Desconocido'")

    return "CASE\n    " + "\n    ".join(cases) + "\nEND"


def get_age_group_labels(age_groups: List[AgeGroup]) -> List[str]:
    """Obtiene las etiquetas de los grupos en orden"""
    return [group.label for group in age_groups]


def get_age_groups_config(config_name: str = "standard") -> List[AgeGroup]:
    """
    Obtiene la configuración de grupos etarios por nombre

    Args:
        config_name: Nombre de la configuración
            - "standard": Grupos quinquenales estándar (default)
            - "pediatric": Grupos pediátricos detallados
            - "simple": Grupos simplificados
            - "decennial": Grupos por decenios

    Returns:
        Lista de grupos etarios
    """
    configs = {
        "standard": STANDARD_AGE_GROUPS,
        "pediatric": PEDIATRIC_AGE_GROUPS,
        "simple": SIMPLE_AGE_GROUPS,
        "decennial": DECENNIAL_AGE_GROUPS,
    }

    if config_name not in configs:
        raise ValueError(f"Configuración desconocida: {config_name}. Opciones: {list(configs.keys())}")

    return configs[config_name]


# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================

# Esta es la configuración que se usa por defecto en la aplicación
DEFAULT_AGE_GROUPS = STANDARD_AGE_GROUPS
