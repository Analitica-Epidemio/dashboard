"""
Investigation bulk processors.

Unified manager for:
- Investigaciones epidemiológicas
- Contactos y notificaciones
"""

from typing import Dict

import pandas as pd

from ..shared import BulkOperationResult


class InvestigacionesProcessor:
    """Unified manager for all investigation-related bulk operations."""

    def __init__(self, context, logger):
        from .contactos import ContactosProcessor
        from .investigaciones_eventos import InvestigacionesEventosProcessor

        self.investigaciones = InvestigacionesEventosProcessor(context, logger)
        self.contactos = ContactosProcessor(context, logger)

    def upsert_investigaciones_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de investigaciones de eventos."""
        return self.investigaciones.upsert_investigaciones_eventos(df, evento_mapping)

    def upsert_contactos_notificaciones(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de contactos y notificaciones."""
        return self.contactos.upsert_contactos_notificaciones(df)


__all__ = ["InvestigacionesProcessor"]
