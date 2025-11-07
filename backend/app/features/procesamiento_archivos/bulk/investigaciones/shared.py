"""
Funciones compartidas para investigaciones y contactos.
"""

from datetime import datetime
from typing import Any, Optional

import pandas as pd

from app.core.shared.enums import OrigenFinanciamiento

# Import funciones del shared principal
from ..shared import (
    safe_int,
    safe_date,
    safe_bool,
    clean_string,
    get_current_timestamp,
    has_any_value,
)

# Re-exportar para mantener compatibilidad
__all__ = [
    "map_origen_financiamiento",
    "safe_int",
    "safe_date",
    "safe_bool",
    "clean_string",
    "get_current_timestamp",
    "has_any_value",
]


def map_origen_financiamiento(value: Any) -> Optional[OrigenFinanciamiento]:
    """Mapea a enum OrigenFinanciamiento."""
    if pd.isna(value) or value is None:
        return None
    try:
        str_value = str(value).upper().strip()
        # Remover acentos comunes
        str_value = (
            str_value.replace("Ú", "U")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Á", "A")
            .replace("É", "E")
        )
        return OrigenFinanciamiento(str_value)
    except ValueError:
        return None
