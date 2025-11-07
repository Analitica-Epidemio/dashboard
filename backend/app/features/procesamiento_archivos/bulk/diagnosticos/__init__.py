"""
Diagnostics bulk processors.

This package handles all diagnostic-related bulk operations:
- Diagnostics (diagnosticos_eventos.py)
- Studies (estudios.py)
- Treatments (tratamientos.py)
- Hospitalizations (internaciones.py)

USAGE:
  from bulk.diagnosticos import DiagnosticosProcessor

  processor = DiagnosticosProcessor(context, logger)
  processor.upsert_diagnosticos_eventos(df, evento_mapping)
  processor.upsert_estudios_eventos(df, evento_mapping)
  processor.upsert_tratamientos_eventos(df, evento_mapping)
  processor.upsert_internaciones_eventos(df, evento_mapping)
"""

from typing import Dict

import pandas as pd

from ..shared import BulkOperationResult


class DiagnosticosProcessor:
    """
    Unified manager for all diagnostic-related bulk operations.
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

        # Import here to avoid circular dependencies
        from .diagnosticos_eventos import DiagnosticosEventosProcessor
        from .estudios import EstudiosProcessor
        from .tratamientos import TratamientosProcessor
        from .internaciones import InternacionesProcessor

        # Initialize all sub-processors
        self.diagnosticos = DiagnosticosEventosProcessor(context, logger)
        self.estudios = EstudiosProcessor(context, logger)
        self.tratamientos = TratamientosProcessor(context, logger)
        self.internaciones = InternacionesProcessor(context, logger)

    # Delegate methods to sub-processors
    def upsert_diagnosticos_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert diagnostic events."""
        return self.diagnosticos.upsert_diagnosticos_eventos(df, evento_mapping)

    def upsert_estudios_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert study events."""
        return self.estudios.upsert_estudios_eventos(df, evento_mapping)

    def upsert_tratamientos_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert treatment events."""
        return self.tratamientos.upsert_tratamientos_eventos(df, evento_mapping)

    def upsert_internaciones_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert hospitalization events."""
        return self.internaciones.upsert_internaciones_eventos(df, evento_mapping)


__all__ = [
    "DiagnosticosProcessor",
]
