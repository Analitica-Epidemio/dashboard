"""
Configuración de fuentes de datos (Sources) para el frontend.

══════════════════════════════════════════════════════════════════════════════════
¿QUÉ ES ESTO?
══════════════════════════════════════════════════════════════════════════════════

Cada SOURCE (CLINICO, LABORATORIO, etc.) representa un "tipo de vigilancia"
que tiene su propia página en el frontend. Este archivo define:

1. Metadata de UI (título, descripción, ícono)
2. Filtros disponibles (qué filtros mostrar, de dónde cargar opciones)
3. Visualizaciones permitidas
4. KPIs predefinidos para tarjetas de resumen

Las MÉTRICAS y DIMENSIONES se definen en metrics.py y dimensions.py.
Este archivo solo agrega la capa de configuración de UI.

══════════════════════════════════════════════════════════════════════════════════
¿POR QUÉ SEPARAR SOURCES DE METRICS?
══════════════════════════════════════════════════════════════════════════════════

- Una SOURCE puede tener múltiples métricas (ej: LABORATORIO tiene
  muestras_estudiadas, muestras_positivas, tasa_positividad)
- La configuración de UI (filtros, KPIs) es por página/source, no por métrica
- Mantiene separación de concerns: metrics.py es backend, sources.py es UI
"""

from dataclasses import dataclass, field
from enum import Enum

from .metrics import MetricSource


class VisualizationType(str, Enum):
    """Tipos de visualización disponibles en frontend."""

    LINE = "line"
    BAR = "bar"
    AREA = "area"
    STACKED_BAR = "stacked_bar"
    PIE = "pie"
    TABLE = "table"
    HEATMAP = "heatmap"
    MAP = "map"


class FilterType(str, Enum):
    """Tipos de filtro para UI."""

    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE_RANGE = "date_range"


@dataclass
class FilterConfig:
    """Configuración de un filtro para UI."""

    key: str
    label: str
    type: FilterType
    endpoint: str | None = None  # Para cargar opciones dinámicamente
    options: list[dict] | None = None  # Opciones estáticas
    depends_on: str | None = None  # Filtro del que depende


@dataclass
class KPIConfig:
    """Configuración de KPI para tarjetas de resumen."""

    key: str
    label: str
    metric_code: str  # Referencia a métrica en metrics.py
    type: str = "value"  # value, trend, comparison


@dataclass
class SourceConfig:
    """Configuración completa de una fuente de datos para UI."""

    source: MetricSource
    title: str
    description: str
    icon: str

    # Filtros disponibles en esta página
    filters: list[FilterConfig] = field(default_factory=list)

    # Visualizaciones
    default_visualization: VisualizationType = VisualizationType.LINE
    allowed_visualizations: list[VisualizationType] = field(default_factory=list)

    # KPIs para tarjetas
    kpis: list[KPIConfig] = field(default_factory=list)

    # Si está habilitado (para features en desarrollo)
    enabled: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN POR SOURCE
# ═══════════════════════════════════════════════════════════════════════════════

SOURCES: dict[MetricSource, SourceConfig] = {
    MetricSource.CLINICO: SourceConfig(
        source=MetricSource.CLINICO,
        title="Vigilancia Clínica",
        description="Monitoreo de síndromes respiratorios (ETI, IRAG, Neumonía, Bronquiolitis)",
        icon="stethoscope",
        filters=[
            FilterConfig(
                key="grupo_eno_id",
                label="Grupo ENO",
                type=FilterType.MULTI_SELECT,
                endpoint="/api/v1/catalogos/grupos-eno",
            ),
            FilterConfig(
                key="evento_ids",
                label="Eventos",
                type=FilterType.MULTI_SELECT,
                endpoint="/api/v1/catalogos/eventos",
                depends_on="grupo_eno_id",
            ),
            FilterConfig(
                key="provincia_id",
                label="Provincia",
                type=FilterType.SELECT,
                endpoint="/api/v1/catalogos/provincias",
            ),
        ],
        default_visualization=VisualizationType.LINE,
        allowed_visualizations=[
            VisualizationType.LINE,
            VisualizationType.AREA,
            VisualizationType.BAR,
            VisualizationType.TABLE,
        ],
        kpis=[
            KPIConfig(
                key="total_casos", label="Total Casos", metric_code="casos_clinicos"
            ),
            KPIConfig(
                key="tendencia",
                label="Tendencia",
                metric_code="casos_clinicos",
                type="trend",
            ),
        ],
    ),
    MetricSource.LABORATORIO: SourceConfig(
        source=MetricSource.LABORATORIO,
        title="Vigilancia por Laboratorio",
        description="Monitoreo de resultados de laboratorio, positividad, agentes detectados",
        icon="flask",
        filters=[
            FilterConfig(
                key="agente_ids",
                label="Agentes",
                type=FilterType.MULTI_SELECT,
                endpoint="/api/v1/catalogos/agentes",
            ),
            FilterConfig(
                key="provincia_id",
                label="Provincia",
                type=FilterType.SELECT,
                endpoint="/api/v1/catalogos/provincias",
            ),
        ],
        default_visualization=VisualizationType.LINE,
        allowed_visualizations=[
            VisualizationType.LINE,
            VisualizationType.BAR,
            VisualizationType.TABLE,
            VisualizationType.HEATMAP,
        ],
        kpis=[
            KPIConfig(
                key="total_muestras",
                label="Muestras",
                metric_code="muestras_estudiadas",
            ),
            KPIConfig(
                key="total_positivos",
                label="Positivos",
                metric_code="muestras_positivas",
            ),
            KPIConfig(
                key="positividad", label="Positividad", metric_code="tasa_positividad"
            ),
        ],
    ),
    MetricSource.NOMINAL: SourceConfig(
        source=MetricSource.NOMINAL,
        title="Vigilancia Nominal",
        description="Seguimiento caso a caso, análisis de brotes, letalidad",
        icon="clipboard-list",
        filters=[
            FilterConfig(
                key="evento_id",
                label="Evento",
                type=FilterType.SELECT,
                endpoint="/api/v1/catalogos/eventos-nominales",
            ),
            FilterConfig(
                key="provincia_id",
                label="Provincia",
                type=FilterType.SELECT,
                endpoint="/api/v1/catalogos/provincias",
            ),
        ],
        default_visualization=VisualizationType.AREA,
        allowed_visualizations=[
            VisualizationType.LINE,
            VisualizationType.AREA,
            VisualizationType.BAR,
            VisualizationType.TABLE,
            VisualizationType.MAP,
        ],
        kpis=[
            KPIConfig(key="total_casos", label="Casos", metric_code="casos_nominales"),
        ],
    ),
    MetricSource.HOSPITALARIO: SourceConfig(
        source=MetricSource.HOSPITALARIO,
        title="Vigilancia Hospitalaria",
        description="Monitoreo de internaciones, UCI, asistencia respiratoria mecánica",
        icon="hospital",
        filters=[
            FilterConfig(
                key="provincia_id",
                label="Provincia",
                type=FilterType.SELECT,
                endpoint="/api/v1/catalogos/provincias",
            ),
        ],
        default_visualization=VisualizationType.LINE,
        allowed_visualizations=[
            VisualizationType.LINE,
            VisualizationType.BAR,
            VisualizationType.TABLE,
        ],
        kpis=[
            KPIConfig(
                key="camas_ira", label="Camas IRA", metric_code="ocupacion_camas_ira"
            ),
        ],
        enabled=True,
    ),
}


def get_source_config(source: MetricSource) -> SourceConfig | None:
    """Obtiene configuración de un source."""
    return SOURCES.get(source)


def list_enabled_sources() -> list[SourceConfig]:
    """Lista sources habilitados."""
    return [s for s in SOURCES.values() if s.enabled]
