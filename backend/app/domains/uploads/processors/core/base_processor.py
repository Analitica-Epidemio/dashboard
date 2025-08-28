"""
Clases base y interfaces para el procesamiento de archivos epidemiológicos.

Define los contratos y comportamientos comunes para todos los procesadores.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

import pandas as pd
from sqlmodel import Session

from .constants import ProcessingStage, ProcessingStatus

logger = logging.getLogger(__name__)

# Type variables para generics
T = TypeVar("T")
ProcessingResult = TypeVar("ProcessingResult")


class ProcessingStats:
    """Estadísticas de procesamiento thread-safe."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_stage: Optional[ProcessingStage] = None
        self.rows_processed = 0
        self.entities_created = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def start(self, stage: ProcessingStage) -> None:
        """Inicia tracking de una etapa."""
        self.current_stage = stage
        self.start_time = datetime.utcnow()

    def complete(self) -> None:
        """Completa el tracking."""
        self.end_time = datetime.utcnow()

    def add_error(
        self, stage: ProcessingStage, message: str, details: Optional[Dict] = None
    ) -> None:
        """Agrega un error al tracking."""
        self.errors.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "stage": stage.value,
                "message": message,
                "details": details or {},
            }
        )

    def add_warning(
        self, stage: ProcessingStage, message: str, details: Optional[Dict] = None
    ) -> None:
        """Agrega un warning al tracking."""
        self.warnings.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "stage": stage.value,
                "message": message,
                "details": details or {},
            }
        )

    def duration_seconds(self) -> float:
        """Calcula duración total en segundos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds(),
            "current_stage": self.current_stage.value if self.current_stage else None,
            "rows_processed": self.rows_processed,
            "entities_created": self.entities_created,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ProcessingContext:
    """Contexto compartido para el procesamiento."""

    def __init__(
        self,
        session: Session,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        batch_size: int = 1000,
    ):
        self.session = session
        self.progress_callback = progress_callback
        self.batch_size = batch_size
        self.stats = ProcessingStats()
        self.cache: Dict[str, Any] = {}

    def update_progress(self, percentage: int, message: str) -> None:
        """Actualiza el progreso del procesamiento."""
        if self.progress_callback:
            try:
                self.progress_callback(percentage, message)
            except Exception as e:
                logger.warning(f"Error en callback de progreso: {e}")

        logger.info(f"Progreso: {percentage}% - {message}")


class BaseProcessor(ABC, Generic[T]):
    """
    Clase base abstracta para todos los procesadores.

    Define el contrato común y comportamientos compartidos.
    """

    def __init__(self, context: ProcessingContext):
        """
        Inicializa el procesador base.

        Args:
            context: Contexto de procesamiento compartido
        """
        self.context = context
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def process(self, data: T) -> T:
        """
        Procesa los datos de entrada.

        Args:
            data: Datos a procesar

        Returns:
            Datos procesados

        Raises:
            ProcessingException: Si hay errores en el procesamiento
        """
        pass

    @abstractmethod
    def validate_input(self, data: T) -> bool:
        """
        Valida que los datos de entrada son válidos.

        Args:
            data: Datos a validar

        Returns:
            True si los datos son válidos
        """
        pass

    def get_stage(self) -> ProcessingStage:
        """Obtiene la etapa de procesamiento que maneja este processor."""
        return ProcessingStage.LOADING  # Default, debe ser sobrescrito

    def pre_process(self, data: T) -> T:
        """
        Hook ejecutado antes del procesamiento principal.

        Args:
            data: Datos de entrada

        Returns:
            Datos pre-procesados
        """
        return data

    def post_process(self, data: T) -> T:
        """
        Hook ejecutado después del procesamiento principal.

        Args:
            data: Datos procesados

        Returns:
            Datos post-procesados
        """
        return data

    def handle_error(self, error: Exception, data: Optional[T] = None) -> None:
        """
        Maneja errores de procesamiento.

        Args:
            error: Error ocurrido
            data: Datos que causaron el error (si están disponibles)
        """
        error_msg = f"Error en {self.__class__.__name__}: {str(error)}"
        self.logger.error(error_msg)
        self.context.stats.add_error(
            self.get_stage(), error_msg, {"error_type": type(error).__name__}
        )


class BatchProcessor(BaseProcessor[pd.DataFrame]):
    """
    Procesador base para operaciones en batches sobre DataFrames.

    Proporciona funcionalidad común para procesamiento en lotes.
    """

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesa un DataFrame en batches.

        Args:
            df: DataFrame a procesar

        Returns:
            DataFrame procesado
        """
        if not self.validate_input(df):
            raise ValueError(
                f"Datos de entrada inválidos para {self.__class__.__name__}"
            )

        self.context.stats.start(self.get_stage())

        try:
            # Pre-procesamiento
            df = self.pre_process(df)

            # Procesamiento por batches
            total_rows = len(df)
            processed_dfs = []

            for start_idx in range(0, total_rows, self.context.batch_size):
                end_idx = min(start_idx + self.context.batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx].copy()

                # Procesar batch
                processed_batch = self.process_batch(batch_df)
                processed_dfs.append(processed_batch)

                # Actualizar progreso
                progress = min(int((end_idx / total_rows) * 100), 100)
                stage_name = self.get_stage().value.title()
                self.context.update_progress(
                    progress, f"{stage_name}: {end_idx}/{total_rows} registros"
                )

            # Combinar resultados
            if processed_dfs:
                result_df = pd.concat(processed_dfs, ignore_index=True)
            else:
                result_df = df.copy()

            # Post-procesamiento
            result_df = self.post_process(result_df)

            self.context.stats.rows_processed = len(result_df)

            return result_df

        except Exception as e:
            self.handle_error(e, df)
            raise
        finally:
            self.context.stats.complete()

    @abstractmethod
    def process_batch(self, batch_df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesa un batch individual de datos.

        Args:
            batch_df: Batch de datos a procesar

        Returns:
            Batch procesado
        """
        pass

    def validate_input(self, df: pd.DataFrame) -> bool:
        """Valida que el DataFrame sea válido."""
        if df is None or df.empty:
            return False
        return True
