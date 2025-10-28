"""
Feature de geocodificación asíncrona de domicilios.
"""

from .tasks import geocode_pending_domicilios

__all__ = ["geocode_pending_domicilios"]
