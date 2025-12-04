"""
Event bulk processors.

This package handles all event-related bulk operations:
- Core event data (processor.py)
- Symptoms (sintomas.py)
- Epidemiological backgrounds (antecedentes.py)
- Places of occurrence (ambitos.py)
- Etiological agents (agentes.py)
- Catalogs (catalogs.py)

USAGE:
  from bulk.eventos import EventosManager

  manager = EventosManager(context, logger)
  manager.upsert_eventos(df, establecimiento_mapping)
  manager.upsert_sintomas_eventos(df, sintoma_mapping)
  manager.upsert_agentes_eventos(df, evento_mapping)
"""

from typing import Dict

import polars as pl

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
        from .agentes import AgentesExtractor
        from .ambitos import AmbitosProcessor
        from .antecedentes import AntecedentesProcessor
        from .processor import EventosProcessor
        from .sintomas import SintomasProcessor

        # Initialize all sub-processors
        self.eventos = EventosProcessor(context, logger)
        self.sintomas = SintomasProcessor(context, logger)
        self.antecedentes = AntecedentesProcessor(context, logger)
        self.ambitos = AmbitosProcessor(context, logger)
        self.agentes = AgentesExtractor(context, logger)

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

    def upsert_agentes_eventos(
        self, df: pl.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """
        Bulk upsert etiological agents detected in events.

        Extracts agents (viruses, bacteria, etc.) from CSV fields using
        deterministic rules defined per TipoEno in REGLAS_POR_TIPO_ENO.
        """
        return self.agentes.upsert_agentes_eventos(df, evento_mapping)

    # Helper methods exposed publicly
    def _get_or_create_sintomas(self, df: pl.DataFrame) -> Dict[str, int]:
        """Get or create symptom catalog entries."""
        return self.sintomas._get_or_create_sintomas(df)


__all__ = [
    "EventosManager",
]
