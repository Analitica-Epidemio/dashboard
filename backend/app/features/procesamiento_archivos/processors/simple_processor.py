"""
Procesador simple y directo para archivos epidemiológicos.

OBJETIVO: Validar, clasificar y guardar en BD de forma eficiente.
Sin abstracciones innecesarias.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd
from sqlmodel import Session

from .bulk_processors import MainBulkProcessor
from .classification.classifier import EventClassifier
from .core.base_processor import ProcessingContext
from .core.columns import Columns
from .validation.validator import OptimizedDataValidator

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
            # 1. Cargar archivo
            self._update_progress(10, "Cargando archivo")
            df = self._load_file(file_path, sheet_name)

            # 2. Validar estructura
            self._update_progress(20, "Validando estructura")
            self._validate_structure(df)

            # 3. Limpiar datos (usando componente nuevo)
            self._update_progress(30, "Limpiando datos")
            df_clean = self._clean_data(df)

            # 4. Clasificar (usando componente nuevo)
            self._update_progress(50, "Clasificando eventos")
            df_classified = self._classify_events(df_clean)

            # 5. Guardar en BD (usando componente nuevo)
            self._update_progress(70, "Guardando en BD")
            self._save_to_database(df_classified)

            self._update_progress(100, "Completado")

            return {
                "status": "SUCCESS",
                "total_rows": len(df),
                "processed_rows": len(df_classified),
                "entities_created": self.stats["entities_created"],
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

    def _load_file(self, file_path: Path, sheet_name: Optional[str]) -> pd.DataFrame:
        """
        Carga CSV o Excel con inferencia de tipos automática.

        MEJOR PRÁCTICA para datos reales (con valores sucios):
        - Dejar que pandas infiera tipos (robusto ante strings vacíos, valores nulos)
        - Solo forzar parse_dates con dayfirst=True para formato argentino
        - Pandas inferirá int64/float64 automáticamente donde sea posible
        """
        # Columnas de fecha del CSV real (formato argentino DD/MM/YYYY)
        date_columns = [
            'FECHA_NACIMIENTO', 'FECHA_APERTURA', 'FECHA_CONSULTA',
            'FECHA_INTERNACION', 'FECHA_CUI_INTENSIVOS', 'FECHA_ALTA_MEDICA',
            'FECHA_FALLECIMIENTO', 'FECHA_ESTUDIO', 'FECHA_RECEPCION',
            'FECHA_INICIO_VIAJE', 'FECHA_FIN_VIAJE', 'FECHA_APLICACION',
            'FECHA_INICIO_SINTOMA', 'FECHA_INICIO_TRAT', 'FECHA_FIN_TRAT',
            'FECHA_AMBITO_OCURRENCIA', 'FECHA_ANTECEDENTE_EPI',
            'FECHA_INVESTIGACION', 'FECHA_DIAG_REFERIDO', 'FECHA_PAPEL'
        ]

        df = None
        if file_path.suffix.lower() == ".csv":
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    # MEJOR PRÁCTICA: Inferencia automática + parse_dates con dayfirst=True
                    # dayfirst=True es crítico para formato argentino (DD/MM/YYYY)
                    # low_memory=False permite inferir tipos consistentes en todo el CSV
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        parse_dates=date_columns,
                        dayfirst=True,
                        low_memory=False,  # Infiere tipos en todo el archivo, no por chunks
                    )
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                raise ValueError(f"No se pudo leer CSV: {file_path}")
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            # Para Excel, parsear fechas con inferencia automática
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name or 0,
                parse_dates=date_columns
            )
        else:
            raise ValueError(f"Formato no soportado: {file_path.suffix}")

        return df

    def _validate_structure(self, df: pd.DataFrame) -> None:
        """Valida estructura mínima usando nuevo sistema de columnas."""
        if df.empty:
            raise ValueError("Archivo vacío")

        # Usar el nuevo sistema de validación
        validation_result = Columns.validate_dataframe(df)

        if not validation_result["is_valid"]:
            missing_required = validation_result["missing_required"]
            coverage = validation_result["coverage_percentage"]

            raise ValueError(
                f"Validación fallida:\n"
                f"- Columnas requeridas faltantes: {missing_required}\n"
                f"- Cobertura de columnas: {coverage}%\n"
                f"- Columnas encontradas: {validation_result['matched_columns']} de {len(Columns.all_columns())}"
            )

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia datos usando validador optimizado."""
        validator = OptimizedDataValidator()
        df_clean = validator.validate(df)
        return df_clean

    def _classify_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clasifica usando clasificador simple."""
        classifier = EventClassifier(self.session)
        df_classified = classifier.classify(df)

        return df_classified

    def _save_to_database(self, df: pd.DataFrame) -> None:
        """Guarda en BD usando bulk processor modular."""
        context = ProcessingContext(
            session=self.session,
            progress_callback=self.progress_callback,
            batch_size=1000,
        )

        processor = MainBulkProcessor(context, logger)
        results = processor.process_all(df)

        # Calcular total de entidades creadas
        total_entities = sum(result.inserted_count for result in results.values())
        self.stats["entities_created"] = total_entities

        # Agregar errores si los hay
        for result in results.values():
            self.stats["errors"].extend(result.errors)

        # Commit de la sesión para persistir cambios
        self.session.commit()
        logger.info(f"Commit exitoso: {total_entities} entidades creadas")

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
