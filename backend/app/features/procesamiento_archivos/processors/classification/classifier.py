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

from ..core.columns import Columns
from ..core.constants import METADATA_EXTRACTION_TYPES

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

        # Validar columnas requeridas usando sistema seguro
        try:
            Columns.validate_column(Columns.EVENTO)
            Columns.validate_column(Columns.GRUPO_EVENTO)

            if Columns.EVENTO not in df.columns:
                logger.error(f"Columna {Columns.EVENTO} no encontrada")
                return self._add_default_columns(df)

            if Columns.GRUPO_EVENTO not in df.columns:
                logger.error(f"Columna {Columns.GRUPO_EVENTO} no encontrada")
                return self._add_default_columns(df)

        except ValueError as e:
            logger.error(f"Error de validación: {e}")
            return self._add_default_columns(df)

        # Validar que todos los registros tienen GRUPO_EVENTO
        missing_grupo_evento = df[Columns.GRUPO_EVENTO].isnull() | (
            df[Columns.GRUPO_EVENTO] == ""
        )
        if missing_grupo_evento.any():
            logger.error(
                f"Se encontraron {missing_grupo_evento.sum()} registros sin GRUPO_EVENTO"
            )
            # Marcar registros problemáticos
            df = df.copy()
            df.loc[missing_grupo_evento, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
            # Continuar con los registros válidos
            df = df[~missing_grupo_evento]

        if df.empty:
            logger.error("No hay registros válidos para clasificar")
            return self._add_default_columns(df)

        # Agregar columnas de resultado
        df = df.copy()
        df["clasificacion_estrategia"] = None
        df["es_positivo"] = False
        df["tipo_eno_detectado"] = None
        df["metadata_extraida"] = None
        df["confidence_score"] = 0.0

        # Procesar por tipo de evento usando acceso seguro
        grouped = df.groupby(Columns.EVENTO)

        for evento_name, group_df in grouped:
            try:
                self._classify_event_group(df, group_df, str(evento_name))
            except Exception as e:
                logger.error(f"Error clasificando {evento_name}: {e}")
                df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION

        logger.info("Clasificación completada")
        return df

    def _classify_event_group(
        self, full_df: pd.DataFrame, group_df: pd.DataFrame, evento_name: str
    ):
        """Clasifica un grupo de eventos del mismo tipo."""
        # Detectar si es dengue y seleccionar 5 casos random para logging
        is_dengue = 'dengue' in evento_name.lower()
        sample_ids = []

        if is_dengue and 'IDEVENTOCASO' in group_df.columns:
            # Seleccionar hasta 5 casos random
            sample_size = min(5, len(group_df))
            sample_indices = group_df.sample(n=sample_size).index
            sample_ids = group_df.loc[sample_indices, 'IDEVENTOCASO'].tolist()
            logger.error(f"🦟 DENGUE: Procesando {len(group_df)} casos de '{evento_name}' - Logeando muestra de {len(sample_ids)}: {sample_ids}")

        # 1. Obtener tipo ENO
        tipo_eno = self._get_tipo_eno(evento_name)

        if not tipo_eno:
            # El evento no está en nuestro seed - marcarlo como requiere revisión
            if is_dengue and sample_ids:
                logger.error(f"🦟 DENGUE: Evento '{evento_name}' no está en el seed - marcando muestra {sample_ids} como REQUIERE_REVISION")
            logger.warning(f"Evento '{evento_name}' no está en el seed - marcando como REQUIERE_REVISION")
            full_df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
            return

        if is_dengue and sample_ids:
            logger.error(f"🦟 DENGUE: Tipo ENO encontrado: ID={tipo_eno['id']}, Nombre={tipo_eno['nombre']}, Código={tipo_eno['codigo']}")

        full_df.loc[group_df.index, "tipo_eno_detectado"] = tipo_eno["nombre"]

        # 2. Aplicar clasificación de BD
        if self.classification_service:
            try:
                if is_dengue and sample_ids:
                    logger.error(f"🦟 DENGUE: Aplicando estrategia de clasificación para tipo_eno_id={tipo_eno['id']}")
                    # Log datos de muestra antes de clasificación
                    for sample_id in sample_ids[:2]:  # Solo primeros 2 para no saturar logs
                        sample_row = group_df[group_df['IDEVENTOCASO'] == sample_id]
                        if not sample_row.empty:
                            # Mostrar solo campos relevantes
                            relevant_fields = ['IDEVENTOCASO', 'CLASIFICACIONMANUAL', 'SEMANAEPI', 'PROVINCIADERESIDENCIA']
                            sample_data = {k: v for k, v in sample_row.iloc[0].to_dict().items() if k in relevant_fields}
                            logger.error(f"🦟 DENGUE: Caso {sample_id} antes de clasificar: {sample_data}")

                classified_group = self.classification_service.classify_events(
                    group_df.copy(), tipo_eno["id"], sample_ids if is_dengue else []
                )

                if is_dengue and sample_ids:
                    # Mostrar resultados de muestra
                    for sample_id in sample_ids[:3]:
                        if sample_id in classified_group.index or (group_df['IDEVENTOCASO'] == sample_id).any():
                            idx = group_df[group_df['IDEVENTOCASO'] == sample_id].index[0]
                            clasificacion = classified_group.loc[idx, 'clasificacion'] if idx in classified_group.index else 'ERROR'
                            es_positivo = classified_group.loc[idx, 'es_positivo'] if idx in classified_group.index else False
                            logger.error(f"🦟 DENGUE: Caso {sample_id} → Clasificación: {clasificacion}, Es positivo: {es_positivo}")

                full_df.loc[group_df.index, "clasificacion_estrategia"] = (
                    classified_group["clasificacion"]
                )
                full_df.loc[group_df.index, "es_positivo"] = classified_group[
                    "es_positivo"
                ]

            except Exception as e:
                if is_dengue and sample_ids:
                    logger.error(f"🦟 DENGUE: ERROR en clasificación de muestra {sample_ids}: {e}")
                logger.error(f"Error en clasificación de BD: {e}")
                full_df.loc[group_df.index, "clasificacion_estrategia"] = TipoClasificacion.REQUIERE_REVISION
        else:
            # Usar GRUPO_EVENTO del CSV como clasificación
            logger.warning(
                "SyncEventClassificationService no disponible, usando GRUPO_EVENTO del CSV"
            )
            for idx in group_df.index:
                grupo_evento = group_df.loc[idx, Columns.GRUPO_EVENTO]
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

        # Log detallado para dengue
        is_dengue = 'dengue' in evento_name.lower()
        if is_dengue:
            logger.error(f"🔍 LOOKUP: Buscando tipo ENO - Nombre original: '{evento_name}' → Código generado: '{evento_codigo}'")

        # Buscar en cache (usando código como clave)
        if evento_codigo in self._tipo_eno_cache:
            if is_dengue:
                logger.error(f"🔍 LOOKUP: Encontrado en cache: {self._tipo_eno_cache[evento_codigo]}")
            return self._tipo_eno_cache[evento_codigo]

        # Buscar en BD por código (más robusto que buscar por nombre)
        try:
            from app.domains.eventos_epidemiologicos.eventos.models import TipoEno

            result = self.session.execute(
                select(TipoEno).where(TipoEno.codigo == evento_codigo)
            )
            tipo_eno = result.scalar_one_or_none()

            if is_dengue:
                logger.error(f"🔍 LOOKUP: Query ejecutada - Resultado: {tipo_eno}")

            if tipo_eno:
                tipo_eno_dict = {
                    "id": tipo_eno.id,
                    "nombre": tipo_eno.nombre,
                    "codigo": tipo_eno.codigo,
                }

                self._tipo_eno_cache[evento_codigo] = tipo_eno_dict
                if is_dengue:
                    logger.error(f"🔍 LOOKUP: ✅ Tipo ENO encontrado y cacheado: {tipo_eno_dict}")
                return tipo_eno_dict

        except Exception as e:
            if is_dengue:
                logger.error(f"🔍 LOOKUP: ❌ ERROR en query: {e}")
            logger.debug(f"Tipo ENO con código '{evento_codigo}' (evento: '{evento_name}') no encontrado en BD: {e}")

        # No encontrado - evento no está en el seed
        if is_dengue:
            logger.error(f"🔍 LOOKUP: ❌ No encontrado en BD - Código buscado: '{evento_codigo}'")
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
        """Agrega columnas por defecto cuando no se puede clasificar."""
        df = df.copy()
        df["clasificacion_estrategia"] = TipoClasificacion.TODOS
        df["es_positivo"] = False
        df["tipo_eno_detectado"] = None
        df["metadata_extraida"] = None
        df["confidence_score"] = 0.0
        return df


class ClassifierFactory:
    """Factory simple para crear clasificador."""

    @staticmethod
    def create_classifier(session: Session) -> EventClassifier:
        """Crea clasificador simple."""
        return EventClassifier(session)
