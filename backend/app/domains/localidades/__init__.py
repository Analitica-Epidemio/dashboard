"""
Dominio de Localidades - Estructura normalizada.

Este dominio contiene la estructura geográfica normalizada con:
- Provincias argentinas
- Departamentos
- Localidades

Todas las localidades están vinculadas a su departamento y provincia correspondiente,
siguiendo los códigos oficiales del INDEC.
"""

from .models import Departamento, Localidad, Provincia

__all__ = ["Provincia", "Departamento", "Localidad"]
