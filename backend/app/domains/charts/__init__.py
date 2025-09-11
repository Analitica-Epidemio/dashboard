"""
Dominio de Charts - Visualizaciones y configuraciones de gráficos epidemiológicos.

Este dominio gestiona:
- Plantillas de gráficos (ChartTemplate)
- Configuraciones por tipo ENO (TipoEnoChartConfig)
- Servicios de generación de datos
- Permisos y auditoría
"""

# Importar modelos para que Alembic los detecte
from .models import *  # noqa: F403, F401

__all__ = ["models"]