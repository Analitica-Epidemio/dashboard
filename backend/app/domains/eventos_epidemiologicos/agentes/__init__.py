"""
Módulo de Agentes Etiológicos.

Contiene modelos para patógenos (virus, bacterias, parásitos) que causan
enfermedades y se detectan en eventos epidemiológicos.
"""

from app.domains.eventos_epidemiologicos.agentes.models import (
    AgenteEtiologico,
    AgenteExtraccionConfig,
    CategoriaAgente,
    EventoAgente,
    GrupoAgente,
    ResultadoDeteccion,
)

__all__ = [
    "AgenteEtiologico",
    "AgenteExtraccionConfig",
    "EventoAgente",
    "CategoriaAgente",
    "GrupoAgente",
    "ResultadoDeteccion",
]
