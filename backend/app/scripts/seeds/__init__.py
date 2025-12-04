"""
Seeds del sistema - Carga de datos iniciales.

Cada módulo en esta carpeta contiene seeds específicos:
- strategies: Estrategias de vigilancia
- charts: Configuración de charts por tipo ENO
- (futuro) users: Usuarios iniciales
- (futuro) establishments: Establecimientos de salud
"""

from app.scripts.seeds.charts import main as seed_charts
from app.scripts.seeds.strategies import main as seed_strategies

__all__ = ["seed_strategies", "seed_charts"]
