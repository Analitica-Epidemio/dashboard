"""
Shared utilities for bulk processors - POLARS PURO.

Consolidates:
- BulkOperationResult (result dataclass)
- Polars expression builders (para mapeos, conversiones, etc.)
- BulkProcessorBase (base class con helpers Polars)
- Catalog get-or-create patterns
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import polars as pl
import re
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from app.core.shared.enums import (
    FrecuenciaOcurrencia,
    OrigenFinanciamiento,
    SexoBiologico,
    TipoDocumento,
)

from ..config.constants import BOOLEAN_MAPPING, DOCUMENTO_MAPPING, SEXO_MAPPING


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
    # Validar None, vacío o solo espacios
    if calle is None or not str(calle).strip():
        return False

    calle_clean = str(calle).strip().upper()

    # Verificar patrones inválidos
    for pattern in INVALID_CALLE_PATTERNS:
        if re.match(pattern, calle_clean, re.IGNORECASE):
            return False

    # Rechazar si solo contiene caracteres especiales y espacios
    if re.match(r"^[\s\.\-_,]+$", calle_clean):
        return False

    # Si la calle es muy corta (menos de 3 caracteres no espacios), probablemente no es válida
    calle_sin_espacios = calle_clean.replace(" ", "")
    if len(calle_sin_espacios) < 3:
        return False

    return True


# Type variable for SQLAlchemy models
T = TypeVar("T")


# ===== RESULT DATACLASS =====


@dataclass
class BulkOperationResult:
    """Resultado de operación bulk con métricas."""

    inserted_count: int
    updated_count: int
    skipped_count: int
    errors: List[str]
    duration_seconds: float


# ===== POLARS EXPRESSION BUILDERS =====
# Estas funciones retornan expresiones Polars para usar en .select() / .with_columns()


def pl_safe_int(col_name: str) -> pl.Expr:
    """
    Expresión Polars para conversión segura a Int64.

    Usage:
        df.select(pl_safe_int("edad").alias("edad"))
    """
    return pl.col(col_name).cast(pl.Int64, strict=False)


def pl_safe_date(col_name: str) -> pl.Expr:
    """
    Expresión Polars para conversión segura a Date.

    Maneja múltiples formatos de fecha comunes en archivos CSV.

    Usage:
        df.select(pl_safe_date("fecha_nacimiento").alias("fecha_nacimiento"))
    """
    return pl.col(col_name).cast(pl.Date, strict=False)


def pl_clean_string(col_name: str) -> pl.Expr:
    """
    Expresión Polars para limpieza de strings.

    - Strip espacios
    - Convierte strings vacíos a null

    Usage:
        df.select(pl_clean_string("nombre").alias("nombre"))
    """
    return (
        pl.col(col_name)
        .str.strip_chars()
        .replace("", None)
    )


def pl_map_sexo(col_name: str) -> pl.Expr:
    """
    Expresión Polars para mapear sexo a enum.

    Mapea:
    - M / MASCULINO -> MASCULINO
    - F / FEMENINO -> FEMENINO
    - X / NO_ESPECIFICADO -> NO_ESPECIFICADO

    Usage:
        df.select(pl_map_sexo("sexo").alias("sexo_biologico"))
    """
    col_upper = pl.col(col_name).str.to_uppercase().str.strip_chars()

    return (
        pl.when(
            (col_upper == "M") |
            (col_upper == "MASCULINO")
        )
        .then(pl.lit(SexoBiologico.MASCULINO.value))
        .when(
            (col_upper == "F") |
            (col_upper == "FEMENINO")
        )
        .then(pl.lit(SexoBiologico.FEMENINO.value))
        .when(
            (col_upper == "X") |
            (col_upper == "NO_ESPECIFICADO")
        )
        .then(pl.lit(SexoBiologico.NO_ESPECIFICADO.value))
        .otherwise(None)
    )


def pl_map_tipo_documento(col_name: str) -> pl.Expr:
    """
    Expresión Polars para mapear tipo de documento a enum.

    Usage:
        df.select(pl_map_tipo_documento("tipo_doc").alias("tipo_documento"))
    """
    expr = pl.col(col_name).str.to_uppercase().str.strip_chars()

    # Construir mapeo usando when/then
    result = pl.lit(None)  # Default
    for key, value in DOCUMENTO_MAPPING.items():
        result = pl.when(expr == key).then(pl.lit(value.value)).otherwise(result)

    return result


def pl_map_boolean(col_name: str) -> pl.Expr:
    """
    Expresión Polars para mapear valores a boolean.

    Usa BOOLEAN_MAPPING definido en constants.py

    Usage:
        df.select(pl_map_boolean("internado").alias("internado"))
    """
    expr = pl.col(col_name).str.to_uppercase().str.strip_chars()

    # Construir mapeo usando when/then
    result = pl.lit(None)  # Default
    for key, value in BOOLEAN_MAPPING.items():
        if value is not None:  # Solo mapear valores definidos
            result = pl.when(expr == key).then(pl.lit(value)).otherwise(result)

    return result


def pl_clean_numero_domicilio(col_name: str) -> pl.Expr:
    """
    Expresión Polars para limpiar número de domicilio.

    Maneja:
    - null/None -> None
    - floats -> convierte a int primero (1332.0 -> "1332")
    - ints -> convierte a string ("1332")
    - strings -> strip
    - strings vacíos -> None

    Usage:
        df.select(pl_clean_numero_domicilio("numero").alias("numero_clean"))
    """
    return (
        pl.when(pl.col(col_name).is_null())
        .then(None)
        .when(pl.col(col_name).cast(pl.Utf8).str.strip_chars() == "")
        .then(None)
        .otherwise(
            # Si es float/int, convertir a int primero para quitar decimales
            pl.when(pl.col(col_name).cast(pl.Float64, strict=False).is_not_null())
            .then(
                pl.col(col_name)
                .cast(pl.Float64, strict=False)
                .cast(pl.Int64, strict=False)
                .cast(pl.Utf8)
            )
            .otherwise(
                # Si no es numeric, usar como string
                pl.col(col_name).cast(pl.Utf8).str.strip_chars()
            )
        )
    )


def pl_col_or_null(df: pl.DataFrame, col_name: str, transform_fn=None) -> pl.Expr:
    """
    Helper para columnas opcionales - retorna expresión o null.

    Si la columna existe en el DataFrame, aplica transform_fn (o limpieza por defecto).
    Si no existe, retorna pl.lit(None).

    Args:
        df: DataFrame a verificar
        col_name: Nombre de la columna
        transform_fn: Función que toma col_name y retorna pl.Expr (ej: pl_clean_string, pl_safe_date)

    Usage:
        df.select([
            pl_col_or_null(df, "nombre").alias("nombre"),  # Limpieza por defecto
            pl_col_or_null(df, "fecha", pl_safe_date).alias("fecha"),  # Con transformación
        ])
    """
    if col_name in df.columns:
        if transform_fn is None:
            # Por defecto: limpiar strings
            return pl_clean_string(col_name)
        else:
            # Aplicar transformación personalizada
            return transform_fn(col_name)
    else:
        return pl.lit(None)


# ===== GENERAL UTILITIES =====


def get_current_timestamp() -> datetime:
    """Get current timestamp for created_at/updated_at."""
    return datetime.utcnow()


def has_any_value(values: list) -> bool:
    """
    Verifica si algún valor en la lista es válido (no None).

    Útil para filtrar registros que tienen al menos un campo relevante.
    """
    return any(v is not None for v in values)


# ===== GET-OR-CREATE CATALOG PATTERN =====


def get_or_create_catalog(
    session: Any,  # Session type
    model: Type[T],
    df,  # Accept both pandas and Polars DataFrames
    column: str,
    key_field: str = "codigo",
    name_field: str = "nombre",
    transform_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
    existing_filter: Optional[Callable] = None,
    has_unique_constraint: bool = True,
) -> Dict[str, int]:
    """
    Patrón genérico para get-or-create de catálogos.

    Elimina duplicación de código en _get_or_create_* methods.

    Args:
        session: SQLAlchemy session
        model: Modelo SQLAlchemy (ej: GrupoEno, Sintoma, etc)
        df: DataFrame con datos
        column: Nombre de columna del CSV (str) - NO pasar Column object
        key_field: Campo de la tabla para buscar (default: "codigo")
        name_field: Campo de nombre (default: "nombre")
        transform_fn: Función para transformar valor CSV → dict para insert
        existing_filter: Filtro adicional para query existentes
        has_unique_constraint: Si la tabla tiene unique constraint en key_field (default: True)

    Returns:
        Dict mapping key → id

    Example:
        >>> # Caso simple
        >>> mapping = get_or_create_catalog(
        ...     session, Sintoma, df, "SINTOMA",
        ...     transform_fn=lambda val: {
        ...         "codigo": val.lower(),
        ...         "nombre": val.title(),
        ...         "created_at": datetime.utcnow(),
        ...     }
        ... )
    """
    # 1. Extraer valores únicos del CSV - POLARS PURO
    if isinstance(df, pl.DataFrame):
        # Polars operations
        valores = df.filter(pl.col(column).is_not_null()).select(column).unique().to_series().to_list()
    else:
        # Pandas fallback (legacy, should not be used)
        valores = df[column].dropna().unique()

    valores_clean = [str(v).strip() for v in valores if str(v).strip()]

    if not valores_clean:
        return {}

    # 2. Si hay transform_fn, aplicarla para obtener las keys que vamos a buscar/crear
    # Mapeo: valor_original (CSV) -> key_transformada (para buscar en BD)
    valor_to_key = {}
    if transform_fn:
        for valor in valores_clean:
            try:
                record = transform_fn(valor)
                key_value = record.get(key_field)
                if key_value:
                    valor_to_key[valor] = key_value
            except Exception as e:
                # Si falla la transformación, skip este valor
                continue
    else:
        # Sin transformación, usar valores directamente
        valor_to_key = {v: v for v in valores_clean}

    if not valor_to_key:
        return {}

    # 3. Buscar existentes en BD usando las keys transformadas
    keys_to_search = list(set(valor_to_key.values()))
    model_key = getattr(model, key_field)
    stmt = select(model.id, model_key)

    if existing_filter:
        stmt = stmt.where(existing_filter)
    else:
        stmt = stmt.where(model_key.in_(keys_to_search))

    existing_mapping = {
        getattr(row, key_field): row.id for row in session.execute(stmt).all()
    }

    # 4. Identificar faltantes (comparar keys transformadas, no valores originales)
    existing_keys = set(existing_mapping.keys())
    keys_set = set(keys_to_search)
    faltantes_keys = keys_set - existing_keys

    if not faltantes_keys:
        return existing_mapping

    # 5. Crear registros faltantes
    # Necesitamos mapear de key_faltante -> valor_original para aplicar transform_fn
    key_to_valor = {v: k for k, v in valor_to_key.items()}

    timestamp = get_current_timestamp()
    nuevos = []

    for key_faltante in faltantes_keys:
        valor_original = key_to_valor.get(key_faltante, key_faltante)

        if transform_fn:
            record = transform_fn(valor_original)
        else:
            # Default: simple key-value
            record = {
                key_field: key_faltante,
                name_field: valor_original,
            }

        # Agregar timestamps si no están
        record.setdefault("created_at", timestamp)
        record.setdefault("updated_at", timestamp)
        nuevos.append(record)

    if nuevos:
        stmt = pg_insert(model.__table__).values(nuevos)

        # Usar ON CONFLICT solo si la tabla tiene unique constraint
        if has_unique_constraint:
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=[key_field])
            session.execute(upsert_stmt)
        else:
            # Sin constraint único, hacer INSERT directo
            # (la lógica previa ya filtró duplicados)
            session.execute(stmt)

        session.flush()

        # 6. Re-query para obtener IDs de TODOS (existentes + nuevos)
        stmt = select(model.id, model_key).where(model_key.in_(keys_to_search))
        existing_mapping = {
            getattr(row, key_field): row.id for row in session.execute(stmt).all()
        }

    return existing_mapping


# ===== BASE CLASS =====


class BulkProcessorBase:
    """
    Clase base para bulk processors con Polars puro.

    Proporciona acceso a:
    - context: Contexto de procesamiento con session, logger, etc.
    - logger: Logger para debugging
    - timestamp helper
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

    def _get_current_timestamp(self) -> datetime:
        """Get current timestamp for created_at/updated_at."""
        return get_current_timestamp()
