"""
Citizen bulk processors.

This package handles all citizen-related bulk operations:
- Core citizen data (processor.py)
- Addresses and links (domicilios.py)
- Trips (viajes.py)
- Comorbidities (comorbilidades.py)

USAGE:
  from bulk.ciudadanos import CiudadanosManager

  manager = CiudadanosManager(context, logger)
  manager.upsert_ciudadanos(df)
  manager.upsert_ciudadanos_domicilios(df)
  manager.upsert_viajes(df)
  manager.upsert_comorbilidades(df)
"""

from typing import Dict

import polars as pl

from .comorbilidades import ComorbilidadesProcessor
from .domicilios import DomiciliosProcessor
from .processor import CiudadanosProcessor
from .viajes import ViajesProcessor
from ..shared import BulkOperationResult


class CiudadanosManager:
    """
    Unified manager for all citizen-related bulk operations.

    Combines processors for citizens, addresses, trips, and comorbidities.
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

        # Initialize all sub-processors
        self.ciudadanos = CiudadanosProcessor(context, logger)
        self.domicilios = DomiciliosProcessor(context, logger)
        self.viajes = ViajesProcessor(context, logger)
        self.comorbilidades = ComorbilidadesProcessor(context, logger)

    # Delegate methods to sub-processors
    def upsert_ciudadanos(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert citizens."""
        return self.ciudadanos.upsert_ciudadanos(df)

    def upsert_ciudadanos_domicilios(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert addresses and citizen-address links."""
        return self.domicilios.upsert_ciudadanos_domicilios(df)

    def upsert_ciudadanos_datos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert citizen data linked to events."""
        return self.ciudadanos.upsert_ciudadanos_datos(df)

    def upsert_viajes(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert citizen trips."""
        return self.viajes.upsert_viajes(df)

    def upsert_comorbilidades(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert citizen comorbidities."""
        return self.comorbilidades.upsert_comorbilidades(df)


__all__ = [
    "CiudadanosManager",
    "CiudadanosProcessor",
    "DomiciliosProcessor",
    "ViajesProcessor",
    "ComorbilidadesProcessor",
]
