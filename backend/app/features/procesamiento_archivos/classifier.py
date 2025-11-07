"""
Clasificador simple de eventos epidemiológicos.

Solo usa la estrategia de BD - sin complexity patterns innecesarios.
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlmodel import Session

from app.core.utils.codigo_generator import CodigoGenerator
from app.domains.eventos_epidemiologicos.clasificacion.models import TipoClasificacion

from .config import Columns
from .config.constants import METADATA_EXTRACTION_TYPES

logger = logging.getLogger(__name__)


class EventClassifier:
    """
    Clasificador simple que usa estrategias de BD.

    Sin strategy pattern - solo la implementación que necesitas.
    """

    def __init__(self, session: Session):
        self.session = session
        self._tipo_eno_cache: Dict[str, Any] = {}

        # Importar servicio de clasificación
        try:
            from app.domains.eventos_epidemiologicos.clasificacion.sync_services import (
                SyncEventClassificationService,
            )

            self.classification_service = SyncEventClassificationService(session)
        except ImportError:
            logger.warning("SyncEventClassificationService no disponible")
            self.classification_service = None

        # Importar extractor de metadata
        try:
            from app.domains.eventos_epidemiologicos.clasificacion.detectors import TipoSujetoDetector

            self.tipo_sujeto_detector = TipoSujetoDetector()
        except ImportError:
            logger.warning("TipoSujetoDetector no disponible")
            self.tipo_sujeto_detector = None

    def classify(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clasifica eventos usando estrategias de BD y GRUPO_EVENTO del CSV.

        Args:
            df: DataFrame con eventos

        Returns:
            DataFrame con clasificación aplicada
        """
        logger.info(f"Clasificando {len(df)} eventos")

        # Validar columnas requeridas
        if Columns.EVENTO.name not in df.columns:
            logger.error(f"Columna {Columns.EVENTO.name} no encontrada")
            return self._add_default_columns(df)

        if Columns.GRUPO_EVENTO.name not in df.columns:
            logger.error(f"Columna {Columns.GRUPO_EVENTO.name} no encontrada")
            return self._add_default_columns(df)

        # Validar que todos los registros tienen GRUPO_EVENTO
        missing_grupo_evento = df[Columns.GRUPO_EVENTO.name].isnull() | (
            df[Columns.GRUPO_EVENTO.name] == ""
        )
        if missing_grupo_evento.any():
            logger.error(
                f"Se encontraron {missing_grupo_evento.sum()} registros sin GRUPO_EVENTO"
            )
            # OPTIMIZACIÓN: Marcar in-place en lugar de copiar todo el DataFrame
            # Esto ahorra ~200-300 MB de RAM
            df.loc[missing_grupo_evento, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
            # Continuar con los registros válidos
            df = df[~missing_grupo_evento].copy()  # Solo copiamos el subset filtrado

        if df.empty:
            logger.error("No hay registros válidos para clasificar")
            return self._add_default_columns(df)

        # OPTIMIZACIÓN: Agregar columnas in-place sin copiar
        # Esto ahorra otra copia del DataFrame completo (~200-300 MB)
        df["clasificacion_estrategia"] = None
        df["es_positivo"] = False
        df["tipo_eno_detectado"] = None
        df["metadata_extraida"] = None
        df["confidence_score"] = 0.0
        df["id_estrategia_aplicada"] = None
        df["trazabilidad_clasificacion"] = None

        # Procesar por tipo de evento
        grouped = df.groupby(Columns.EVENTO.name)

        for evento_name, group_df in grouped:
            try:
                self._classify_event_group(df, group_df, str(evento_name))
            except Exception as e:
                logger.error(f"Error clasificando {evento_name}: {e}")
                df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION

        logger.info("Clasificación completada")

        # OPTIMIZACIÓN: No hacer copia innecesaria del DataFrame
        # El DataFrame se pasa directamente al bulk processor que usa .to_dict('records')
        # y no itera por filas, por lo que no hay beneficio real de "desfragmentar"
        # Ahorro: ~350 MB RAM en archivos de 14K registros

        return df

    def _classify_event_group(
        self, full_df: pd.DataFrame, group_df: pd.DataFrame, evento_name: str
    ):
        """Clasifica un grupo de eventos del mismo tipo."""
        # 1. Obtener tipo ENO
        tipo_eno = self._get_tipo_eno(evento_name)

        if not tipo_eno:
            # El evento no está en nuestro seed - marcarlo como requiere revisión
            logger.warning(f"Evento '{evento_name}' no está en el seed - marcando como REQUIERE_REVISION")
            full_df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
            return

        full_df.loc[group_df.index, "tipo_eno_detectado"] = tipo_eno["nombre"]

        # 2. Aplicar clasificación de BD
        if self.classification_service:
            try:
                classified_group = self.classification_service.classify_events(
                    group_df.copy(), tipo_eno["id"]
                )

                full_df.loc[group_df.index, "clasificacion_estrategia"] = (
                    classified_group["clasificacion"]
                )
                full_df.loc[group_df.index, "es_positivo"] = classified_group[
                    "es_positivo"
                ]

                # Copiar información de trazabilidad
                if "id_estrategia_aplicada" in classified_group.columns:
                    full_df.loc[group_df.index, "id_estrategia_aplicada"] = (
                        classified_group["id_estrategia_aplicada"]
                    )

                if "trazabilidad" in classified_group.columns:
                    full_df.loc[group_df.index, "trazabilidad_clasificacion"] = (
                        classified_group["trazabilidad"]
                    )

            except Exception as e:
                logger.error(f"Error en clasificación de BD: {e}")
                full_df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
                full_df.loc[group_df.index, "trazabilidad_clasificacion"] = {
                    "razon": "error",
                    "mensaje": f"Error al aplicar clasificación: {str(e)}"
                }
        else:
            # Usar GRUPO_EVENTO del CSV como clasificación
            logger.warning(
                "SyncEventClassificationService no disponible, usando GRUPO_EVENTO del CSV"
            )
            for idx in group_df.index:
                grupo_evento = group_df.loc[idx, Columns.GRUPO_EVENTO.name]
                if pd.notna(grupo_evento) and grupo_evento.strip():
                    full_df.loc[idx, "clasificacion_estrategia"] = (
                        str(grupo_evento).strip().upper()
                    )
                else:
                    full_df.loc[idx, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION

        # 3. Extraer metadata si es necesario
        if tipo_eno["nombre"] in METADATA_EXTRACTION_TYPES:
            self._extract_metadata(full_df, group_df, tipo_eno["nombre"])

    def _get_tipo_eno(self, evento_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene tipo ENO desde cache o BD usando código kebab-case."""
        if not evento_name or not evento_name.strip():
            return None

        # Convertir nombre del evento a código kebab-case estable
        evento_codigo = CodigoGenerator.generar_codigo_kebab(evento_name)

        # Buscar en cache (usando código como clave)
        if evento_codigo in self._tipo_eno_cache:
            return self._tipo_eno_cache[evento_codigo]

        # Buscar en BD por código (más robusto que buscar por nombre)
        try:
            from app.domains.eventos_epidemiologicos.eventos.models import TipoEno

            result = self.session.execute(
                select(TipoEno).where(TipoEno.codigo == evento_codigo)
            )
            tipo_eno = result.scalar_one_or_none()

            if tipo_eno:
                tipo_eno_dict = {
                    "id": tipo_eno.id,
                    "nombre": tipo_eno.nombre,
                    "codigo": tipo_eno.codigo,
                }

                self._tipo_eno_cache[evento_codigo] = tipo_eno_dict
                return tipo_eno_dict

        except Exception as e:
            logger.debug(f"Tipo ENO con código '{evento_codigo}' (evento: '{evento_name}') no encontrado en BD: {e}")

        # No encontrado - evento no está en el seed
        self._tipo_eno_cache[evento_codigo] = None
        return None

    def _extract_metadata(
        self, full_df: pd.DataFrame, group_df: pd.DataFrame, tipo_eno_name: str
    ):
        """Extrae metadata para tipos específicos."""
        if not self.tipo_sujeto_detector:
            return

        for idx in group_df.index:
            try:
                row = group_df.loc[idx]

                # Detectar tipo de sujeto
                tipo_sujeto, confidence, metadata = self.tipo_sujeto_detector.detectar(
                    row.to_dict()
                )

                full_df.at[idx, "metadata_extraida"] = metadata if metadata else None
                full_df.at[idx, "confidence_score"] = confidence

            except Exception as e:
                logger.warning(f"Error extrayendo metadata para fila {idx}: {e}")
                full_df.at[idx, "metadata_extraida"] = {"error": str(e)}
                full_df.at[idx, "confidence_score"] = 0.0

    def _add_default_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega columnas por defecto cuando no se puede clasificar. Modifica in-place."""
        df["clasificacion_estrategia"] = TipoClasificacion.TODOS
        df["es_positivo"] = False
        df["tipo_eno_detectado"] = None
        df["metadata_extraida"] = None
        df["confidence_score"] = 0.0
        df["id_estrategia_aplicada"] = None
        df["trazabilidad_clasificacion"] = None
        return df
