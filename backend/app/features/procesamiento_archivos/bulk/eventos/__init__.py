"""
Event bulk processors.

This package handles all event-related bulk operations:
- Core event data (processor.py)
- Symptoms (sintomas.py)
- Epidemiological backgrounds (antecedentes.py)
- Places of occurrence (ambitos.py)
- Catalogs (catalogs.py)

USAGE:
  from bulk.eventos import EventosManager

  manager = EventosManager(context, logger)
  manager.upsert_eventos(df, establecimiento_mapping)
  manager.upsert_sintomas_eventos(df, sintoma_mapping)
"""

import polars as pl
from typing import Dict

from ..shared import BulkOperationResult


class EventosManager:
    """
    Unified manager for all event-related bulk operations.

    Combines processors for events, symptoms, backgrounds, and places.
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

        # Import here to avoid circular dependencies
        from .processor import EventosProcessor
        from .sintomas import SintomasProcessor
        from .antecedentes import AntecedentesProcessor
        from .ambitos import AmbitosProcessor

        # Initialize all sub-processors
        self.eventos = EventosProcessor(context, logger)
        self.sintomas = SintomasProcessor(context, logger)
        self.antecedentes = AntecedentesProcessor(context, logger)
        self.ambitos = AmbitosProcessor(context, logger)

    # Delegate methods to sub-processors
    def upsert_eventos(
        self, df: pl.DataFrame, establecimiento_mapping: Dict
    ) -> Dict[int, int]:
        """Bulk upsert events."""
        return self.eventos.upsert_eventos(df, establecimiento_mapping)

    def upsert_sintomas_eventos(
        self, df: pl.DataFrame, sintoma_mapping: Dict[str, int]
    ) -> BulkOperationResult:
        """Bulk upsert event symptoms."""
        return self.sintomas.upsert_sintomas_eventos(df, sintoma_mapping)

    def upsert_antecedentes_epidemiologicos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert epidemiological backgrounds."""
        return self.antecedentes.upsert_antecedentes_epidemiologicos(df)

    def upsert_ambitos_concurrencia(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert places of occurrence."""
        return self.ambitos.upsert_ambitos_concurrencia(df)

    # Helper methods exposed publicly
    def _get_or_create_sintomas(self, df: pl.DataFrame) -> Dict[str, int]:
        """Get or create symptom catalog entries."""
        return self.sintomas._get_or_create_sintomas(df)


__all__ = [
    "EventosManager",
]
