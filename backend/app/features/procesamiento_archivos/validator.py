"""
Validador simplificado y optimizado para archivos epidemiológicos.

Usa Polars para máximo rendimiento y mínimo uso de memoria.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

import polars as pl

from .config import Columns
from .config.constants import (
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
)

logger = logging.getLogger(__name__)


class OptimizedDataValidator:
    """
    Validador de datos optimizado con Polars.

    Características:
    - Validación vectorizada con Polars (5-54x más rápido)
    - Limpieza de datos en una pasada
    - Reportes estructurados de errores
    - 50-70% menos memoria que pandas
    """

    def __init__(self):
        """Inicializa el validador sin dependencias externas."""
        self.validation_report = {"errors": [], "warnings": [], "stats": {}}

    def validate(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Valida y limpia un batch de datos.

        Args:
            df: Polars DataFrame de datos a validar

        Returns:
            Polars DataFrame validado y limpio
        """
        logger.info(f"Validando batch de {df.height} registros")

        original_count = df.height

        # 1. Validación estructural crítica
        self._validate_structure(df)

        # 2. Limpieza de datos vectorizada
        df = self._clean_data_vectorized(df)

        # 3. Conversión de tipos optimizada
        df = self._convert_types_vectorized(df)

        # 4. Validaciones críticas solamente
        self._validate_critical_values(df)

        # 5. Actualizar estadísticas
        self._update_validation_stats(original_count, df.height)

        logger.info(
            f"Validación completada: {df.height}/{original_count} registros válidos"
        )

        return df

    def _validate_structure(self, df: pl.DataFrame) -> None:
        """Valida estructura crítica del DataFrame Polars."""
        # Verificar columnas críticas solamente
        df_columns = df.columns
        missing_critical = [col for col in REQUIRED_COLUMNS if col not in df_columns]

        if missing_critical:
            # DEBUGGING EXHAUSTIVO
            logger.error(f"📋 Columnas presentes ({len(df_columns)}): {df_columns[:20]}...")
            logger.error(f"❌ Columnas críticas faltantes ({len(missing_critical)}): {missing_critical}")

            error_msg = f"Columnas críticas faltantes: {missing_critical}"
            self.validation_report["errors"].append(
                {
                    "type": "missing_critical_columns",
                    "columns": missing_critical,
                    "severity": "critical",
                }
            )

            raise ValueError(error_msg)

        # Verificar que no esté vacío
        if df.height == 0:
            error_msg = "DataFrame vacío"
            self.validation_report["errors"].append(
                {"type": "empty_dataframe", "severity": "critical"}
            )

            raise ValueError(error_msg)

        logger.debug(f"Estructura válida: {len(df.columns)} columnas, {df.height} filas")

    def _clean_data_vectorized(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Limpieza vectorizada con Polars para máximo rendimiento.

        Polars es 5-54x más rápido que pandas y usa 50-70% menos memoria.
        """
        logger.debug("Iniciando limpieza vectorizada con Polars")

        # 1. Limpiar strings: strip espacios en todas las columnas string
        # Polars hace esto de forma ultra eficiente con operaciones columnar
        string_exprs = []
        for col in df.columns:
            if df[col].dtype == pl.Utf8:  # Columnas de texto
                string_exprs.append(pl.col(col).str.strip_chars().alias(col))
            else:
                string_exprs.append(pl.col(col))

        df = df.select(string_exprs)

        # 2. Reemplazar valores nulos (Polars usa null nativamente, más eficiente que pandas NaN)
        # Convertir strings vacíos y espacios a null
        null_exprs = []
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                # Reemplazar valores nulos con null
                null_exprs.append(
                    pl.when(pl.col(col).is_in(list(NULL_VALUES)))
                    .then(None)
                    .otherwise(pl.col(col))
                    .alias(col)
                )
            else:
                null_exprs.append(pl.col(col))

        df = df.select(null_exprs)

        # 3. Normalizar campos específicos a mayúsculas
        uppercase_exprs = []
        for col in df.columns:
            if col in UPPERCASE_COLUMNS and df[col].dtype == pl.Utf8:
                uppercase_exprs.append(pl.col(col).str.to_uppercase().alias(col))
            else:
                uppercase_exprs.append(pl.col(col))

        df = df.select(uppercase_exprs)

        # 4. Normalizar provincias usando mapeo
        provincia_exprs = []
        for col in df.columns:
            if "PROVINCIA" in col and df[col].dtype == pl.Utf8:
                # Usar replace de Polars (más eficiente)
                provincia_exprs.append(
                    pl.col(col).replace(PROVINCIA_MAPPING, default=pl.col(col)).alias(col)
                )
            else:
                provincia_exprs.append(pl.col(col))

        df = df.select(provincia_exprs)

        # 5. Normalizar tipos de documento
        if Columns.TIPO_DOC.name in df.columns:
            doc_mapping = {k: v.name for k, v in DOCUMENTO_MAPPING.items()}
            df = df.with_columns([
                pl.col(Columns.TIPO_DOC.name).replace(doc_mapping, default=pl.col(Columns.TIPO_DOC.name))
            ])

        # 6. Normalizar sexo
        if Columns.SEXO.name in df.columns:
            sexo_mapping = {k: v.name for k, v in SEXO_MAPPING.items()}
            df = df.with_columns([
                pl.col(Columns.SEXO.name).replace(sexo_mapping, default=pl.col(Columns.SEXO.name))
            ])

        logger.debug("Limpieza vectorizada completada")

        return df

    def _convert_types_vectorized(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Conversión de tipos con Polars.

        Polars infiere tipos automáticamente de forma más inteligente que pandas.
        Solo necesitamos convertir booleanos que vienen como strings.
        """
        logger.debug("Iniciando conversión de tipos (solo booleanos)")

        # Solo convertir booleanos (único tipo que requiere mapeo)
        bool_exprs = []
        for col in df.columns:
            if col in BOOLEAN_COLUMNS and col in df.columns:
                # Crear mapeo para booleanos
                bool_map = {}
                for k, v in BOOLEAN_MAPPING.items():
                    bool_map[str(k).upper() if isinstance(k, str) else str(k)] = v
                    bool_map[str(v).upper()] = v
                    bool_map[str(int(v))] = v

                # Convertir a string uppercase y mapear
                bool_exprs.append(
                    pl.col(col).cast(pl.Utf8).str.to_uppercase().replace(bool_map).alias(col)
                )
            else:
                bool_exprs.append(pl.col(col))

        df = df.select(bool_exprs)

        logger.debug("Conversión de booleanos completada")

        return df

    def _validate_critical_values(self, df: pl.DataFrame) -> None:
        """
        Valida solo los valores críticos con Polars.

        Polars es mucho más rápido para estas operaciones de filtrado.
        """
        # 1. Verificar IDs únicos críticos
        if Columns.IDEVENTOCASO.name in df.columns:
            duplicate_count = df[Columns.IDEVENTOCASO.name].n_unique() < df.height
            if duplicate_count:
                duplicates = df.height - df[Columns.IDEVENTOCASO.name].n_unique()
                self.validation_report["warnings"].append(
                    {
                        "type": "duplicate_event_ids",
                        "count": duplicates,
                        "severity": "high",
                    }
                )

        # 2. Verificar rangos críticos de edad solamente
        age_cols = ["EDAD_ACTUAL", "EDAD_DIAGNOSTICO"]
        for col in age_cols:
            if col in df.columns:
                invalid_count = df.filter(
                    (pl.col(col) < VALIDATION_LIMITS["min_age"]) |
                    (pl.col(col) > VALIDATION_LIMITS["max_age"])
                ).height

                if invalid_count > 0:
                    self.validation_report["warnings"].append(
                        {"type": "invalid_ages", "column": col, "count": invalid_count}
                    )

        # 3. Verificar fechas futuras solo en fechas críticas
        from datetime import datetime as dt
        current_date = dt.now()
        critical_date_cols = ["FECHA_APERTURA", "FECHA_NACIMIENTO"]

        for col in critical_date_cols:
            if col in df.columns and df[col].dtype in [pl.Date, pl.Datetime]:
                future_count = df.filter(pl.col(col) > current_date).height

                if future_count > 0:
                    self.validation_report["warnings"].append(
                        {"type": "future_dates", "column": col, "count": future_count}
                    )

        logger.debug("Validación de valores críticos completada")

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

    def get_validation_report(self) -> Dict:
        """Obtiene el reporte de validación completo."""
        return self.validation_report

    def validate_input(self, df: pl.DataFrame) -> bool:
        """Valida entrada del procesador."""
        return df is not None and df.height > 0
