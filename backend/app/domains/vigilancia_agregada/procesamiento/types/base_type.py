"""
Base interface para procesadores de tipos de archivo.

Cada tipo de archivo (CLI_P26, CLI_P26_INT, LAB_P26) implementa esta interfaz.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

import polars as pl
from sqlmodel import Session

from ..columns.base import ColumnRegistry


@dataclass
class ProcessingResult:
    """Resultado de procesamiento de un archivo."""

    status: str  # SUCCESS, FAILED, PARTIAL
    total_rows: int
    processed_rows: int
    inserted_count: int
    updated_count: int
    errors: list[str]

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"


class FileTypeProcessor(ABC):
    """
    Interface base para procesadores de tipos de archivo.

    Cada tipo de archivo implementa esta interfaz con su lógica específica
    de columnas, validación, transformación y guardado.
    """

    def __init__(
        self,
        session: Session,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.session = session
        self.progress_callback = progress_callback

    @property
    @abstractmethod
    def file_type(self) -> str:
        """Código del tipo de archivo (ej: CLI_P26)."""
        pass

    @property
    @abstractmethod
    def column_registry(self) -> ColumnRegistry:
        """Registro de columnas para este tipo."""
        pass

    @abstractmethod
    def transform(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Transforma el DataFrame a formato interno.

        Incluye:
        - Renombrar columnas
        - Convertir tipos
        - Normalizar valores
        """
        pass

    @abstractmethod
    def save_to_db(self, df: pl.DataFrame) -> ProcessingResult:
        """
        Guarda los datos en la base de datos.

        Incluye:
        - Upsert de NotificacionSemanal
        - Lookup/upsert de catálogos
        - Bulk insert de conteos
        """
        pass

    def validate(self, df: pl.DataFrame) -> tuple[bool, list[str]]:
        """Valida columnas requeridas."""
        return self.column_registry.validate(df)

    def process(self, df: pl.DataFrame) -> ProcessingResult:
        """
        Pipeline completo de procesamiento.

        1. Validar columnas
        2. Transformar datos
        3. Guardar en BD
        """
        # 1. Validar
        self._update_progress(10, "Validando columnas")
        is_valid, missing = self.validate(df)
        if not is_valid:
            return ProcessingResult(
                status="FAILED",
                total_rows=len(df),
                processed_rows=0,
                inserted_count=0,
                updated_count=0,
                errors=[f"Columnas faltantes: {missing}"],
            )

        # 2. Transformar
        self._update_progress(20, "Transformando datos")
        df_transformed = self.transform(df)

        # 3. Guardar
        self._update_progress(30, "Guardando en base de datos")
        result = self.save_to_db(df_transformed)

        self._update_progress(100, "Completado")
        return result

    def _update_progress(self, percentage: int, message: str) -> None:
        """Actualiza progreso si hay callback."""
        if self.progress_callback:
            try:
                self.progress_callback(percentage, message)
            except Exception:
                pass  # Ignorar errores de callback
