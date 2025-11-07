"""
Constantes centralizadas para el procesamiento de archivos epidemiológicos.

Centraliza todos los mapeos, configuraciones y constantes que estaban
duplicados en múltiples archivos.
"""

from enum import Enum
from typing import Dict, List, Set

from app.core.shared.enums import SexoBiologico, TipoDocumento

from .columns import (
    BOOLEAN_COLUMNS as BOOLEAN_COLUMNS_LIST,
)
from .columns import (
    DATE_COLUMNS as DATE_COLUMNS_LIST,
)
from .columns import (
    NUMERIC_COLUMNS as NUMERIC_COLUMNS_LIST,
)
from .columns import (
    Columns,
)


class ProcessingStage(Enum):
    """Etapas del procesamiento de archivos."""

    LOADING = "loading"
    VALIDATION = "validation"
    CLASSIFICATION = "classification"
    NORMALIZATION = "normalization"
    REPORTING = "reporting"
    COMPLETED = "completed"


class ProcessingStatus(Enum):
    """Estados del procesamiento."""

    SUCCESS = "SUCCESS"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"


# === CONFIGURACIÓN DE PROCESAMIENTO ===

# Configuración de batch sizes optimizada para 14k+ registros
BATCH_SIZES = {
    "default": 1000,
    "bulk_insert": 2000,
    "validation": 5000,
    "geography": 500,  # Para evitar lock de tablas geográficas
    "references": 1000,
}

# Configuración de performance
PERFORMANCE_CONFIG = {
    "connection_pool_size": 20,
    "max_concurrent_batches": 4,
    "memory_limit_mb": 512,
    "query_timeout_seconds": 30,
}

# === ESQUEMA CSV ===

# NOTA: Las listas de columnas ahora se importan desde columns.py
# para mantener sincronización con el frontend y proveer type checking

# Columnas que requieren normalización de mayúsculas
UPPERCASE_COLUMNS: List[str] = [
    Columns.EVENTO.name,
    Columns.CLASIFICACION_MANUAL.name,
    Columns.SEXO.name,
    Columns.TIPO_DOC.name,
    Columns.PROVINCIA_RESIDENCIA.name,
    Columns.PROVINCIA_CARGA.name,
]

# === MAPEOS DE NORMALIZACIÓN ===
# Mapeo de tipos de documento
DOCUMENTO_MAPPING: Dict[str, TipoDocumento] = {
    "DNI": TipoDocumento.DNI,
    "D.N.I.": TipoDocumento.DNI,
    "D.N.I": TipoDocumento.DNI,
    "DOCUMENTO": TipoDocumento.DNI,
    "LC": TipoDocumento.LIBRETA_CIVICA,
    "L.C.": TipoDocumento.LIBRETA_CIVICA,
    "LE": TipoDocumento.LIBRETA_ENROLAMIENTO,
    "L.E.": TipoDocumento.LIBRETA_ENROLAMIENTO,
    "CI": TipoDocumento.CEDULA_IDENTIDAD,
    "C.I.": TipoDocumento.CEDULA_IDENTIDAD,
    "CEDULA": TipoDocumento.CEDULA_IDENTIDAD,
    "PAS": TipoDocumento.PASAPORTE,
    "PASAPORTE": TipoDocumento.PASAPORTE,
    "PASSPORT": TipoDocumento.PASAPORTE,
}

# Mapeo de sexo biológico
SEXO_MAPPING: Dict[str, SexoBiologico] = {
    "MASCULINO": SexoBiologico.MASCULINO,
    "MASC": SexoBiologico.MASCULINO,
    "HOMBRE": SexoBiologico.MASCULINO,
    "H": SexoBiologico.MASCULINO,
    "M": SexoBiologico.MASCULINO,
    "FEMENINO": SexoBiologico.FEMENINO,
    "FEM": SexoBiologico.FEMENINO,
    "MUJER": SexoBiologico.FEMENINO,
    "F": SexoBiologico.FEMENINO,
    "INDETERMINADO": SexoBiologico.NO_ESPECIFICADO,
    "INDEFINIDO": SexoBiologico.NO_ESPECIFICADO,
    "IND": SexoBiologico.NO_ESPECIFICADO,
    "X": SexoBiologico.NO_ESPECIFICADO,
}

# Mapeo de provincias normalizadas
PROVINCIA_MAPPING: Dict[str, str] = {
    "CABA": "CIUDAD AUTÓNOMA DE BUENOS AIRES",
    "C.A.B.A.": "CIUDAD AUTÓNOMA DE BUENOS AIRES",
    "CAPITAL FEDERAL": "CIUDAD AUTÓNOMA DE BUENOS AIRES",
    "BS AS": "BUENOS AIRES",
    "BS. AS.": "BUENOS AIRES",
    "TIERRA DEL FUEGO": "TIERRA DEL FUEGO, ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR",
    "TDF": "TIERRA DEL FUEGO, ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR",
}

# Mapeo de valores booleanos
BOOLEAN_MAPPING: Dict[str, bool] = {
    "SI": True,
    "SÍ": True,
    "S": True,
    "1": True,
    "TRUE": True,
    "YES": True,
    "NO": False,
    "N": False,
    "0": False,
    "FALSE": False,
    "NO": False,
}

# === VALIDACIÓN ===

# Valores que se consideran nulos/vacíos
NULL_VALUES: Set[str] = {
    "",
    " ",
    "N/A",
    "n/a",
    "NULL",
    "null",
    "None",
    "NONE",
    "nan",
    "NaN",
}

# Límites de validación
VALIDATION_LIMITS = {
    "min_age": 0,
    "max_age": 150,
    "max_string_length": 500,
    "max_document_number": 999999999,
    "min_year": 1900,
    "max_year": 2100,
}

# Configuración de alertas
ALERT_THRESHOLDS = {
    "error_rate_high": 0.10,  # 10%+ errores = alerta alta
    "classification_rate_low": 80,  # <80% clasificación = alerta media
    "performance_slow": 10,  # <10 rows/sec = alerta baja
    "null_percentage_high": 30,  # >30% nulls = alerta media
}

# === CONFIGURACIÓN DE SQL ===
# (SQL Templates eliminados - ahora usamos SQLAlchemy 2.0 nativo)

# === METADATA EXTRACTION ===

# Tipos ENO que requieren extracción de metadata especial
METADATA_EXTRACTION_TYPES: Set[str] = {
    "Rabia animal",
    "Lesiones graves por mordedura de perro",
}

# === LOGGING ===

# Configuración de logging estructurado
LOG_FIELDS = {
    "performance": ["stage", "duration_ms", "rows_processed", "memory_mb"],
    "errors": ["stage", "error_type", "row_id", "details"],
    "business": ["event_type", "classification", "entities_created"],
}

# === VALIDATION CONSTANTS (for validator.py) ===
# Using EpiColumns instead of hardcoded strings

# Boolean columns for validation (using EpiColumns)
BOOLEAN_COLUMNS: Set[str] = set(BOOLEAN_COLUMNS_LIST)

# Date columns for validation (using EpiColumns)
DATE_COLUMNS: Set[str] = set(DATE_COLUMNS_LIST)

# Integer columns for validation (using EpiColumns)
INTEGER_COLUMNS: Set[str] = set(NUMERIC_COLUMNS_LIST)

# Numeric columns for validation (using EpiColumns)
NUMERIC_COLUMNS: Set[str] = set(NUMERIC_COLUMNS_LIST)

# String columns that require cleaning (using EpiColumns)
STRING_COLUMNS: Set[str] = {
    Columns.NOMBRE.name,
    Columns.APELLIDO.name,
    Columns.NRO_DOC.name,
    Columns.CALLE_DOMICILIO.name,
    Columns.NUMERO_DOMICILIO.name,
    Columns.LOCALIDAD_RESIDENCIA.name,
    Columns.DEPARTAMENTO_RESIDENCIA.name,
    Columns.PROVINCIA_RESIDENCIA.name,
    Columns.PAIS_RESIDENCIA.name,
    Columns.ESTAB_CLINICA.name,
    Columns.ESTABLECIMIENTO_EPI.name,
    Columns.ESTABLECIMIENTO_CARGA.name,
}

# Required columns that must be present (using EpiColumns)
REQUIRED_COLUMNS: Set[str] = {
    Columns.IDEVENTOCASO.name,
    Columns.EVENTO.name,
    Columns.CODIGO_CIUDADANO.name,
}

# Text column processing (using EpiColumns)
TEXT_COLUMNS: Set[str] = STRING_COLUMNS.union(
    {
        Columns.OBSERVACIONES.name,
        Columns.ANTECEDENTE_EPIDEMIOLOGICO.name,
        Columns.NOMBRE_LUGAR_OCURRENCIA.name,
        Columns.TIPO_LUGAR_OCURRENCIA.name,
        Columns.LOCALIDAD_AMBITO_OCURRENCIA.name,
        Columns.TIPO_Y_LUGAR_INVESTIGACION.name,
        Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name,
        Columns.RESULTADO_TRATAMIENTO.name,
        Columns.DETERMINACION.name,
        Columns.TECNICA.name,
        Columns.RESULTADO.name,
        Columns.VACUNA.name,
        Columns.COMORBILIDAD.name,
    }
)

# Boolean value mapping (keeping existing mapping - these are data values, not column names)
BOOLEAN_MAPPING: Dict[str, bool] = {
    "SI": True,
    "SÍ": True,
    "S": True,
    "YES": True,
    "Y": True,
    "1": True,
    "VERDADERO": True,
    "TRUE": True,
    "NO": False,
    "N": False,
    "0": False,
    "FALSO": False,
    "FALSE": False,
}

# NULL values that should be treated as None (keeping existing - these are data values, not column names)
NULL_VALUES: Set[str] = {
    "",
    " ",
    "  ",
    "   ",
    "NULL",
    "null",
    "None",
    "none",
    "N/A",
    "n/a",
    "NA",
    "na",
    "#N/A",
    "#NULL!",
    "NaN",
    "nan",
    "-",
    "--",
    "---",
    "Sin especificar",
    "No especificado",
    "Desconocido",
    "DESCONOCIDO",
}
