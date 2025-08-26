"""
Dominio de Eventos - Gestión de eventos epidemiológicos.

Contiene:
- Eventos epidemiológicos y sus grupos
- Antecedentes epidemiológicos
- Relación ciudadano-evento con detalles
- Síntomas y antecedentes por evento
"""

from .models import (
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
    DetalleEventoSintomas,
    Evento,
    GrupoEno,
    TipoEno,
)

__all__ = [
    "Evento",
    "AntecedenteEpidemiologico",
    "DetalleEventoSintomas",
    "AntecedentesEpidemiologicosEvento",
    "GrupoEno",
    "TipoEno",
]
