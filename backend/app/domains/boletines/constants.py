"""
Constantes y enumeraciones del dominio de Boletines.
"""

from enum import Enum


class TipoBloque(str, Enum):
    """Tipos de bloque de datos soportados."""

    CORREDOR_ENDEMICO = "CORREDOR_ENDEMICO"
    CURVA_EPIDEMIOLOGICA = "CURVA_EPIDEMIOLOGICA"
    DISTRIBUCION_EDAD = "DISTRIBUCION_EDAD"
    TABLA_RESUMEN = "TABLA_RESUMEN"
    COMPARACION_ANUAL = "COMPARACION_ANUAL"
    TOP_EVENTOS = "TOP_EVENTOS"
    TABLA_CASOS = "TABLA_CASOS"  # Tabla de casos individuales nominales


class TipoVisualizacion(str, Enum):
    """Tipos de visualización para renderizado."""

    AREA_CHART = "AREA_CHART"
    STACKED_BAR = "STACKED_BAR"
    GROUPED_BAR = "GROUPED_BAR"
    LINE_CHART = "LINE_CHART"
    TABLE = "TABLE"
