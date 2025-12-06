"""
Utilidades compartidas para procesadores bulk - POLARS PURO.

Consolida:
- BulkOperationResult (dataclass de resultado)
- Builders de expresiones Polars (para mapeos, conversiones, etc.)
- BulkProcessorBase (clase base con helpers Polars)
- Patrones de get-or-create para catálogos
"""

import re
from typing import TypeVar

# Importar utilidades genéricas del core
from app.core.bulk import (
    BulkOperationResult,
    BulkProcessorBase,
    get_current_timestamp,
    get_or_create_catalog,
    has_any_value,
    pl_clean_numero_domicilio,
    pl_clean_string,
    pl_col_or_null,
    pl_map_boolean,
    pl_map_sexo,
    pl_map_tipo_documento,
    pl_safe_date,
    pl_safe_int,
)

__all__ = [
    "BulkOperationResult",
    "BulkProcessorBase",
    "get_current_timestamp",
    "get_or_create_catalog",
    "has_any_value",
    "pl_clean_numero_domicilio",
    "pl_clean_string",
    "pl_col_or_null",
    "pl_map_boolean",
    "pl_map_sexo",
    "pl_map_tipo_documento",
    "pl_safe_date",
    "pl_safe_int",
]

# Patrones de calles inválidas
PATRONES_CALLE_INVALIDA = [
    r"^s/n$",  # S/N
    r"^s/n\s+",  # S/N 0, S/N algo
    r"^sin\s+nombre",  # SIN NOMBRE
    r"^sin\s+calle",  # SIN CALLE
    r"^s/c$",  # S/C
    r"^s/c\s+",  # S/C 0
    r"^no\s+aplica",  # NO APLICA
    r"^codigo\s+\d+",  # CODIGO 676 552
    r"^chacra\s+\d+$",  # Chacra 97 (sin calle específica)
    # NOTA: RUTA X KM Y es VÁLIDA - Google Maps puede encontrarla
    r"^casa\s+\d+$",  # CASA 8, CASA 44
    r"^casa\s+\d+,",  # CASA 44, Alto Río Senguer
    r"^aldea\s+escolar",  # ALDEA ESCOLAR
    r"^zona\s+urbana",  # ZONA URBANA 0
    r"^\.$",  # .
    r"^\.\.$",  # ..
    r"^\.\.\s+\.\.",  # .. ..
    r"^0+$",  # 0, 00, 000
    r"^0+\s+0+$",  # 0 0
    r"^\d+\s+edificio",  # 1008 edificio 90
    r"^\d+\s+bis\s+norte",  # 10 BIS NORTE 586
    r"^\d+\s+\d+$",  # Solo números: 2 1667, 1333 419
    r"^\d+vdas",  # 20VDAS CASA 3
]


def es_nombre_calle_valido(calle: str) -> bool:
    """
    Valida si un nombre de calle es válido para geocodificación.

    Retorna False si:
    - Es None, vacío o solo espacios
    - Coincide con patrones de valores inválidos
    - Solo contiene puntos, guiones u otros caracteres especiales
    - Termina con " 0" (indica número no válido)
    - Es muy corta (menos de 3 caracteres)

    Args:
        calle: Nombre de calle a validar

    Returns:
        True si es válida, False si no
    """
    # Validar None, vacío o solo espacios
    if calle is None or not str(calle).strip():
        return False

    calle_limpia = str(calle).strip().upper()

    # Verificar patrones inválidos
    for patron in PATRONES_CALLE_INVALIDA:
        if re.match(patron, calle_limpia, re.IGNORECASE):
            return False

    # Rechazar si solo contiene caracteres especiales y espacios
    if re.match(r"^[\s\.\-_,]+$", calle_limpia):
        return False

    # Si la calle es muy corta (menos de 3 caracteres no espacios), probablemente no es válida
    calle_sin_espacios = calle_limpia.replace(" ", "")
    if len(calle_sin_espacios) < 3:
        return False

    return True


# Type variable for SQLAlchemy models
T = TypeVar("T")
