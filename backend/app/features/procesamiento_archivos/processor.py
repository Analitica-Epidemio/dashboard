"""
Procesador simple y directo para archivos epidemiológicos.

OBJETIVO: Validar, clasificar y guardar en BD de forma eficiente.
Sin abstracciones innecesarias.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import polars as pl
from sqlmodel import Session

from .bulk import MainProcessor as MainBulkProcessor
from .bulk.shared import BulkOperationResult
from .classifier import EventClassifier
from .config import ProcessingContext, Columns
from .validator import OptimizedDataValidator

logger = logging.getLogger(__name__)


class SimpleEpidemiologicalProcessor:
    """
    Procesador directo para archivos epidemiológicos.

    Sin complejidades - directo al grano:
    1. Validar datos
    2. Clasificar eventos
    3. Guardar en BD con bulk operations
    """

    def __init__(
        self,
        session: Session,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.session = session
        self.progress_callback = progress_callback
        self.stats = {"rows_processed": 0, "entities_created": 0, "errors": []}

    def process_file(
        self, file_path: Path, sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa archivo CSV/Excel.

        Args:
            file_path: Ruta del archivo
            sheet_name: Hoja de Excel (opcional)

        Returns:
            Resultados del procesamiento
        """
        logger.info(f"Procesando: {file_path}")

        try:
            # 1. Cargar archivo (5% del trabajo)
            self._update_progress(5, "Cargando archivo")
            df = self._load_file(file_path, sheet_name)

            # 2. Validar estructura (10% del trabajo)
            self._update_progress(10, "Validando estructura de columnas")
            self._validate_structure(df)

            # 3. Limpiar datos (15% del trabajo)
            self._update_progress(15, "Limpiando y normalizando datos")
            df_clean = self._clean_data(df)

            # 4. Clasificar (20% del trabajo)
            self._update_progress(20, "Clasificando eventos epidemiológicos")
            df_classified = self._classify_events(df_clean)

            # 5. Guardar en BD (25-95% del trabajo - se actualiza internamente)
            self._update_progress(25, "Iniciando guardado en base de datos")
            self._save_to_database(df_classified)

            self._update_progress(100, "Procesamiento completado")

            return {
                "status": "SUCCESS",
                "total_rows": len(df),
                "processed_rows": len(df_classified),
                "entities_created": self.stats["entities_created"],
                "ciudadanos_created": self.stats.get("ciudadanos_created", 0),
                "eventos_created": self.stats.get("eventos_created", 0),
                "diagnosticos_created": self.stats.get("diagnosticos_created", 0),
                "errors": self.stats["errors"],
            }

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return {
                "status": "FAILED",
                "error": error_msg,
                "total_rows": len(df) if "df" in locals() else 0,
                "processed_rows": 0,
                "entities_created": 0,
                "errors": [error_msg],
            }

    def _load_file(self, file_path: Path, sheet_name: Optional[str]) -> pl.DataFrame:
        """
        Carga CSV o Excel usando Polars (5-54x más rápido, mucho menos memoria).

        ESTRATEGIA ESTRICTA PERO INTELIGENTE:
        1. Lee TODAS las columnas que encuentra (sin truncar ni ignorar)
        2. Valida que tengamos las columnas requeridas
        3. Log de columnas extra (para detección de problemas)
        4. Selecciona solo las columnas que necesitamos

        Ventajas Polars:
        - 5-54x más rápido que pandas
        - Usa 50-70% menos memoria
        - Multithreading automático
        - Mejor manejo de nulls
        """
        from .config.columns import DATE_COLUMNS

        all_date_columns = list(DATE_COLUMNS)

        # Leer archivo - UNA SOLA MANERA
        if file_path.suffix.lower() == ".csv":
            logger.info(f"⚡ Leyendo CSV con Polars...")
            df_polars = pl.read_csv(
                file_path,
                encoding="latin1",  # SNVS siempre usa Latin-1 (ISO-8859-1)
                null_values=['', ' ', '  '],
                try_parse_dates=True,
                infer_schema_length=10000,
                truncate_ragged_lines=True,  # CSV del SNVS tienen filas irregulares
            )
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            logger.info(f"⚡ Leyendo Excel con Polars...")

            # Polars requiere nombre de hoja, no índice
            if not sheet_name:
                raise ValueError("Excel requiere sheet_name - debe especificarse la hoja a procesar")

            df_polars = pl.read_excel(
                file_path,
                sheet_name=sheet_name,  # Nombre de la hoja (string)
                engine="calamine",  # Motor Rust ultra rápido
            )
        else:
            raise ValueError(f"Formato no soportado: {file_path.suffix}")

        # Log columnas encontradas
        logger.info(f"✅ Archivo cargado con Polars: {df_polars.shape[0]:,} filas × {df_polars.shape[1]} columnas")

        # VALIDACIÓN ESTRICTA: Comparar columnas CSV vs nuestro mapeo
        from .config.columns import get_column_names

        columnas_csv = set(df_polars.columns)
        columnas_mapeadas = set(get_column_names())

        # Columnas en CSV que NO están en nuestro mapeo (CRÍTICO - pueden ser importantes!)
        columnas_extra = columnas_csv - columnas_mapeadas
        if columnas_extra:
            logger.warning(f"⚠️  COLUMNAS EXTRA en CSV (NO mapeadas): {len(columnas_extra)}")
            logger.warning(f"    Columnas: {sorted(columnas_extra)}")
            logger.warning(f"    ⚠️  REVISAR: ¿Son columnas importantes que deberíamos mapear?")

        # Columnas mapeadas que NO están en el CSV (esperado - depende del tipo de evento)
        columnas_faltantes = columnas_mapeadas - columnas_csv
        if columnas_faltantes:
            logger.info(f"ℹ️  Columnas mapeadas pero ausentes en CSV: {len(columnas_faltantes)}")
            # Solo log a nivel debug para no saturar
            logger.debug(f"    Columnas faltantes: {sorted(columnas_faltantes)}")

        # Cobertura
        columnas_matcheadas = columnas_csv & columnas_mapeadas
        cobertura = (len(columnas_matcheadas) / len(columnas_csv)) * 100 if columnas_csv else 0
        logger.info(f"📊 Cobertura de mapeo: {len(columnas_matcheadas)}/{len(columnas_csv)} columnas ({cobertura:.1f}%)")

        # POLARS PURO - no convertir a pandas
        # Todo el pipeline usa Polars para máximo rendimiento y mínima memoria
        return df_polars

    def _validate_structure(self, df: pl.DataFrame) -> None:
        """Valida estructura mínima usando nuevo sistema de columnas."""
        if len(df) == 0:
            raise ValueError("Archivo vacío")

        # Usar el nuevo sistema de validación
        from .config.columns import validate_dataframe, get_column_names

        validation_result = validate_dataframe(df)

        if not validation_result["is_valid"]:
            missing_required = validation_result["missing_required"]
            coverage = validation_result["coverage_percentage"]

            raise ValueError(
                f"Validación fallida:\n"
                f"- Columnas requeridas faltantes: {missing_required}\n"
                f"- Cobertura de columnas: {coverage}%\n"
                f"- Columnas encontradas: {validation_result['matched_columns']} de {len(get_column_names())}"
            )

    def _clean_data(self, df: pl.DataFrame) -> pl.DataFrame:
        """Limpia datos usando validador optimizado."""
        validator = OptimizedDataValidator()
        df_clean = validator.validate(df)
        return df_clean

    def _classify_events(self, df: pl.DataFrame) -> pl.DataFrame:
        """Clasifica usando clasificador simple."""
        classifier = EventClassifier(self.session)
        df_classified = classifier.classify(df)

        return df_classified

    def _save_to_database(self, df: pl.DataFrame) -> None:
        """
        Guarda en BD usando bulk processor modular.

        Reporta progreso granular durante las ~18 operaciones de BD (25%-95%).
        """
        # Crear callback wrapper que mapea progreso interno (0-100) a rango 25-95
        def wrapped_progress_callback(internal_percentage: int, message: str):
            # Mapear 0-100 interno → 25-95 externo
            mapped_percentage = 25 + int((internal_percentage / 100) * 70)
            self._update_progress(mapped_percentage, message)

        context = ProcessingContext(
            session=self.session,
            progress_callback=wrapped_progress_callback,
            batch_size=1000,
        )

        processor = MainBulkProcessor(context, logger)
        results = processor.process_all(df)

        # Calcular total de entidades creadas
        total_entities = sum(result.inserted_count for result in results.values())
        self.stats["entities_created"] = total_entities

        # Calcular contadores específicos por tipo
        self.stats["ciudadanos_created"] = results.get("ciudadanos", BulkOperationResult(0, 0, 0, [], 0.0)).inserted_count
        self.stats["eventos_created"] = results.get("eventos", BulkOperationResult(0, 0, 0, [], 0.0)).inserted_count
        self.stats["diagnosticos_created"] = results.get("diagnosticos_eventos", BulkOperationResult(0, 0, 0, [], 0.0)).inserted_count

        # Agregar errores si los hay
        for result in results.values():
            self.stats["errors"].extend(result.errors)

        # NOTA: Los commits ya se hicieron en cada operación individual del MainProcessor
        logger.info(f"Procesamiento completado: {total_entities} entidades creadas")

    def _update_progress(self, percentage: int, message: str) -> None:
        """Actualiza progreso."""
        if self.progress_callback:
            try:
                self.progress_callback(percentage, message)
            except Exception as e:
                logger.warning(f"Error en callback: {e}")


def create_processor(
    session: Session, progress_callback: Optional[Callable] = None
) -> SimpleEpidemiologicalProcessor:
    """Crea procesador simple."""
    return SimpleEpidemiologicalProcessor(session, progress_callback)
