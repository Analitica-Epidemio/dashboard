"""
Validador simplificado y optimizado para archivos epidemiológicos.

Usa Polars para máximo rendimiento y mínimo uso de memoria.
"""

import logging
from datetime import UTC, datetime
from typing import Any, cast

import polars as pl

from .config import Columns
from .config.constants import (
    BOOLEAN_COLUMNS,
    BOOLEAN_MAPPING,
    DOCUMENTO_MAPPING,
    NULL_VALUES,
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

    def __init__(self) -> None:
        """Inicializa el validador sin dependencias externas."""
        self.reporte_validacion: dict[str, Any] = {
            "errores": [],
            "advertencias": [],
            "estadisticas": {},
        }

    def validar(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Valida y limpia un batch de datos.

        Args:
            df: Polars DataFrame de datos a validar

        Returns:
            Polars DataFrame validado y limpio
        """
        logger.info(f"Validando batch de {df.height} registros")

        conteo_original = df.height

        # 1. Validación estructural crítica
        self._validar_estructura(df)

        # 2. Limpieza de datos vectorizada
        df = self._limpiar_datos_vectorizado(df)

        # 3. Conversión de tipos optimizada
        df = self._convertir_tipos_vectorizado(df)

        # 4. Validaciones críticas solamente
        self._validar_valores_criticos(df)

        # 5. Actualizar estadísticas
        self._actualizar_estadisticas(conteo_original, df.height)

        logger.info(
            f"Validación completada: {df.height}/{conteo_original} registros válidos"
        )

        return df

    def _validar_estructura(self, df: pl.DataFrame) -> None:
        """Valida estructura crítica del DataFrame Polars."""
        # Verificar columnas críticas solamente
        columnas_df = df.columns
        criticas_faltantes = [col for col in REQUIRED_COLUMNS if col not in columnas_df]

        if criticas_faltantes:
            # DEBUGGING EXHAUSTIVO
            logger.error(
                f"📋 Columnas presentes ({len(columnas_df)}): {columnas_df[:20]}..."
            )
            logger.error(
                f"❌ Columnas críticas faltantes ({len(criticas_faltantes)}): {criticas_faltantes}"
            )

            mensaje_error = f"Columnas críticas faltantes: {criticas_faltantes}"
            cast(list[dict[str, Any]], self.reporte_validacion["errores"]).append(
                {
                    "tipo": "columnas_criticas_faltantes",
                    "columnas": criticas_faltantes,
                    "severidad": "critica",
                }
            )

            raise ValueError(mensaje_error)

        # Verificar que no esté vacío
        if df.height == 0:
            mensaje_error = "DataFrame vacío"
            cast(list[dict[str, Any]], self.reporte_validacion["errores"]).append(
                {"tipo": "dataframe_vacio", "severidad": "critica"}
            )

            raise ValueError(mensaje_error)

        logger.debug(
            f"Estructura válida: {len(df.columns)} columnas, {df.height} filas"
        )

    def _limpiar_datos_vectorizado(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Limpieza vectorizada con Polars para máximo rendimiento.

        Polars es 5-54x más rápido que pandas y usa 50-70% menos memoria.
        """
        logger.debug("Iniciando limpieza vectorizada con Polars")

        # 1. Limpiar strings: strip espacios en todas las columnas string
        # Polars hace esto de forma ultra eficiente con operaciones columnar
        exprs_string = []
        for col in df.columns:
            if df[col].dtype == pl.Utf8:  # Columnas de texto
                exprs_string.append(pl.col(col).str.strip_chars().alias(col))
            else:
                exprs_string.append(pl.col(col))

        df = df.select(exprs_string)

        # 2. Reemplazar valores nulos (Polars usa null nativamente, más eficiente que pandas NaN)
        # Convertir strings vacíos y espacios a null
        exprs_nulos = []
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                # Reemplazar valores nulos con null
                exprs_nulos.append(
                    pl.when(pl.col(col).is_in(list(NULL_VALUES)))
                    .then(None)
                    .otherwise(pl.col(col))
                    .alias(col)
                )
            else:
                exprs_nulos.append(pl.col(col))

        df = df.select(exprs_nulos)

        # 3. Normalizar campos específicos a mayúsculas
        exprs_mayusculas = []
        for col in df.columns:
            if col in UPPERCASE_COLUMNS and df[col].dtype == pl.Utf8:
                exprs_mayusculas.append(pl.col(col).str.to_uppercase().alias(col))
            else:
                exprs_mayusculas.append(pl.col(col))

        df = df.select(exprs_mayusculas)

        # 4. Normalizar provincias usando mapeo
        exprs_provincia = []
        for col in df.columns:
            if "PROVINCIA" in col and df[col].dtype == pl.Utf8:
                # Usar replace de Polars (más eficiente)
                exprs_provincia.append(
                    pl.col(col)
                    .replace(PROVINCIA_MAPPING, default=pl.col(col))
                    .alias(col)
                )
            else:
                exprs_provincia.append(pl.col(col))

        df = df.select(exprs_provincia)

        # 5. Normalizar tipos de documento
        if Columns.TIPO_DOC.name in df.columns:
            mapeo_doc = {k: v.name for k, v in DOCUMENTO_MAPPING.items()}
            df = df.with_columns(
                [
                    pl.col(Columns.TIPO_DOC.name).replace(
                        mapeo_doc, default=pl.col(Columns.TIPO_DOC.name)
                    )
                ]
            )

        # 6. Normalizar sexo
        if Columns.SEXO.name in df.columns:
            mapeo_sexo = {k: v.name for k, v in SEXO_MAPPING.items()}
            df = df.with_columns(
                [
                    pl.col(Columns.SEXO.name).replace(
                        mapeo_sexo, default=pl.col(Columns.SEXO.name)
                    )
                ]
            )

        logger.debug("Limpieza vectorizada completada")

        return df

    def _convertir_tipos_vectorizado(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Conversión de tipos con Polars.

        Polars infiere tipos automáticamente de forma más inteligente que pandas.
        Solo necesitamos convertir booleanos que vienen como strings.
        """
        logger.debug("Iniciando conversión de tipos (solo booleanos)")

        # Solo convertir booleanos (único tipo que requiere mapeo)
        exprs_bool = []
        for col in df.columns:
            if col in BOOLEAN_COLUMNS and col in df.columns:
                # Crear mapeo para booleanos
                mapeo_bool = {}
                for k, v in BOOLEAN_MAPPING.items():
                    mapeo_bool[str(k).upper() if isinstance(k, str) else str(k)] = v
                    mapeo_bool[str(v).upper()] = v
                    mapeo_bool[str(int(v))] = v

                # Convertir a string uppercase y mapear
                exprs_bool.append(
                    pl.col(col)
                    .cast(pl.Utf8)
                    .str.to_uppercase()
                    .replace(mapeo_bool)
                    .alias(col)
                )
            else:
                exprs_bool.append(pl.col(col))

        df = df.select(exprs_bool)

        logger.debug("Conversión de booleanos completada")

        return df

    def _validar_valores_criticos(self, df: pl.DataFrame) -> None:
        """
        Valida solo los valores críticos con Polars.

        Polars es mucho más rápido para estas operaciones de filtrado.
        """
        # 1. Verificar IDs únicos críticos
        if Columns.IDEVENTOCASO.name in df.columns:
            conteo_duplicados = df[Columns.IDEVENTOCASO.name].n_unique() < df.height
            if conteo_duplicados:
                duplicados = df.height - df[Columns.IDEVENTOCASO.name].n_unique()
                cast(
                    list[dict[str, Any]], self.reporte_validacion["advertencias"]
                ).append(
                    {
                        "tipo": "ids_evento_duplicados",
                        "conteo": duplicados,
                        "severidad": "alta",
                    }
                )

        # 2. Verificar rangos críticos de edad solamente
        # Las columnas NUMERIC se leen como Utf8 desde el CSV (ver POLARS_SCHEMA_OVERRIDES),
        # por eso se castean a Int64 antes de comparar.
        cols_edad = ["EDAD_ACTUAL", "EDAD_DIAGNOSTICO"]
        for col in cols_edad:
            if col in df.columns:
                col_expr = pl.col(col).cast(pl.Int64, strict=False)
                conteo_invalido = df.filter(
                    (col_expr < VALIDATION_LIMITS["min_age"])
                    | (col_expr > VALIDATION_LIMITS["max_age"])
                ).height

                if conteo_invalido > 0:
                    cast(
                        list[dict[str, Any]], self.reporte_validacion["advertencias"]
                    ).append(
                        {
                            "tipo": "edades_invalidas",
                            "columna": col,
                            "conteo": conteo_invalido,
                        }
                    )

        # 3. Verificar fechas futuras solo en fechas críticas
        from datetime import datetime as dt

        fecha_actual = dt.now()
        cols_fecha_critica = ["FECHA_APERTURA", "FECHA_NACIMIENTO"]

        for col in cols_fecha_critica:
            if col in df.columns and df[col].dtype in [pl.Date, pl.Datetime]:
                conteo_futuro = df.filter(pl.col(col) > fecha_actual).height

                if conteo_futuro > 0:
                    cast(
                        list[dict[str, Any]], self.reporte_validacion["advertencias"]
                    ).append(
                        {
                            "tipo": "fechas_futuras",
                            "columna": col,
                            "conteo": conteo_futuro,
                        }
                    )

        logger.debug("Validación de valores críticos completada")

    def _actualizar_estadisticas(self, conteo_original: int, conteo_final: int) -> None:
        """Actualiza estadísticas de validación."""
        self.reporte_validacion["estadisticas"] = {
            "filas_originales": conteo_original,
            "filas_validas": conteo_final,
            "filas_removidas": conteo_original - conteo_final,
            "conteo_errores": len(self.reporte_validacion["errores"]),
            "conteo_advertencias": len(self.reporte_validacion["advertencias"]),
            "tiempo_validacion": datetime.now(UTC).isoformat(),
        }

    def obtener_reporte_validacion(self) -> dict:
        """Obtiene el reporte de validación completo."""
        return self.reporte_validacion

    def validar_entrada(self, df: pl.DataFrame) -> bool:
        """Valida entrada del procesador."""
        return df is not None and df.height > 0
