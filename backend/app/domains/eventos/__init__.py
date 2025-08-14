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
    CiudadanoEvento,
    DetalleEventoSintomas,
    Evento,
)

__all__ = [
    "Evento",
    "AntecedenteEpidemiologico",
    "CiudadanoEvento",
    "DetalleEventoSintomas",
    "AntecedentesEpidemiologicosEvento",
]
