"""
Dominio de Charts - Visualizaciones y configuraciones de gráficos epidemiológicos.

Este dominio gestiona:
- Plantillas de gráficos (ChartTemplate)
- Configuraciones por tipo ENO (EnfermedadChartConfig)
- Servicios de generación de datos
- Permisos y auditoría
"""

# Importar modelos para que Alembic los detecte
from .models import DashboardChart

__all__ = ["DashboardChart"]
