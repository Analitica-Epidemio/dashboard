"""
Health bulk processors (samples and vaccines).

This package handles all health-related bulk operations:
- Samples (muestras.py)
- Vaccines (vacunas.py)

USAGE:
  from bulk.salud import SaludManager

  manager = SaludManager(context, logger)
  manager.upsert_muestras_eventos(df)
  manager.upsert_vacunas_ciudadanos(df)
"""

from typing import Dict

import polars as pl

from ..shared import BulkOperationResult


class SaludManager:
    """
    Unified manager for all health-related bulk operations.
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

        # Import here to avoid circular dependencies
        from .muestras import MuestrasProcessor
        from .vacunas import VacunasProcessor

        # Initialize all sub-processors
        self.muestras = MuestrasProcessor(context, logger)
        self.vacunas = VacunasProcessor(context, logger)

    # Delegate methods to sub-processors
    def upsert_muestras_eventos(
        self, df: pl.DataFrame, establecimiento_mapping: Dict[str, int], evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert event samples."""
        return self.muestras.upsert_muestras_eventos(df, establecimiento_mapping, evento_mapping)

    def upsert_vacunas_ciudadanos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert citizen vaccines."""
        return self.vacunas.upsert_vacunas_ciudadanos(df)


__all__ = [
    "SaludManager",
]
