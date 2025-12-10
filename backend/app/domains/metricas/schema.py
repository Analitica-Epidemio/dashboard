"""
Generador de Schema para Frontend (API de Descubrimiento).

══════════════════════════════════════════════════════════════════════════════════
¿QUÉ ES ESTO?
══════════════════════════════════════════════════════════════════════════════════

Este módulo GENERA el schema para el frontend combinando:
- registry/metrics.py: Definición de métricas
- registry/dimensions.py: Definición de dimensiones
- registry/sources.py: Configuración de UI por source

El frontend llama a /api/v1/metricas/schema y recibe qué filtros mostrar,
qué visualizaciones permitir, qué métricas hay disponibles, etc.

NO hay duplicación de datos - todo se genera desde el registry.
"""

from typing import Any

from .registry.dimensions import DIMENSIONS, DimensionCode
from .registry.metrics import METRICS, MetricSource
from .registry.sources import (
    SOURCES,
    FilterType,
    SourceConfig,
    VisualizationType,
    get_source_config,
)


def _source_to_cube_id(source: MetricSource) -> str:
    """Convierte MetricSource a cube_id para compatibilidad."""
    mapping = {
        MetricSource.CLINICO: "vigilancia_clinica",
        MetricSource.LABORATORIO: "vigilancia_laboratorio",
        MetricSource.NOMINAL: "vigilancia_nominal",
        MetricSource.HOSPITALARIO: "vigilancia_hospitalaria",
    }
    return mapping.get(source, source.value.lower())


def _cube_id_to_source(cube_id: str) -> MetricSource | None:
    """Convierte cube_id a MetricSource."""
    mapping = {
        "vigilancia_clinica": MetricSource.CLINICO,
        "vigilancia_laboratorio": MetricSource.LABORATORIO,
        "vigilancia_nominal": MetricSource.NOMINAL,
        "vigilancia_hospitalaria": MetricSource.HOSPITALARIO,
    }
    return mapping.get(cube_id)


def _generate_measures_for_source(source: MetricSource) -> dict[str, Any]:
    """Genera definición de measures desde metrics.py."""
    measures = {}
    for metric in METRICS.values():
        if metric.source == source:
            measures[metric.code] = {
                "type": metric.aggregation.value.lower(),
                "label": metric.label,
                "description": metric.description,
                "format": metric.format_pattern,
                "suffix": metric.suffix,
            }
    return measures


def _generate_dimensions_for_source(source: MetricSource) -> dict[str, Any]:
    """Genera definición de dimensions desde dimensions.py filtrado por source."""
    # Obtener dimensiones permitidas para las métricas de este source
    allowed_dims: set[DimensionCode] = set()
    for metric in METRICS.values():
        if metric.source == source:
            allowed_dims.update(metric.allowed_dimensions)

    dimensions = {}
    for dim_code in allowed_dims:
        dim = DIMENSIONS.get(dim_code)
        if dim:
            dimensions[dim_code.value.lower()] = {
                "type": "number"
                if "SEMANA" in dim_code.value or "ANIO" in dim_code.value
                else "string",
                "label": dim.label,
                "description": dim.description,
            }
    return dimensions


def _generate_filters_for_source(source_config: SourceConfig) -> dict[str, Any]:
    """Genera definición de filters desde sources.py."""
    filters = {}
    for f in source_config.filters:
        filter_def: dict[str, Any] = {
            "type": f.type.value,
            "label": f.label,
        }
        if f.endpoint:
            filter_def["endpoint"] = f.endpoint
        if f.options:
            filter_def["options"] = f.options
        if f.depends_on:
            filter_def["depends_on"] = f.depends_on
        filters[f.key] = filter_def
    return filters


def _generate_kpis_for_source(source_config: SourceConfig) -> list[dict[str, Any]]:
    """Genera definición de KPIs desde sources.py."""
    return [
        {
            "key": kpi.key,
            "label": kpi.label,
            "measure": kpi.metric_code,
            "type": kpi.type,
        }
        for kpi in source_config.kpis
    ]


def get_cube(cube_id: str) -> dict[str, Any] | None:
    """
    Obtiene un cube por su ID.

    GENERA dinámicamente desde el registry (no hay datos duplicados).
    """
    source = _cube_id_to_source(cube_id)
    if not source:
        return None

    source_config = get_source_config(source)
    if not source_config or not source_config.enabled:
        return None

    return {
        "title": source_config.title,
        "description": source_config.description,
        "source": source.value,
        "icon": source_config.icon,
        "measures": _generate_measures_for_source(source),
        "dimensions": _generate_dimensions_for_source(source),
        "filters": _generate_filters_for_source(source_config),
        "default_visualization": source_config.default_visualization.value,
        "allowed_visualizations": [
            v.value for v in source_config.allowed_visualizations
        ],
        "kpis": _generate_kpis_for_source(source_config),
    }


def list_cubes(include_disabled: bool = False) -> list[dict[str, Any]]:
    """
    Lista todos los cubes disponibles.

    GENERA dinámicamente desde el registry.
    """
    result = []
    for source_config in SOURCES.values():
        if not include_disabled and not source_config.enabled:
            continue

        cube_id = _source_to_cube_id(source_config.source)
        measures = _generate_measures_for_source(source_config.source)
        dimensions = _generate_dimensions_for_source(source_config.source)

        result.append(
            {
                "id": cube_id,
                "title": source_config.title,
                "description": source_config.description,
                "icon": source_config.icon,
                "source": source_config.source.value,
                "measures": list(measures.keys()),
                "dimensions": list(dimensions.keys()),
                "filters": {
                    f.key: {"type": f.type.value, "label": f.label}
                    for f in source_config.filters
                },
                "visualizations": [
                    v.value for v in source_config.allowed_visualizations
                ],
                "default_visualization": source_config.default_visualization.value,
                "kpis": _generate_kpis_for_source(source_config),
            }
        )

    return result


def get_cube_schema(cube_id: str) -> dict[str, Any] | None:
    """
    Obtiene el schema completo de un cube para el frontend.

    Equivalente a get_cube pero con formato expandido.
    """
    cube = get_cube(cube_id)
    if not cube:
        return None

    return {
        "id": cube_id,
        **cube,
    }


# Re-exportar tipos para compatibilidad
__all__ = [
    "get_cube",
    "list_cubes",
    "get_cube_schema",
    "VisualizationType",
    "FilterType",
]
