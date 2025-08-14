"""
Dominio de Diagnósticos - Diagnósticos médicos y tratamientos.

Contiene:
- Diagnósticos de eventos epidemiológicos
- Internaciones hospitalarias
- Estudios clínicos y análisis
- Tratamientos médicos
"""

from .models import (
    DiagnosticoEvento,
    EstudioEvento,
    InternacionEvento,
    TratamientoEvento,
)

__all__ = [
    "DiagnosticoEvento",
    "InternacionEvento",
    "EstudioEvento",
    "TratamientoEvento",
]
