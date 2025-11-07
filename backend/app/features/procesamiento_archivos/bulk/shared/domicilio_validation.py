"""
Validación compartida de domicilios.

Usado por DomiciliosProcessor y EventosProcessor para asegurar
que no se creen domicilios con calles inválidas.
"""

import re
import pandas as pd


# Patrones de calles inválidas
INVALID_CALLE_PATTERNS = [
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


def is_valid_street_name(calle: str) -> bool:
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
    # Validar None, NaN, vacío o solo espacios
    if pd.isna(calle) or calle is None or not str(calle).strip():
        return False

    calle_clean = str(calle).strip().upper()

    # Verificar patrones inválidos
    for pattern in INVALID_CALLE_PATTERNS:
        if re.match(pattern, calle_clean, re.IGNORECASE):
            return False

    # Rechazar si termina con " 0" (ej: "AV SAN MARTIN 0", "ESTRADA 0")
    if calle_clean.endswith(" 0"):
        return False

    # Rechazar si solo contiene caracteres especiales y espacios
    if re.match(r"^[\s\.\-_,]+$", calle_clean):
        return False

    # Si la calle es muy corta (menos de 3 caracteres no espacios), probablemente no es válida
    calle_sin_espacios = calle_clean.replace(" ", "")
    if len(calle_sin_espacios) < 3:
        return False

    return True
