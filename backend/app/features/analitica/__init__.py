"""
Dominio de Analytics y Datamarts.

Contiene modelos optimizados para consultas analíticas rápidas.
Estos modelos están desnormalizados y diseñados para performance
en queries de reporting y dashboards.
"""

from .models import DatamartEpidemiologia

__all__ = ["DatamartEpidemiologia"]
