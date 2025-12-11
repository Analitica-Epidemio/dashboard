"""
Catalogos compartidos entre dominios de vigilancia.

Este dominio contiene entidades que son referenciadas tanto por
vigilancia_nominal como por vigilancia_agregada:

- AgenteEtiologico: Patogenos (virus, bacterias, parasitos)
  Usado en nominal (CasoAgente) y agregada (ConteoEstudiosLab)
"""

from app.domains.catalogos.agentes.models import (
    AgenteEtiologico,
    CategoriaAgente,
    GrupoAgente,
)

__all__ = [
    "AgenteEtiologico",
    "CategoriaAgente",
    "GrupoAgente",
]
