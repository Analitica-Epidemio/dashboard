"""
Shared utilities for bulk processors.

Consolidates:
- BulkOperationResult (result dataclass)
- Data conversion functions (safe_int, clean_string, etc.)
- BulkProcessorBase (base class with delegation)
- Pandas vectorization helpers
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import pandas as pd
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


# ===== DATA CONVERSION FUNCTIONS =====


def safe_int(value: Any) -> Optional[int]:
    """Conversión segura a int."""
    if pd.isna(value) or value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def safe_date(value: Any):
    """
    Conversión segura de datetime a date.

    Las fechas ya vienen parseadas por read_csv(parse_dates=..., dayfirst=True),
    este método solo convierte datetime → date y maneja edge cases.

    IMPORTANTE: pd.NaT.date() devuelve NaT (no None), lo que causa errores en PostgreSQL.
    Debemos verificar pd.isna() ANTES de llamar .date().
    """
    if pd.isna(value) or value is None:
        return None
    try:
        # Caso más común: ya es datetime (viene de parse_dates)
        if hasattr(value, "date"):
            result = value.date()
            # CRÍTICO: verificar si el resultado es NaT
            if pd.isna(result):
                return None
            return result
        # Fallback: parsear string si es necesario
        if isinstance(value, str):
            return pd.to_datetime(value, dayfirst=True).date()
        return pd.to_datetime(value).date()
    except (ValueError, TypeError):
        return None


def safe_bool(value: Any) -> Optional[bool]:
    """Mapea a boolean usando BOOLEAN_MAPPING."""
    if pd.isna(value) or value is None:
        return None
    try:
        str_value = str(value).upper().strip()
        return BOOLEAN_MAPPING.get(str_value)
    except (ValueError, TypeError):
        return None


def clean_string(value: Any) -> Optional[str]:
    """Limpieza de strings - strip y convierte vacíos a None."""
    if pd.isna(value) or value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


# ===== ENUM MAPPING =====


def map_tipo_documento(value: Any) -> Optional[TipoDocumento]:
    """Mapea a enum TipoDocumento."""
    if pd.isna(value) or value is None:
        return None
    return DOCUMENTO_MAPPING.get(str(value).upper())


def map_sexo(value: Any) -> Optional[SexoBiologico]:
    """Mapea a enum SexoBiologico."""
    if pd.isna(value) or value is None:
        return None
    return SEXO_MAPPING.get(str(value).upper())


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


def map_frecuencia_ocurrencia(value: Any) -> Optional[FrecuenciaOcurrencia]:
    """Mapea a enum FrecuenciaOcurrencia."""
    if pd.isna(value) or value is None:
        return None
    try:
        # Normalizar a formato del enum
        frecuencia_normalizada = str(value).upper().strip().replace(" ", "_")
        return FrecuenciaOcurrencia(frecuencia_normalizada)
    except ValueError:
        return None


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
    df: pd.DataFrame,
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
    # 1. Extraer valores únicos del CSV
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


# ===== PANDAS VECTORIZATION HELPERS =====


def vectorized_dict_builder(
    df: pd.DataFrame,
    column_mappings: Dict[str, str | Callable],
    timestamp: datetime | None = None,
) -> List[Dict[str, Any]]:
    """
    Construye lista de dicts usando operaciones vectorizadas.

    MUCHO más rápido que df.apply(lambda row: {...}).

    Args:
        df: DataFrame source
        column_mappings: {
            "output_key": "column_name",  # Copia directa
            "output_key": callable,        # Función sobre columna
        }
        timestamp: Timestamp para created_at/updated_at

    Returns:
        List[Dict] listo para bulk insert

    Example:
        >>> mappings = {
        ...     "nombre": "NOMBRE_COL",
        ...     "edad": lambda df: df["EDAD_COL"].astype('Int64'),
        ...     "created_at": lambda df: timestamp,
        ... }
        >>> records = vectorized_dict_builder(df, mappings, timestamp)
    """
    result_dict = {}

    for output_key, source in column_mappings.items():
        if callable(source):
            # Función custom sobre el DataFrame
            result_dict[output_key] = source(df)
        else:
            # Columna directa
            result_dict[output_key] = df[source]

    # Convertir a records (más rápido que apply)
    return pd.DataFrame(result_dict).to_dict("records")


def clean_string_column(series: pd.Series) -> pd.Series:
    """
    Limpia columna de strings vectorialmente.

    - Strip espacios
    - Convierte vacíos a None
    - Maneja NaN correctamente
    """
    return series.str.strip().replace("", None).replace("nan", None)


def safe_int_column(series: pd.Series) -> pd.Series:
    """Convierte columna a Int64 (nullable)."""
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def safe_bool_column(series: pd.Series, true_values: List[str] = None) -> pd.Series:
    """
    Convierte columna a boolean.

    Args:
        series: Serie a convertir
        true_values: Valores que se consideran True
    """
    if true_values is None:
        true_values = ["SI", "S", "TRUE", "1", "YES", "Y"]

    return series.astype(str).str.upper().str.strip().isin(true_values)


def has_valid_value(series: pd.Series) -> pd.Series:
    """
    Verifica si la serie tiene valores válidos (no NaN, no '', no 'nan').

    Returns:
        Serie booleana
    """
    return (
        series.notna()
        & (series.astype(str) != "nan")
        & (series.astype(str).str.strip() != "")
    )


# ===== BASE CLASS =====


class BulkProcessorBase:
    """
    Clase base con helpers comunes.

    TODOS los métodos delegan a funciones puras.
    Esto permite:
    1. Testear funciones sin instanciar clases
    2. Usar funciones directamente si no necesitas herencia
    3. Mantener compatibilidad con código existente
    """

    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

    # ===== DELEGATES A FUNCIONES PURAS =====
    # Mantiene compatibilidad con código existente que llama self._safe_int()

    def _safe_int(self, value):
        """Delegate to safe_int()"""
        return safe_int(value)

    def _safe_date(self, value):
        """Delegate to safe_date()"""
        return safe_date(value)

    def _safe_bool(self, value):
        """Delegate to safe_bool()"""
        return safe_bool(value)

    def _clean_string(self, value):
        """Delegate to clean_string()"""
        return clean_string(value)

    def _map_tipo_documento(self, value):
        """Delegate to map_tipo_documento()"""
        return map_tipo_documento(value)

    def _map_sexo(self, value):
        """Delegate to map_sexo()"""
        return map_sexo(value)

    def _map_origen_financiamiento(self, value):
        """Delegate to map_origen_financiamiento()"""
        return map_origen_financiamiento(value)

    def _map_frecuencia_ocurrencia(self, value):
        """Delegate to map_frecuencia_ocurrencia()"""
        return map_frecuencia_ocurrencia(value)

    def _get_current_timestamp(self):
        """Delegate to get_current_timestamp()"""
        return get_current_timestamp()
