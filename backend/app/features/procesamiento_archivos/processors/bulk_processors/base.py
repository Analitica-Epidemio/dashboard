"""Base classes and helpers for bulk processors."""

from datetime import datetime
from typing import Any, Optional

import pandas as pd

from app.core.shared.enums import (
    FrecuenciaOcurrencia,
    OrigenFinanciamiento,
    SexoBiologico,
    TipoDocumento,
)

from ..core.constants import BOOLEAN_MAPPING, DOCUMENTO_MAPPING, SEXO_MAPPING


class BulkProcessorBase:
    """Base class with common helper methods for all bulk processors."""

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

    # === HELPER METHODS ===

    def _safe_int(self, value: Any) -> Optional[int]:
        """Conversión segura a int."""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))
        except Exception:
            return None

    def _safe_date(self, value: Any):
        """Conversión segura de datetime a date.

        Las fechas ya vienen parseadas por read_csv(parse_dates=..., dayfirst=True),
        este método solo convierte datetime → date y maneja edge cases.
        """
        if pd.isna(value) or value is None:
            return None
        try:
            # Caso más común: ya es datetime (viene de parse_dates)
            if hasattr(value, 'date'):
                return value.date()
            # Fallback: parsear string si es necesario
            if isinstance(value, str):
                return pd.to_datetime(value, dayfirst=True).date()
            return pd.to_datetime(value).date()
        except Exception:
            return None

    def _safe_bool(self, value: Any) -> Optional[bool]:
        """Mapea a boolean."""
        if pd.isna(value) or value is None:
            return None
        try:
            str_value = str(value).upper().strip()
            return BOOLEAN_MAPPING.get(str_value)
        except Exception:
            return None

    def _clean_string(self, value: Any) -> Optional[str]:
        """Limpieza de strings."""
        if pd.isna(value) or value is None:
            return None
        return str(value).strip() if str(value).strip() else None

    def _map_tipo_documento(self, value: Any) -> Optional[TipoDocumento]:
        """Mapea a enum real, no string."""
        if pd.isna(value) or value is None:
            return None
        return DOCUMENTO_MAPPING.get(str(value).upper())

    def _map_sexo(self, value: Any) -> Optional[SexoBiologico]:
        """Mapea a enum real."""
        if pd.isna(value) or value is None:
            return None
        return SEXO_MAPPING.get(str(value).upper())

    def _map_origen_financiamiento(self, value: Any) -> Optional[OrigenFinanciamiento]:
        """Mapea a enum OrigenFinanciamiento."""
        if pd.isna(value) or value is None:
            return None
        try:
            str_value = str(value).upper().strip()
            # Remover acentos comunes
            str_value = str_value.replace("Ú", "U").replace("Í", "I").replace("Ó", "O").replace("Á", "A").replace("É", "E")
            return OrigenFinanciamiento(str_value)
        except ValueError:
            self.logger.warning(f"Origen financiamiento no reconocido: {value}")
            return None

    def _map_frecuencia_ocurrencia(self, value: Any) -> Optional[FrecuenciaOcurrencia]:
        """Mapea a enum FrecuenciaOcurrencia."""
        if pd.isna(value) or value is None:
            return None
        try:
            # Normalizar a formato del enum
            frecuencia_normalizada = str(value).upper().strip().replace(" ", "_")
            return FrecuenciaOcurrencia(frecuencia_normalizada)
        except ValueError:
            self.logger.warning(f"Frecuencia no reconocida: {value}")
            return None

    def _get_current_timestamp(self):
        """Get current timestamp for created_at/updated_at."""
        return datetime.utcnow()