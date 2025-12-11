"""
Modelo simplificado para sistema de charts dinámicos
Arquitectura simple sin sobre-ingeniería
"""

from typing import Dict, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field

from app.core.models import BaseModel


class DashboardChart(BaseModel, table=True):
    """
    Configuración de charts disponibles en el dashboard
    Simple y directo: qué chart mostrar según los filtros aplicados
    """

    __tablename__ = "dashboard_charts"

    # Identificación
    codigo: str = Field(
        max_length=50, unique=True, index=True, description="Código único del chart"
    )
    nombre: str = Field(max_length=100, description="Nombre del chart para mostrar")
    descripcion: Optional[str] = Field(
        None, sa_column=Column(Text), description="Descripción del chart"
    )

    # Función de procesamiento (Python, no SQL)
    funcion_procesamiento: str = Field(
        max_length=100, description="Nombre de la función Python que procesa los datos"
    )

    # Condiciones para mostrar este chart
    condiciones_display: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Condiciones para mostrar el chart. Ej: {'grupo': ['DENGUE', 'IRA']}",
    )

    # Tipo de visualización
    tipo_visualizacion: str = Field(
        max_length=50,
        description="Tipo de chart: line, bar, pie, map, metric, area, heatmap",
    )

    # Configuración del chart
    configuracion_chart: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Config específica del chart (colores, ejes, etc)",
    )

    # Orden y estado
    orden: int = Field(default=0, description="Orden de visualización en el dashboard")
    activo: bool = Field(default=True, description="Si el chart está activo")
