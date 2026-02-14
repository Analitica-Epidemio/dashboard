"""
Generic CSV/Excel reader using Polars.

Para CSVs epidemiológicos, el caller pasa schema_overrides desde la config
de columnas para que los tipos sean correctos desde la lectura.
"""

import logging
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)


def load_file(
    file_path: Path,
    sheet_name: str | None = None,
    schema_overrides: dict[str, pl.DataType] | None = None,
) -> pl.DataFrame:
    """
    Carga CSV o Excel usando Polars.

    Args:
        file_path: Ruta al archivo
        sheet_name: Hoja de Excel (requerido para .xlsx/.xls)
        schema_overrides: Dict de column_name → pl.DataType para forzar tipos.
            Para CSVs del SNVS, pasar POLARS_SCHEMA_OVERRIDES desde columns.py.
    """
    if file_path.suffix.lower() == ".csv":
        logger.info("⚡ Leyendo CSV con Polars...")
        df_polars = _read_csv(file_path, schema_overrides)

    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        logger.info("⚡ Leyendo Excel con Polars...")

        if not sheet_name:
            raise ValueError(
                "Excel requiere sheet_name - debe especificarse la hoja a procesar"
            )

        df_polars = pl.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="calamine",
        )
    else:
        raise ValueError(f"Formato no soportado: {file_path.suffix}")

    logger.info(
        f"✅ Archivo cargado con Polars: {df_polars.shape[0]:,} filas × {df_polars.shape[1]} columnas"
    )

    return df_polars


def _read_csv(
    file_path: Path,
    schema_overrides: dict[str, pl.DataType] | None = None,
) -> pl.DataFrame:
    """
    Lee CSV probando múltiples encodings.

    Usa schema_overrides para forzar tipos explícitos y try_parse_dates
    para que las columnas de fecha se lean como pl.Date nativamente.
    """
    encodings_to_try = ["utf-8-sig", "utf-8", "latin1"]
    last_error: Exception | None = None

    for encoding in encodings_to_try:
        try:
            logger.info(f"  Intentando encoding: {encoding}")
            df = pl.read_csv(
                file_path,
                encoding=encoding,
                null_values=["", " ", "  ", "\ufeff"],
                try_parse_dates=True,
                infer_schema_length=10000,
                schema_overrides=schema_overrides,
                truncate_ragged_lines=True,
                quote_char='"',
            )
            logger.info(f"  ✅ Encoding {encoding} funcionó")
            return df
        except Exception as e:
            last_error = e
            logger.warning(f"  ⚠️ Encoding {encoding} falló: {str(e)[:100]}")

    raise last_error  # type: ignore[misc]
