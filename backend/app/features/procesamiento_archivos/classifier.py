"""
Clasificador simple de eventos epidemiológicos.

Usa Polars para máximo rendimiento - sin complexity patterns innecesarios.
"""

import logging
from typing import Any, Dict, Optional

import polars as pl
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

    def classify(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Clasifica eventos usando estrategias de BD y GRUPO_EVENTO del CSV.

        Args:
            df: Polars DataFrame con eventos

        Returns:
            Polars DataFrame con clasificación aplicada
        """
        logger.info(f"Clasificando {df.height} eventos")

        # Validar columnas requeridas
        if Columns.EVENTO.name not in df.columns:
            logger.error(f"Columna {Columns.EVENTO.name} no encontrada")
            return self._add_default_columns(df)

        if Columns.GRUPO_EVENTO.name not in df.columns:
            logger.error(f"Columna {Columns.GRUPO_EVENTO.name} no encontrada")
            return self._add_default_columns(df)

        # Validar que todos los registros tienen GRUPO_EVENTO
        missing_mask = (
            pl.col(Columns.GRUPO_EVENTO.name).is_null() |
            (pl.col(Columns.GRUPO_EVENTO.name) == "")
        )

        if df.select(missing_mask).to_series().any():
            missing_count = df.select(missing_mask).to_series().sum()
            logger.error(f"Se encontraron {missing_count} registros sin GRUPO_EVENTO")

            # Marcar registros sin GRUPO_EVENTO como requieren revisión
            df = df.with_columns([
                pl.when(missing_mask)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia") if "clasificacion_estrategia" in df.columns else None)
                .alias("clasificacion_estrategia")
            ])

            # Filtrar para continuar solo con registros válidos
            df = df.filter(~missing_mask)

        if df.height == 0:
            logger.error("No hay registros válidos para clasificar")
            return self._add_default_columns(df)

        # Agregar columnas de clasificación con valores por defecto
        df = df.with_columns([
            pl.lit(None).cast(pl.Utf8).alias("clasificacion_estrategia") if "clasificacion_estrategia" not in df.columns else pl.col("clasificacion_estrategia"),
            pl.lit(False).alias("es_positivo"),
            pl.lit(None).cast(pl.Utf8).alias("tipo_eno_detectado"),
            pl.lit(None).alias("metadata_extraida"),
            pl.lit(0.0).alias("confidence_score"),
            pl.lit(None).alias("id_estrategia_aplicada"),
            pl.lit(None).alias("trazabilidad_clasificacion"),
        ])

        # Procesar por tipo de evento
        # Obtener eventos únicos
        eventos_unicos = df.select(Columns.EVENTO.name).unique().to_series().to_list()

        for evento_name in eventos_unicos:
            try:
                # Filtrar registros de este evento
                mask = pl.col(Columns.EVENTO.name) == evento_name
                indices_evento = df.with_row_count("__idx__").filter(mask).select("__idx__").to_series().to_list()

                # Procesar este grupo
                df = self._classify_event_group_polars(df, evento_name, indices_evento)
            except Exception as e:
                logger.error(f"Error clasificando {evento_name}: {e}")
                # Marcar como requiere revisión
                df = df.with_columns([
                    pl.when(pl.col(Columns.EVENTO.name) == evento_name)
                    .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                    .otherwise(pl.col("clasificacion_estrategia"))
                    .alias("clasificacion_estrategia")
                ])

        logger.info("Clasificación completada")

        return df

    def _classify_event_group_polars(
        self, df: pl.DataFrame, evento_name: str, indices: list
    ) -> pl.DataFrame:
        """Clasifica un grupo de eventos del mismo tipo - Polars puro."""
        # 1. Obtener tipo ENO
        tipo_eno = self._get_tipo_eno(evento_name)

        if not tipo_eno:
            # El evento no está en nuestro seed - marcarlo como requiere revisión
            logger.warning(f"Evento '{evento_name}' no está en el seed - marcando como REQUIERE_REVISION")
            return df.with_columns([
                pl.when(pl.col(Columns.EVENTO.name) == evento_name)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia"))
                .alias("clasificacion_estrategia")
            ])

        # Marcar tipo_eno_detectado
        df = df.with_columns([
            pl.when(pl.col(Columns.EVENTO.name) == evento_name)
            .then(pl.lit(tipo_eno["nombre"]))
            .otherwise(pl.col("tipo_eno_detectado"))
            .alias("tipo_eno_detectado")
        ])

        # 2. Aplicar clasificación de BD
        if self.classification_service:
            try:
                # El servicio de clasificación usa pandas, así que convertimos SOLO este grupo
                group_df = df.filter(pl.col(Columns.EVENTO.name) == evento_name)
                group_pandas = group_df.to_pandas()

                classified_group = self.classification_service.classify_events(
                    group_pandas, tipo_eno["id"]
                )

                # Convertir resultado de vuelta a Polars
                classified_polars = pl.from_pandas(classified_group)

                # Verificar que el resultado tenga la columna 'clasificacion'
                if "clasificacion" in classified_polars.columns and Columns.IDEVENTOCASO.name in group_df.columns:
                    # OPTIMIZACIÓN: Usar JOIN de Polars VECTORIZADO
                    # 1. Agregar índice temporal para correlacionar las filas
                    group_with_idx = group_df.with_row_count("__row_idx__")
                    classified_with_idx = classified_polars.with_row_count("__row_idx__")

                    # 2. JOIN para obtener clasificaciones por índice
                    merged = group_with_idx.join(
                        classified_with_idx.select(["__row_idx__", "clasificacion"]),
                        on="__row_idx__",
                        how="left"
                    )

                    # 3. Extraer mapa de IDEVENTOCASO -> clasificacion
                    clasificaciones_map = merged.select([
                        Columns.IDEVENTOCASO.name,
                        "clasificacion"
                    ]).unique(subset=[Columns.IDEVENTOCASO.name], maintain_order=True)

                    # 4. JOIN con df principal (VECTORIZADO)
                    # IMPORTANTE: Renombrar la columna ANTES del JOIN para evitar conflictos de sufijos
                    clasificaciones_map = clasificaciones_map.rename({"clasificacion": "clasificacion_nueva"})

                    df = df.join(
                        clasificaciones_map,
                        on=Columns.IDEVENTOCASO.name,
                        how="left"
                    )

                    # 5. Actualizar clasificacion_estrategia solo para este evento
                    # Usar when/then para solo tocar las filas de este evento
                    if "clasificacion_nueva" in df.columns:
                        df = df.with_columns([
                            pl.when(
                                (pl.col(Columns.EVENTO.name) == evento_name) &
                                pl.col("clasificacion_nueva").is_not_null()
                            )
                            .then(pl.col("clasificacion_nueva"))
                            .otherwise(pl.col("clasificacion_estrategia"))
                            .alias("clasificacion_estrategia")
                        ]).drop("clasificacion_nueva")
                    else:
                        # El JOIN no agregó la columna, todos quedaron null
                        logger.warning(f"No se pudo obtener clasificaciones para {evento_name}")
                else:
                    # Sin columna clasificacion o sin IDEVENTOCASO, marcar como requiere revisión
                    df = df.with_columns([
                        pl.when(pl.col(Columns.EVENTO.name) == evento_name)
                        .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                        .otherwise(pl.col("clasificacion_estrategia"))
                        .alias("clasificacion_estrategia")
                    ])

            except Exception as e:
                logger.error(f"Error en clasificación de BD: {e}")
                df = df.with_columns([
                    pl.when(pl.col(Columns.EVENTO.name) == evento_name)
                    .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                    .otherwise(pl.col("clasificacion_estrategia"))
                    .alias("clasificacion_estrategia")
                ])
        else:
            # Sin servicio de clasificación, marcar como requiere revisión
            logger.warning(
                "SyncEventClassificationService no disponible, marcando como REQUIERE_REVISION"
            )
            df = df.with_columns([
                pl.when(pl.col(Columns.EVENTO.name) == evento_name)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia"))
                .alias("clasificacion_estrategia")
            ])

        return df

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
        self, full_df: pl.DataFrame, group_df: pl.DataFrame, tipo_eno_name: str
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

    def _add_default_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Agrega columnas por defecto cuando no se puede clasificar."""
        return df.with_columns([
            pl.lit(TipoClasificacion.TODOS).alias("clasificacion_estrategia"),
            pl.lit(False).alias("es_positivo"),
            pl.lit(None).cast(pl.Utf8).alias("tipo_eno_detectado"),
            pl.lit(None).alias("metadata_extraida"),
            pl.lit(0.0).alias("confidence_score"),
            pl.lit(None).alias("id_estrategia_aplicada"),
            pl.lit(None).alias("trazabilidad_clasificacion"),
        ])
