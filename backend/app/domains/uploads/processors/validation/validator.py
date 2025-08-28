"""
Validador simplificado y optimizado para archivos epidemiológicos.

Elimina redundancias y enfoca en validaciones críticas.
"""

import logging
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd

from ..core.base_processor import BatchProcessor, ProcessingContext
from ..core.columns import Columns
from ..core.constants import (
    BOOLEAN_COLUMNS,
    BOOLEAN_MAPPING,
    DATE_COLUMNS,
    DOCUMENTO_MAPPING,
    NULL_VALUES,
    NUMERIC_COLUMNS,
    PROVINCIA_MAPPING,
    REQUIRED_COLUMNS,
    SEXO_MAPPING,
    UPPERCASE_COLUMNS,
    VALIDATION_LIMITS,
    ProcessingStage,
)

logger = logging.getLogger(__name__)


class OptimizedDataValidator(BatchProcessor):
    """
    Validador de datos optimizado para máximo rendimiento.

    Características:
    - Validación vectorizada con pandas
    - Limpieza de datos en una pasada
    - Reportes estructurados de errores
    - Enfoque en validaciones críticas solamente
    """

    def __init__(self, context: ProcessingContext):
        super().__init__(context)
        self.validation_report = {"errors": [], "warnings": [], "stats": {}}

    def get_stage(self) -> ProcessingStage:
        """Etapa de validación."""
        return ProcessingStage.VALIDATION

    def process_batch(self, batch_df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y limpia un batch de datos.

        Args:
            batch_df: Batch de datos a validar

        Returns:
            Batch validado y limpio
        """
        self.logger.info(f"Validando batch de {len(batch_df)} registros")

        original_count = len(batch_df)

        # 1. Validación estructural crítica
        self._validate_structure(batch_df)

        # 2. Limpieza de datos vectorizada
        batch_df = self._clean_data_vectorized(batch_df)

        # 3. Conversión de tipos optimizada
        batch_df = self._convert_types_vectorized(batch_df)

        # 4. Validaciones críticas solamente
        self._validate_critical_values(batch_df)

        # 5. Actualizar estadísticas
        self._update_validation_stats(original_count, len(batch_df))

        self.logger.info(
            f"Validación completada: {len(batch_df)}/{original_count} registros válidos"
        )

        return batch_df

    def _validate_structure(self, df: pd.DataFrame) -> None:
        """Valida estructura crítica del DataFrame."""
        # Verificar columnas críticas solamente
        missing_critical = [col for col in REQUIRED_COLUMNS if col not in df.columns]

        if missing_critical:
            error_msg = f"Columnas críticas faltantes: {missing_critical}"
            self.validation_report["errors"].append(
                {
                    "type": "missing_critical_columns",
                    "columns": missing_critical,
                    "severity": "critical",
                }
            )
            self.context.stats.add_error(ProcessingStage.VALIDATION, error_msg)
            raise ValueError(error_msg)

        # Verificar que no esté vacío
        if df.empty:
            error_msg = "DataFrame vacío"
            self.validation_report["errors"].append(
                {"type": "empty_dataframe", "severity": "critical"}
            )
            self.context.stats.add_error(ProcessingStage.VALIDATION, error_msg)
            raise ValueError(error_msg)

        self.logger.debug(
            f"Estructura válida: {len(df.columns)} columnas, {len(df)} filas"
        )

    def _clean_data_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza vectorizada de datos para máximo rendimiento.

        Aplica todas las limpiezas en una sola pasada usando pandas vectorization.
        """
        self.logger.debug("Iniciando limpieza vectorizada")

        # Crear copia para evitar SettingWithCopyWarning
        df = df.copy()

        # 1. Limpiar strings: strip espacios
        string_cols = df.select_dtypes(include=["object"]).columns
        for col in string_cols:
            df[col] = df[col].astype(str).str.strip()

        # 2. Reemplazar valores nulos en una operación
        df = df.replace(list(NULL_VALUES), np.nan)

        # 3. Normalizar campos específicos a mayúsculas
        for col in UPPERCASE_COLUMNS:
            if col in df.columns:
                df[col] = df[col].str.upper()

        # 4. Normalizar provincias usando mapeo
        provincia_cols = [col for col in df.columns if "PROVINCIA" in col]
        for col in provincia_cols:
            if col in df.columns:
                df[col] = df[col].replace(PROVINCIA_MAPPING)

        # 5. Normalizar tipos de documento
        if Columns.TIPO_DOC in df.columns:
            df[Columns.TIPO_DOC] = df[Columns.TIPO_DOC].replace(
                {k: v.name for k, v in DOCUMENTO_MAPPING.items()}
            )

        # 6. Normalizar sexo
        if Columns.SEXO in df.columns:
            df[Columns.SEXO] = df[Columns.SEXO].replace(
                {k: v.name for k, v in SEXO_MAPPING.items()}
            )

        self.logger.debug("Limpieza vectorizada completada")

        return df

    def _convert_types_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Conversión de tipos vectorizada usando pandas.

        Convierte todos los tipos necesarios en operaciones vectorizadas.
        """
        self.logger.debug("Iniciando conversión de tipos vectorizada")

        # 1. Conversión de fechas vectorizada
        for col in DATE_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        # 2. Conversión numérica vectorizada
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 3. Conversión booleana vectorizada
        for col in BOOLEAN_COLUMNS:
            if col in df.columns:
                # Crear mapeo invertido para booleanos
                bool_map = {}
                for k, v in BOOLEAN_MAPPING.items():
                    bool_map[k] = v
                    bool_map[str(v).upper()] = v  # También mapear 'TRUE'/'FALSE'
                    bool_map[str(int(v))] = v  # También mapear '1'/'0'

                df[col] = df[col].astype(str).str.upper().map(bool_map)

        self.logger.debug("Conversión de tipos completada")

        return df

    def _validate_critical_values(self, df: pd.DataFrame) -> None:
        """
        Valida solo los valores críticos que pueden causar fallos.

        Enfoque minimalista: solo lo que realmente importa.
        """
        # 1. Verificar IDs únicos críticos
        if Columns.IDEVENTOCASO in df.columns:
            duplicated_ids = df[Columns.IDEVENTOCASO].duplicated()
            if duplicated_ids.sum() > 0:
                duplicate_count = duplicated_ids.sum()
                self.validation_report["warnings"].append(
                    {
                        "type": "duplicate_event_ids",
                        "count": duplicate_count,
                        "severity": "high",
                    }
                )
                self.context.stats.add_warning(
                    ProcessingStage.VALIDATION,
                    f"{duplicate_count} IDs de evento duplicados",
                )

        # 2. Verificar rangos críticos de edad solamente
        age_cols = ["EDAD_ACTUAL", "EDAD_DIAGNOSTICO"]
        for col in age_cols:
            if col in df.columns:
                invalid_ages = (df[col] < VALIDATION_LIMITS["min_age"]) | (
                    df[col] > VALIDATION_LIMITS["max_age"]
                )
                invalid_count = invalid_ages.sum()

                if invalid_count > 0:
                    self.validation_report["warnings"].append(
                        {"type": "invalid_ages", "column": col, "count": invalid_count}
                    )

        # 3. Verificar fechas futuras solo en fechas críticas
        current_date = pd.Timestamp.now()
        critical_date_cols = ["FECHA_APERTURA", "FECHA_NACIMIENTO"]

        for col in critical_date_cols:
            if col in df.columns and df[col].dtype == "datetime64[ns]":
                future_dates = df[col] > current_date
                future_count = future_dates.sum()

                if future_count > 0:
                    self.validation_report["warnings"].append(
                        {"type": "future_dates", "column": col, "count": future_count}
                    )

        self.logger.debug("Validación de valores críticos completada")

    def _update_validation_stats(self, original_count: int, final_count: int) -> None:
        """Actualiza estadísticas de validación."""
        self.validation_report["stats"] = {
            "original_rows": original_count,
            "valid_rows": final_count,
            "rows_removed": original_count - final_count,
            "errors_count": len(self.validation_report["errors"]),
            "warnings_count": len(self.validation_report["warnings"]),
            "validation_time": datetime.utcnow().isoformat(),
        }

        # Actualizar contexto
        self.context.stats.rows_processed += final_count

    def get_validation_report(self) -> Dict:
        """Obtiene el reporte de validación completo."""
        return self.validation_report

    def validate_input(self, df: pd.DataFrame) -> bool:
        """Valida entrada del procesador."""
        return df is not None and not df.empty


class SchemaValidator:
    """
    Validador de esquema independiente para verificación rápida.

    Útil para validar archivos antes del procesamiento completo.
    """

    @staticmethod
    def validate_csv_schema(df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida esquema CSV de forma rápida.

        Returns:
            Diccionario con resultado de validación
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_columns": len(df.columns),
                "total_rows": len(df),
                "required_columns_found": 0,
                "match_percentage": 0.0,
            },
        }

        # Verificar columnas requeridas
        missing_columns = []
        found_columns = 0

        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                found_columns += 1
            else:
                missing_columns.append(col)

        result["stats"]["required_columns_found"] = found_columns
        result["stats"]["match_percentage"] = (
            found_columns / len(REQUIRED_COLUMNS)
        ) * 100

        if missing_columns:
            result["is_valid"] = False
            result["errors"].append(
                {
                    "type": "missing_required_columns",
                    "columns": missing_columns,
                    "count": len(missing_columns),
                }
            )

        # Verificar filas vacías
        if df.empty:
            result["is_valid"] = False
            result["errors"].append(
                {"type": "empty_file", "message": "El archivo no contiene datos"}
            )

        # Warnings por columnas esperadas faltantes (no críticas)
        expected_columns = set(DATE_COLUMNS + NUMERIC_COLUMNS + BOOLEAN_COLUMNS)
        actual_columns = set(df.columns)
        missing_optional = expected_columns - actual_columns

        if missing_optional:
            result["warnings"].append(
                {
                    "type": "missing_optional_columns",
                    "columns": list(missing_optional),
                    "count": len(missing_optional),
                    "message": f"Faltan {len(missing_optional)} columnas opcionales",
                }
            )

        return result

    @staticmethod
    def get_schema_summary(df: pd.DataFrame) -> Dict[str, any]:
        """Obtiene resumen rápido del esquema."""
        return {
            "filename": "CSV_INPUT",
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
            "column_types": {
                "object": len(df.select_dtypes(include=["object"]).columns),
                "numeric": len(df.select_dtypes(include=[np.number]).columns),
                "datetime": len(df.select_dtypes(include=["datetime64"]).columns),
                "boolean": len(df.select_dtypes(include=["bool"]).columns),
            },
            "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns)))
            * 100,
        }
