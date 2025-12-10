"""
Definiciones de dimensiones para agrupación de métricas (Registry de Dimensiones).

══════════════════════════════════════════════════════════════════════════════════
¿QUÉ ES UNA DIMENSIÓN?
══════════════════════════════════════════════════════════════════════════════════

Una dimensión es una "forma de agrupar" los datos. Por ejemplo:
- SEMANA_EPIDEMIOLOGICA: Agrupa casos por semana → curva epidemiológica
- GRUPO_ETARIO: Agrupa por edad → pirámide poblacional
- PROVINCIA: Agrupa por provincia → mapa coroplético

Cuando haces una query como:
    service.query(metric="casos_clinicos", dimensions=["SEMANA_EPIDEMIOLOGICA"])

El sistema genera:
    SELECT semana, SUM(cantidad) FROM ... GROUP BY semana ORDER BY semana

══════════════════════════════════════════════════════════════════════════════════
ARQUITECTURA: METADATA + BUILDERS EXPLÍCITOS
══════════════════════════════════════════════════════════════════════════════════

DimensionDefinition = SOLO METADATA (código, label, descripción para UI).

CADA BUILDER define su propio mapeo de columnas en get_dimension_column():
- ClinicoQueryBuilder:      builders/clinico.py
- LaboratorioQueryBuilder:  builders/laboratorio.py
- HospitalarioQueryBuilder: builders/hospitalario.py
- NominalQueryBuilder:      builders/nominal.py

EJEMPLOS DE DIFERENCIAS ENTRE BUILDERS:

    SEMANA_EPIDEMIOLOGICA:
    - Agregados: NotificacionSemanal.semana
    - Nominal:   CasoEpidemiologico.fecha_minima_caso_semana_epi

    SEXO:
    - Clínico:      ConteoCasosClinicos.sexo
    - Hospitalario: ConteoCamasIRA.sexo
    - Nominal:      Ciudadano.sexo_biologico

Si agregás un nuevo builder, DEBÉS implementar get_dimension_column().

══════════════════════════════════════════════════════════════════════════════════
DIMENSIONES DISPONIBLES
══════════════════════════════════════════════════════════════════════════════════

Temporales:
- SEMANA_EPIDEMIOLOGICA: Semana 1-52/53 del año epidemiológico
- ANIO_EPIDEMIOLOGICO: Año (2024, 2025, etc.)

Evento:
- TIPO_EVENTO: ETI, Neumonía, Bronquiolitis, etc.
- AGENTE_ETIOLOGICO: VSR, Influenza A, Rotavirus, etc. (solo lab)

Demográficas:
- GRUPO_ETARIO: < 1 año, 1-4 años, 5-9 años, etc.
- SEXO: M/F/X

Geográficas:
- PROVINCIA, DEPARTAMENTO, ESTABLECIMIENTO

══════════════════════════════════════════════════════════════════════════════════
NOTA SOBRE TERMINOLOGÍA: TIPO_EVENTO
══════════════════════════════════════════════════════════════════════════════════

Usamos TIPO_EVENTO en vez de "enfermedad" porque:
  - "Intento de suicidio" no es enfermedad
  - "Intoxicación por CO" no es enfermedad
  - "Mordedura de animal" no es enfermedad

El modelo puede seguir llamándose Enfermedad, pero la capa semántica usa
la terminología más correcta: "tipo de evento epidemiológico".
"""

from dataclasses import dataclass
from enum import Enum


class DimensionCode(str, Enum):
    """Códigos de dimensiones disponibles (UPPERCASE por convención)."""

    SEMANA_EPIDEMIOLOGICA = "SEMANA_EPIDEMIOLOGICA"
    ANIO_EPIDEMIOLOGICO = "ANIO_EPIDEMIOLOGICO"
    TIPO_EVENTO = "TIPO_EVENTO"
    AGENTE_ETIOLOGICO = "AGENTE_ETIOLOGICO"
    GRUPO_ETARIO = "GRUPO_ETARIO"
    SEXO = "SEXO"
    PROVINCIA = "PROVINCIA"
    DEPARTAMENTO = "DEPARTAMENTO"
    ESTABLECIMIENTO = "ESTABLECIMIENTO"


@dataclass
class DimensionDefinition:
    """
    Definición de una dimensión - SOLO METADATA.

    El mapeo a columnas reales lo hace cada builder en get_dimension_column().
    Esto permite que cada builder use sus propias tablas/columnas sin confusión.
    """

    code: DimensionCode
    label: str
    description: str


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRO DE DIMENSIONES (METADATA PARA UI)
# ═══════════════════════════════════════════════════════════════════════════════

DIMENSIONS: dict[DimensionCode, DimensionDefinition] = {
    DimensionCode.SEMANA_EPIDEMIOLOGICA: DimensionDefinition(
        code=DimensionCode.SEMANA_EPIDEMIOLOGICA,
        label="Semana Epidemiológica",
        description="Semana del año epidemiológico (1-52/53)",
    ),
    DimensionCode.ANIO_EPIDEMIOLOGICO: DimensionDefinition(
        code=DimensionCode.ANIO_EPIDEMIOLOGICO,
        label="Año Epidemiológico",
        description="Año del calendario epidemiológico",
    ),
    DimensionCode.TIPO_EVENTO: DimensionDefinition(
        code=DimensionCode.TIPO_EVENTO,
        label="Tipo de Evento",
        description="Tipo de evento epidemiológico (ETI, Neumonía, etc.)",
    ),
    DimensionCode.AGENTE_ETIOLOGICO: DimensionDefinition(
        code=DimensionCode.AGENTE_ETIOLOGICO,
        label="Agente Etiológico",
        description="Patógeno detectado (VSR, Rotavirus, etc.)",
    ),
    DimensionCode.GRUPO_ETARIO: DimensionDefinition(
        code=DimensionCode.GRUPO_ETARIO,
        label="Grupo Etario",
        description="Rango de edad",
    ),
    DimensionCode.SEXO: DimensionDefinition(
        code=DimensionCode.SEXO,
        label="Sexo",
        description="Sexo biológico (M/F/X)",
    ),
    DimensionCode.PROVINCIA: DimensionDefinition(
        code=DimensionCode.PROVINCIA,
        label="Provincia",
        description="Provincia del establecimiento",
    ),
    DimensionCode.DEPARTAMENTO: DimensionDefinition(
        code=DimensionCode.DEPARTAMENTO,
        label="Departamento",
        description="Departamento del establecimiento",
    ),
    DimensionCode.ESTABLECIMIENTO: DimensionDefinition(
        code=DimensionCode.ESTABLECIMIENTO,
        label="Establecimiento",
        description="Establecimiento de salud",
    ),
}


def get_dimension(code: str | DimensionCode) -> DimensionDefinition:
    """Obtiene una dimensión por código."""
    if isinstance(code, str):
        code = DimensionCode(code)
    return DIMENSIONS[code]
