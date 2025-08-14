"""
Dominio de Establecimientos - Instituciones de salud.

Contiene:
- Establecimientos de salud y su información
- Participación de establecimientos en eventos
- Relaciones con localidades y usuarios
"""

from .models import Establecimiento, EstablecimientoEvento

__all__ = ["Establecimiento", "EstablecimientoEvento"]
