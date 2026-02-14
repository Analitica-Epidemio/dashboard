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

import logging
from typing import TYPE_CHECKING

import polars as pl

from ..shared import BulkOperationResult

if TYPE_CHECKING:
    from ...config import ProcessingContext


class SaludManager:
    """
    Unified manager for all health-related bulk operations.
    """

    def __init__(self, context: "ProcessingContext", logger: logging.Logger) -> None:
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
        self,
        df: pl.DataFrame,
        establecimiento_mapping: dict[str, int],
        evento_mapping: dict[int, int],
    ) -> BulkOperationResult:
        """Bulk upsert event samples."""
        return self.muestras.upsert_muestras_eventos(
            df, establecimiento_mapping, evento_mapping
        )

    def upsert_vacunas_ciudadanos(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert citizen vaccines."""
        return self.vacunas.upsert_vacunas_ciudadanos(df)


__all__ = [
    "SaludManager",
]
