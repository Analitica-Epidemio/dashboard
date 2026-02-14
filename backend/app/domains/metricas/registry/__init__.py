"""
Registry de métricas, dimensiones y sources.
============================================

Este es el ÚNICO lugar donde se definen métricas y dimensiones.
El schema para frontend se GENERA desde aquí (ver schema.py).

ARCHIVOS:
    - metrics.py: Define métricas (qué columna, qué agregación)
    - dimensions.py: Define dimensiones (por qué agrupar)
    - sources.py: Config de UI por tipo de vigilancia (filtros, KPIs)

USO:
    from app.domains.metricas.registry import get_metric, get_dimension

    metric = get_metric("casos_clinicos")
    dim = get_dimension("SEMANA_EPIDEMIOLOGICA")
"""

from .dimensions import (
    DIMENSIONS,
    DimensionCode,
    DimensionDefinition,
    get_dimension,
)
from .metrics import (
    METRICS,
    AggregationType,
    MetricDefinition,
    MetricSource,
    get_metric,
    list_metrics,
)
from .sources import (
    SOURCES,
    FilterConfig,
    FilterType,
    KPIConfig,
    SourceConfig,
    VisualizationType,
    get_source_config,
    list_enabled_sources,
)

__all__ = [
    # Dimensiones
    "DIMENSIONS",
    # Métricas
    "METRICS",
    # Sources (UI config)
    "SOURCES",
    "AggregationType",
    "DimensionCode",
    "DimensionDefinition",
    "FilterConfig",
    "FilterType",
    "KPIConfig",
    "MetricDefinition",
    "MetricSource",
    "SourceConfig",
    "VisualizationType",
    "get_dimension",
    "get_metric",
    "get_source_config",
    "list_enabled_sources",
    "list_metrics",
]
