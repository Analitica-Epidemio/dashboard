"""
Dominio de Ciudadanos - Gestión de datos de ciudadanos.

Contiene:
- Datos principales de ciudadanos
- Domicilios
- Datos adicionales
- Comorbilidades
- Viajes
- Ámbitos de concurrencia
"""

from .models import (
    AmbitosConcurrenciaCiudadano,
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
    ViajesCiudadano,
)

__all__ = [
    "Ciudadano",
    "CiudadanoDomicilio",
    "CiudadanoDatos",
    "CiudadanoComorbilidades",
    "ViajesCiudadano",
    "AmbitosConcurrenciaCiudadano",
]