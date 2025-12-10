"""
Dispatcher de procesamiento para vigilancia agregada.

Detecta el tipo de archivo y delega al procesador correspondiente.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import polars as pl
from sqlmodel import Session

from app.core.csv_reader import load_file

from .types import (
    CLIP26IntProcessor,
    CLIP26Processor,
    FileTypeProcessor,
    LabP26Processor,
)

logger = logging.getLogger(__name__)


class AgregadaProcessor:
    """
    Dispatcher principal para archivos de vigilancia agregada.

    Detecta automáticamente el tipo de archivo y delega al procesador específico.

    Tipos soportados:
    - CLI_P26: Casos clínicos ambulatorios
    - CLI_P26_INT: Ocupación hospitalaria IRA
    - LAB_P26: Estudios de laboratorio
    """

    def __init__(
        self,
        session: Session,
        callback_progreso: Optional[Callable[[int, str], None]] = None,
    ):
        self.session = session
        self.callback_progreso = callback_progreso

    def procesar_archivo(
        self,
        ruta_archivo: Path,
        nombre_hoja: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Procesa un archivo de vigilancia agregada.

        Args:
            ruta_archivo: Ruta al archivo (xlsx o csv)
            nombre_hoja: Nombre de la hoja para Excel
            file_type: Tipo de archivo (opcional, se detecta automáticamente)

        Returns:
            Diccionario con resultados del procesamiento
        """
        logger.info(f"Procesando archivo agregado: {ruta_archivo}")

        try:
            # 1. Cargar archivo
            self._update_progress(5, "Cargando archivo")
            df = load_file(ruta_archivo, nombre_hoja)

            if len(df) == 0:
                return {
                    "status": "FAILED",
                    "error": "Archivo vacío",
                    "total_rows": 0,
                    "processed_rows": 0,
                }

            # 2. Detectar tipo de archivo
            self._update_progress(10, "Detectando tipo de archivo")
            detected_type = file_type or self._detect_file_type(df)

            if not detected_type:
                return {
                    "status": "FAILED",
                    "error": "No se pudo detectar el tipo de archivo. Columnas encontradas: "
                    + ", ".join(df.columns[:10]),
                    "total_rows": len(df),
                    "processed_rows": 0,
                }

            logger.info(f"Tipo detectado: {detected_type}")

            # 3. Obtener procesador específico
            processor = self._get_processor(detected_type)
            if not processor:
                return {
                    "status": "FAILED",
                    "error": f"Tipo de archivo no soportado: {detected_type}",
                    "total_rows": len(df),
                    "processed_rows": 0,
                }

            # 4. Procesar
            result = processor.process(df)

            return {
                "status": result.status,
                "file_type": detected_type,
                "total_rows": result.total_rows,
                "processed_rows": result.processed_rows,
                "inserted_count": result.inserted_count,
                "updated_count": result.updated_count,
                "errors": result.errors,
            }

        except Exception as e:
            logger.error(f"Error procesando archivo: {e}", exc_info=True)
            return {
                "status": "FAILED",
                "error": str(e),
                "total_rows": 0,
                "processed_rows": 0,
            }

    def _detect_file_type(self, df: pl.DataFrame) -> Optional[str]:
        """
        Detecta el tipo de archivo basándose en las columnas.

        Estrategia:
        - LAB_P26: tiene ID_AGRP_LABO (no ID_AGRP_CLINICA)
        - CLI_P26_INT: tiene ID_AGRP_CLINICA y NOMBREGRPEVENTOAGRP contiene "Vigilancia de internaciones"
        - CLI_P26: tiene ID_AGRP_CLINICA (catch-all para clínicos)
        """
        columns = set(df.columns)

        # LAB_P26: columna distintiva
        if "ID_AGRP_LABO" in columns:
            return "LAB_P26"

        # Archivos clínicos
        if "ID_AGRP_CLINICA" in columns:
            # Verificar si es internación por el contenido de grupos o eventos
            # CLI_P26_INT usa términos como 'internación', 'camas', 'uti', 'arm'
            internacion_keywords = [
                "internacion",
                "internación",
                "camas",
                "uti",
                "arm",
                "respirador",
                "uci",
                "ocupacion",
                "ocupación",
            ]

            # Recolectar textos únicos de columnas relevantes para buscar palabras clave
            textos_a_verificar = set()

            if "NOMBREGRPEVENTOAGRP" in columns:
                textos_a_verificar.update(
                    str(x).lower()
                    for x in df["NOMBREGRPEVENTOAGRP"].unique().to_list()
                    if x
                )

            if "NOMBREEVENTOAGRP" in columns:
                textos_a_verificar.update(
                    str(x).lower()
                    for x in df["NOMBREEVENTOAGRP"].unique().to_list()
                    if x
                )

            # Si encontramos palabras clave de hospitalización, es CLI_P26_INT
            for texto in textos_a_verificar:
                if any(kw in texto for kw in internacion_keywords):
                    return "CLI_P26_INT"

            return "CLI_P26"

        return None

    def _get_processor(self, file_type: str) -> Optional[FileTypeProcessor]:
        """Obtiene el procesador para un tipo de archivo."""
        processors = {
            "CLI_P26": CLIP26Processor,
            "CLI_P26_INT": CLIP26IntProcessor,
            "LAB_P26": LabP26Processor,
        }

        processor_class = processors.get(file_type)
        if processor_class:
            return processor_class(
                session=self.session,
                progress_callback=self.callback_progreso,
            )

        return None

    def _update_progress(self, percentage: int, message: str) -> None:
        """Actualiza progreso si hay callback."""
        if self.callback_progreso:
            try:
                self.callback_progreso(percentage, message)
            except Exception:
                pass


def crear_procesador(
    session: Session,
    callback_progreso: Optional[Callable[[int, str], None]] = None,
) -> AgregadaProcessor:
    """Factory function para crear el procesador."""
    return AgregadaProcessor(session, callback_progreso)
