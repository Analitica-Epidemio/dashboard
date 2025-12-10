"""
Catalogo de Agentes Etiologicos.

Los agentes etiologicos son patogenos (virus, bacterias, parasitos) que causan
enfermedades. Este catalogo es compartido entre:

- vigilancia_nominal: Deteccion en casos individuales
- vigilancia_agregada: Conteos de laboratorio (LAB_P26)
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
