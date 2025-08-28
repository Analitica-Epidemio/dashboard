"""
Seeds del sistema - Carga de datos iniciales.

Cada módulo en esta carpeta contiene seeds específicos:
- strategies: Estrategias de vigilancia
- (futuro) users: Usuarios iniciales
- (futuro) establishments: Establecimientos de salud
"""

from app.scripts.seeds.strategies import main as seed_strategies

__all__ = ["seed_strategies"]