"""
Registry de métricas y dimensiones.
====================================

Este es el ÚNICO lugar donde se definen métricas y dimensiones.
El schema para frontend se GENERA desde aquí (ver schema.py).

ARCHIVOS:
    - metrics.py: Define métricas (qué columna, qué agregación)
    - dimensions.py: Define dimensiones (por qué agrupar)

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

__all__ = [
    # Métricas
    "METRICS",
    "MetricDefinition",
    "MetricSource",
    "AggregationType",
    "get_metric",
    "list_metrics",
    # Dimensiones
    "DIMENSIONS",
    "DimensionCode",
    "DimensionDefinition",
    "get_dimension",
]
