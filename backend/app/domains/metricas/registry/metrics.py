"""
Definiciones de métricas disponibles para consulta (Registry de Métricas).

══════════════════════════════════════════════════════════════════════════════════
¿QUÉ ES ESTO?
══════════════════════════════════════════════════════════════════════════════════

Este archivo define CÓMO EJECUTAR cada métrica a nivel de base de datos.
Cada MetricDefinition especifica:

1. source: De qué tipo de vigilancia viene (CLINICO, LABORATORIO, NOMINAL, etc.)
   Esto determina qué Builder se usa para construir la query.

2. model: Qué modelo SQLModel contiene los datos (ConteoCasosClinicos, etc.)

3. field_getter: Lambda que retorna la columna a agregar. Usamos lambdas
   en vez de strings para que el IDE detecte errores y los refactors se
   propaguen automáticamente.

4. aggregation: Cómo agregar (SUM, COUNT, AVG, DERIVED)

5. allowed_dimensions: Por qué dimensiones se puede agrupar esta métrica.
   Por ejemplo, "muestras_positivas" permite AGENTE_ETIOLOGICO pero
   "casos_clinicos" no (porque clínico no tiene agente, solo laboratorio).

══════════════════════════════════════════════════════════════════════════════════
¿POR QUÉ LAMBDAS EN VEZ DE STRINGS?
══════════════════════════════════════════════════════════════════════════════════

MAL (string mágico que se puede romper silenciosamente):
    field_name="cantidad"

BIEN (type-safe, el IDE detecta errores):
    field_getter=lambda: ConteoCasosClinicos.cantidad

Si alguien renombra la columna, el IDE lo detecta inmediatamente.

══════════════════════════════════════════════════════════════════════════════════
FUENTES DE DATOS (MetricSource)
══════════════════════════════════════════════════════════════════════════════════

- CLINICO:     ConteoCasosClinicos - Conteos semanales de síndromes (CLI_P26)
- LABORATORIO: ConteoEstudiosLab - Muestras procesadas/positivas (LAB_P26)
- HOSPITALARIO: ConteoCamasIRA - Ocupación de camas (CLI_P26_INT)
- NOMINAL:     CasoEpidemiologico - Casos individuales con datos de paciente

Cada source tiene su propio Builder en builders/ que sabe hacer los JOINs.

══════════════════════════════════════════════════════════════════════════════════
MÉTRICAS DERIVADAS
══════════════════════════════════════════════════════════════════════════════════

Algunas métricas se calculan a partir de otras (ej: tasa_positividad).
Estas tienen:
- aggregation=DERIVED
- derived_from=["metrica1", "metrica2"]
- formula_fn=lambda row: row["metrica1"] / row["metrica2"] * 100

El MetricService ejecuta primero las métricas base y luego aplica la fórmula.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Type

from sqlalchemy import func
from sqlmodel import SQLModel

# Imports de modelos
from app.domains.vigilancia_agregada.models.conteos import (
    ConteoCamasIRA,
    ConteoCasosClinicos,
    ConteoEstudiosLab,
)
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico

from .dimensions import DimensionCode


class MetricSource(str, Enum):
    """Fuente de datos de la métrica."""

    CLINICO = "CLINICO"  # ConteoCasosClinicos
    LABORATORIO = "LABORATORIO"  # ConteoEstudiosLab
    NOMINAL = "NOMINAL"  # CasoEpidemiologico
    HOSPITALARIO = "HOSPITALARIO"  # ConteoCamasIRA


class AggregationType(str, Enum):
    """Tipo de agregación."""

    SUM = "SUM"
    COUNT = "COUNT"
    AVG = "AVG"
    DERIVED = "DERIVED"  # Calculada a partir de otras métricas


@dataclass
class MetricDefinition:
    """
    Definición type-safe de una métrica.

    Usa field_getter (callable) para referencias type-safe a columnas.
    """

    code: str
    label: str
    description: str
    source: MetricSource

    # Categoría para agrupar en UI
    categoria: str = ""

    # Modelo principal
    model: Type[SQLModel] = None  # type: ignore

    # Tipo de agregación
    aggregation: AggregationType = AggregationType.SUM

    # Lambda que retorna la columna a agregar - Type-safe
    field_getter: Callable[[], Any] | None = None

    # Dimensiones permitidas para esta métrica
    allowed_dimensions: list[DimensionCode] = field(default_factory=list)

    # Para métricas derivadas
    derived_from: list[str] | None = None
    formula_fn: Callable[[dict], float] | None = None

    # Formato de display
    format_pattern: str = "0,0"
    suffix: str = ""

    def get_aggregation_expr(self):
        """
        Genera la expresión SQLAlchemy para agregación.
        Usa referencias directas al modelo.
        """
        if self.aggregation == AggregationType.DERIVED:
            return None

        if not self.field_getter:
            raise ValueError(f"Métrica {self.code} requiere field_getter")

        column = self.field_getter()

        if self.aggregation == AggregationType.SUM:
            return func.sum(column)
        elif self.aggregation == AggregationType.COUNT:
            return func.count(column)
        elif self.aggregation == AggregationType.AVG:
            return func.avg(column)

        raise ValueError(f"Agregación no soportada: {self.aggregation}")

    def compute_derived(self, row: dict) -> float | None:
        """Calcula métrica derivada."""
        if not self.formula_fn:
            return None
        try:
            return self.formula_fn(row)
        except (ZeroDivisionError, TypeError, KeyError):
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRO DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

METRICS: dict[str, MetricDefinition] = {
    # ═══════════════════════════════════════════════════════════════
    # VIGILANCIA CLÍNICA (CLI_P26)
    # ═══════════════════════════════════════════════════════════════
    "casos_clinicos": MetricDefinition(
        code="casos_clinicos",
        label="Casos Clínicos",
        description="Casos notificados por establecimientos de salud (vigilancia pasiva CLI_P26)",
        categoria="Vigilancia Clínica",
        source=MetricSource.CLINICO,
        model=ConteoCasosClinicos,
        aggregation=AggregationType.SUM,
        field_getter=lambda: ConteoCasosClinicos.cantidad,
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.ANIO_EPIDEMIOLOGICO,
            DimensionCode.TIPO_EVENTO,
            DimensionCode.GRUPO_ETARIO,
            DimensionCode.SEXO,
            DimensionCode.PROVINCIA,
            DimensionCode.DEPARTAMENTO,
            DimensionCode.ESTABLECIMIENTO,
        ],
        suffix=" casos",
    ),
    # ═══════════════════════════════════════════════════════════════
    # LABORATORIO (LAB_P26)
    # ═══════════════════════════════════════════════════════════════
    "muestras_estudiadas": MetricDefinition(
        code="muestras_estudiadas",
        label="Muestras Estudiadas",
        description="Total de muestras procesadas por laboratorio (LAB_P26)",
        categoria="Laboratorio",
        source=MetricSource.LABORATORIO,
        model=ConteoEstudiosLab,
        aggregation=AggregationType.SUM,
        field_getter=lambda: ConteoEstudiosLab.estudiadas,
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.ANIO_EPIDEMIOLOGICO,
            DimensionCode.AGENTE_ETIOLOGICO,
            DimensionCode.GRUPO_ETARIO,
        ],
    ),
    "muestras_positivas": MetricDefinition(
        code="muestras_positivas",
        label="Muestras Positivas",
        description="Muestras con resultado positivo confirmado",
        categoria="Laboratorio",
        source=MetricSource.LABORATORIO,
        model=ConteoEstudiosLab,
        aggregation=AggregationType.SUM,
        field_getter=lambda: ConteoEstudiosLab.positivas,
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.ANIO_EPIDEMIOLOGICO,
            DimensionCode.AGENTE_ETIOLOGICO,
            DimensionCode.GRUPO_ETARIO,
        ],
    ),
    "tasa_positividad": MetricDefinition(
        code="tasa_positividad",
        label="Tasa de Positividad",
        description="Porcentaje de muestras con resultado positivo (positivas/estudiadas × 100)",
        categoria="Laboratorio",
        source=MetricSource.LABORATORIO,
        model=ConteoEstudiosLab,
        aggregation=AggregationType.DERIVED,
        derived_from=["muestras_positivas", "muestras_estudiadas"],
        formula_fn=lambda row: (
            (row["muestras_positivas"] / row["muestras_estudiadas"] * 100)
            if row.get("muestras_estudiadas", 0) > 0
            else 0.0
        ),
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.AGENTE_ETIOLOGICO,
        ],
        format_pattern="0.0",
        suffix="%",
    ),
    # ═══════════════════════════════════════════════════════════════
    # NOMINALES
    # ═══════════════════════════════════════════════════════════════
    "casos_nominales": MetricDefinition(
        code="casos_nominales",
        label="Casos Nominales",
        description="Casos individuales con datos de paciente (vigilancia nominal)",
        categoria="Vigilancia Nominal",
        source=MetricSource.NOMINAL,
        model=CasoEpidemiologico,
        aggregation=AggregationType.COUNT,
        field_getter=lambda: CasoEpidemiologico.id,
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.ANIO_EPIDEMIOLOGICO,
            DimensionCode.TIPO_EVENTO,
            DimensionCode.GRUPO_ETARIO,
            DimensionCode.SEXO,
            DimensionCode.PROVINCIA,
            DimensionCode.DEPARTAMENTO,
        ],
        suffix=" casos",
    ),
    # ═══════════════════════════════════════════════════════════════
    # OCUPACIÓN HOSPITALARIA (CLI_P26_INT)
    # ═══════════════════════════════════════════════════════════════
    "ocupacion_camas_ira": MetricDefinition(
        code="ocupacion_camas_ira",
        label="Camas IRA",
        description="Camas ocupadas por IRA",
        source=MetricSource.HOSPITALARIO,
        model=ConteoCamasIRA,
        aggregation=AggregationType.SUM,
        field_getter=lambda: ConteoCamasIRA.cantidad,
        allowed_dimensions=[
            DimensionCode.SEMANA_EPIDEMIOLOGICA,
            DimensionCode.ANIO_EPIDEMIOLOGICO,
            DimensionCode.TIPO_EVENTO,
            DimensionCode.GRUPO_ETARIO,
            DimensionCode.SEXO,
            DimensionCode.PROVINCIA,
            DimensionCode.DEPARTAMENTO,
            DimensionCode.ESTABLECIMIENTO,
        ],
    ),
}


def get_metric(code: str) -> MetricDefinition:
    """Obtiene una métrica por código."""
    if code not in METRICS:
        raise ValueError(f"Métrica desconocida: {code}")
    return METRICS[code]


def list_metrics() -> list[dict]:
    """Lista métricas disponibles para el frontend.

    Filtra métricas cuyo source no tiene builder implementado.
    """
    # Sources con builder implementado
    implemented_sources = {
        MetricSource.CLINICO,
        MetricSource.LABORATORIO,
        MetricSource.HOSPITALARIO,
        MetricSource.NOMINAL,
    }

    return [
        {
            "code": m.code,
            "label": m.label,
            "description": m.description,
            "categoria": m.categoria,
            "source": m.source.value,
            "allowed_dimensions": [d.value for d in m.allowed_dimensions],
            "format": m.format_pattern,
            "suffix": m.suffix,
        }
        for m in METRICS.values()
        if m.source in implemented_sources
    ]
