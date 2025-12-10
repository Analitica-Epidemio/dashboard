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

from app.core.bulk import BulkOperationResult
from app.core.csv_reader import load_file

from .bulk import MainProcessor as MainBulkProcessor
from .classifier import EventClassifier
from .config import ProcessingContext
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
        callback_progreso: Optional[Callable[[int, str], None]] = None,
    ):
        self.session = session
        self.callback_progreso = callback_progreso
        self.estadisticas: Dict[str, Any] = {
            "filas_procesadas": 0,
            "entidades_creadas": 0,
            "errores": [],
        }

    def procesar_archivo(
        self, ruta_archivo: Path, nombre_hoja: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa archivo CSV/Excel.

        Args:
            ruta_archivo: Ruta del archivo
            nombre_hoja: Hoja de Excel (opcional)

        Returns:
            Resultados del procesamiento
        """
        logger.info(f"Procesando: {ruta_archivo}")

        df_datos: Optional[pl.DataFrame] = None
        try:
            # 1. Cargar archivo (5% del trabajo)
            self._actualizar_progreso(5, "Cargando archivo")
            df_datos = load_file(ruta_archivo, nombre_hoja)

            # 2. Validar estructura (10% del trabajo)
            self._actualizar_progreso(10, "Validando estructura de columnas")
            self._validar_estructura(df_datos)

            # 3. Limpiar datos (15% del trabajo)
            self._actualizar_progreso(15, "Limpiando y normalizando datos")
            df_limpio = self._limpiar_datos(df_datos)

            # 4. Clasificar (20% del trabajo)
            self._actualizar_progreso(20, "Clasificando eventos epidemiológicos")
            df_clasificado = self._clasificar_eventos(df_limpio)

            # 5. Guardar en BD (25-95% del trabajo - se actualiza internamente)
            self._actualizar_progreso(25, "Iniciando guardado en base de datos")
            self._guardar_en_bd(df_clasificado)

            self._actualizar_progreso(100, "Procesamiento completado")

            return {
                "status": "SUCCESS",
                "total_rows": len(df_datos),
                "processed_rows": len(df_clasificado),
                "entities_created": self.estadisticas["entidades_creadas"],
                "ciudadanos_created": self.estadisticas.get("ciudadanos_creados", 0),
                "eventos_created": self.estadisticas.get("eventos_creados", 0),
                "diagnosticos_created": self.estadisticas.get(
                    "diagnosticos_creados", 0
                ),
                "errors": self.estadisticas["errores"],
            }

        except Exception as e:
            mensaje_error = f"Error: {str(e)}"
            logger.error(mensaje_error, exc_info=True)

            return {
                "status": "FAILED",
                "error": mensaje_error,
                "total_rows": len(df_datos) if df_datos is not None else 0,
                "processed_rows": 0,
                "entities_created": 0,
                "errors": [mensaje_error],
            }

    def _validar_estructura(self, df: pl.DataFrame) -> None:
        """Valida estructura mínima usando nuevo sistema de columnas."""
        if len(df) == 0:
            raise ValueError("Archivo vacío")

        # Usar el nuevo sistema de validación
        from .config.columns import get_column_names, validate_dataframe

        # validate_dataframe expects pd.DataFrame, so convert
        df_pandas = df.to_pandas()
        resultado_validacion = validate_dataframe(df_pandas)

        if not resultado_validacion["is_valid"]:
            faltantes_requeridas = resultado_validacion["missing_required"]
            cobertura = resultado_validacion["coverage_percentage"]

            raise ValueError(
                f"Validación fallida:\n"
                f"- Columnas requeridas faltantes: {faltantes_requeridas}\n"
                f"- Cobertura de columnas: {cobertura}%\n"
                f"- Columnas encontradas: {resultado_validacion['matched_columns']} de {len(get_column_names())}"
            )

    def _limpiar_datos(self, df: pl.DataFrame) -> pl.DataFrame:
        """Limpia datos usando validador optimizado."""
        validador = OptimizedDataValidator()
        df_limpio = validador.validar(df)
        return df_limpio

    def _clasificar_eventos(self, df: pl.DataFrame) -> pl.DataFrame:
        """Clasifica usando clasificador simple."""
        clasificador = EventClassifier(self.session)
        df_clasificado = clasificador.clasificar(df)

        return df_clasificado

    def _guardar_en_bd(self, df: pl.DataFrame) -> None:
        """
        Guarda en BD usando bulk processor modular.

        Reporta progreso granular durante las ~18 operaciones de BD (25%-95%).
        """

        # Crear callback wrapper que mapea progreso interno (0-100) a rango 25-95
        def callback_progreso_wrapper(porcentaje_interno: int, mensaje: str):
            # Mapear 0-100 interno → 25-95 externo
            porcentaje_mapeado = 25 + int((porcentaje_interno / 100) * 70)
            self._actualizar_progreso(porcentaje_mapeado, mensaje)

        contexto = ProcessingContext(
            session=self.session,
            progress_callback=callback_progreso_wrapper,
            batch_size=1000,
        )

        procesador = MainBulkProcessor(contexto, logger)
        resultados = procesador.procesar_todo(df)

        # Calcular total de entidades creadas
        total_entidades = sum(res.inserted_count for res in resultados.values())
        self.estadisticas["entidades_creadas"] = total_entidades

        # Calcular contadores específicos por tipo
        self.estadisticas["ciudadanos_creados"] = resultados.get(
            "ciudadanos", BulkOperationResult(0, 0, 0, [], 0.0)
        ).inserted_count
        self.estadisticas["eventos_creados"] = resultados.get(
            "eventos", BulkOperationResult(0, 0, 0, [], 0.0)
        ).inserted_count
        self.estadisticas["diagnosticos_creados"] = resultados.get(
            "diagnosticos_eventos", BulkOperationResult(0, 0, 0, [], 0.0)
        ).inserted_count

        # Agregar errores si los hay
        errores_list = self.estadisticas.get("errores")
        if errores_list is not None and isinstance(errores_list, list):
            for res in resultados.values():
                errores_list.extend(res.errors)

        # NOTA: Los commits ya se hicieron en cada operación individual del MainProcessor
        logger.info(f"Procesamiento completado: {total_entidades} entidades creadas")

    def _actualizar_progreso(self, porcentaje: int, mensaje: str) -> None:
        """Actualiza progreso."""
        if self.callback_progreso:
            try:
                self.callback_progreso(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error en callback: {e}")


def crear_procesador(
    session: Session, callback_progreso: Optional[Callable] = None
) -> SimpleEpidemiologicalProcessor:
    """Crea procesador simple."""
    return SimpleEpidemiologicalProcessor(session, callback_progreso)
