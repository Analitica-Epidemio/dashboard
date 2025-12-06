"""
Clasificador simple de eventos epidemiológicos.

Usa Polars para máximo rendimiento - sin complexity patterns innecesarios.
"""

import logging
from typing import Any, Dict, Optional

import polars as pl
from sqlalchemy import select
from sqlmodel import Session

from app.core.slug import generar_slug
from app.domains.vigilancia_nominal.clasificacion.models import TipoClasificacion

from .config import Columns

logger = logging.getLogger(__name__)


class EventClassifier:
    """
    Clasificador simple que usa estrategias de BD.

    Sin strategy pattern - solo la implementación que necesitas.
    """

    def __init__(self, session: Session):
        self.session = session
        self._cache_tipo_eno: Dict[str, Any] = {}

        # Importar servicio de clasificación
        try:
            from app.domains.vigilancia_nominal.clasificacion.sync_services import (
                SyncEventClassificationService,
            )

            self.servicio_clasificacion = SyncEventClassificationService(session)
        except ImportError:
            logger.warning("SyncEventClassificationService no disponible")
            self.servicio_clasificacion = None

        # Importar extractor de metadata
        try:
            from app.domains.vigilancia_nominal.clasificacion.detectors import (
                TipoSujetoDetector,
            )

            self.detector_tipo_sujeto = TipoSujetoDetector()
        except ImportError:
            logger.warning("TipoSujetoDetector no disponible")
            self.detector_tipo_sujeto = None

    def clasificar(self, df: pl.DataFrame) -> pl.DataFrame:
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
            return self._agregar_columnas_defecto(df)

        if Columns.GRUPO_EVENTO.name not in df.columns:
            logger.error(f"Columna {Columns.GRUPO_EVENTO.name} no encontrada")
            return self._agregar_columnas_defecto(df)

        # Validar que todos los registros tienen GRUPO_EVENTO
        mascara_faltantes = (
            pl.col(Columns.GRUPO_EVENTO.name).is_null() |
            (pl.col(Columns.GRUPO_EVENTO.name) == "")
        )

        if df.select(mascara_faltantes).to_series().any():
            conteo_faltantes = df.select(mascara_faltantes).to_series().sum()
            logger.error(f"Se encontraron {conteo_faltantes} registros sin GRUPO_EVENTO")

            # Marcar registros sin GRUPO_EVENTO como requieren revisión
            df = df.with_columns([
                pl.when(mascara_faltantes)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia") if "clasificacion_estrategia" in df.columns else None)
                .alias("clasificacion_estrategia")
            ])

            # Filtrar para continuar solo con registros válidos
            df = df.filter(~mascara_faltantes)

        if df.height == 0:
            logger.error("No hay registros válidos para clasificar")
            return self._agregar_columnas_defecto(df)

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

        for nombre_evento in eventos_unicos:
            try:
                # Filtrar registros de este evento
                mascara = pl.col(Columns.EVENTO.name) == nombre_evento
                indices_evento = df.with_row_count("__idx__").filter(mascara).select("__idx__").to_series().to_list()

                # Procesar este grupo
                df = self._clasificar_grupo_evento_polars(df, nombre_evento, indices_evento)
            except Exception as e:
                logger.error(f"Error clasificando {nombre_evento}: {e}")
                # Marcar como requiere revisión
                df = df.with_columns([
                    pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
                    .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                    .otherwise(pl.col("clasificacion_estrategia"))
                    .alias("clasificacion_estrategia")
                ])

        logger.info("Clasificación completada")

        return df

    def _clasificar_grupo_evento_polars(
        self, df: pl.DataFrame, nombre_evento: str, indices: list
    ) -> pl.DataFrame:
        """Clasifica un grupo de eventos del mismo tipo - Polars puro."""
        # 1. Obtener tipo ENO
        tipo_eno = self._obtener_tipo_eno(nombre_evento)

        if not tipo_eno:
            # El evento no está en nuestro seed - marcarlo como requiere revisión
            logger.warning(f"CasoEpidemiologico '{nombre_evento}' no está en el seed - marcando como REQUIERE_REVISION")
            return df.with_columns([
                pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia"))
                .alias("clasificacion_estrategia")
            ])

        # Marcar tipo_eno_detectado
        df = df.with_columns([
            pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
            .then(pl.lit(tipo_eno["nombre"]))
            .otherwise(pl.col("tipo_eno_detectado"))
            .alias("tipo_eno_detectado")
        ])

        # 2. Aplicar clasificación de BD
        if self.servicio_clasificacion:
            try:
                # El servicio de clasificación usa pandas, así que convertimos SOLO este grupo
                grupo_df = df.filter(pl.col(Columns.EVENTO.name) == nombre_evento)
                grupo_pandas = grupo_df.to_pandas()

                grupo_clasificado = self.servicio_clasificacion.classify_events(
                    grupo_pandas, tipo_eno["id"]
                )

                # Convertir resultado de vuelta a Polars
                polars_clasificado = pl.from_pandas(grupo_clasificado)

                # Verificar que el resultado tenga la columna 'clasificacion'
                if "clasificacion" in polars_clasificado.columns and Columns.IDEVENTOCASO.name in grupo_df.columns:
                    # OPTIMIZACIÓN: Usar JOIN de Polars VECTORIZADO
                    # 1. Agregar índice temporal para correlacionar las filas
                    grupo_con_idx = grupo_df.with_row_count("__row_idx__")
                    clasificado_con_idx = polars_clasificado.with_row_count("__row_idx__")

                    # 2. JOIN para obtener clasificaciones por índice
                    unido = grupo_con_idx.join(
                        clasificado_con_idx.select(["__row_idx__", "clasificacion"]),
                        on="__row_idx__",
                        how="left"
                    )

                    # 3. Extraer mapa de IDEVENTOCASO -> clasificacion
                    mapa_clasificaciones = unido.select([
                        Columns.IDEVENTOCASO.name,
                        "clasificacion"
                    ]).unique(subset=[Columns.IDEVENTOCASO.name], maintain_order=True)

                    # 4. JOIN con df principal (VECTORIZADO)
                    # IMPORTANTE: Renombrar la columna ANTES del JOIN para evitar conflictos de sufijos
                    mapa_clasificaciones = mapa_clasificaciones.rename({"clasificacion": "clasificacion_nueva"})

                    df = df.join(
                        mapa_clasificaciones,
                        on=Columns.IDEVENTOCASO.name,
                        how="left"
                    )

                    # 5. Actualizar clasificacion_estrategia solo para este evento
                    # Usar when/then para solo tocar las filas de este evento
                    if "clasificacion_nueva" in df.columns:
                        df = df.with_columns([
                            pl.when(
                                (pl.col(Columns.EVENTO.name) == nombre_evento) &
                                pl.col("clasificacion_nueva").is_not_null()
                            )
                            .then(pl.col("clasificacion_nueva"))
                            .otherwise(pl.col("clasificacion_estrategia"))
                            .alias("clasificacion_estrategia")
                        ]).drop("clasificacion_nueva")
                    else:
                        # El JOIN no agregó la columna, todos quedaron null
                        logger.warning(f"No se pudo obtener clasificaciones para {nombre_evento}")
                else:
                    # Sin columna clasificacion o sin IDEVENTOCASO, marcar como requiere revisión
                    df = df.with_columns([
                        pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
                        .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                        .otherwise(pl.col("clasificacion_estrategia"))
                        .alias("clasificacion_estrategia")
                    ])

            except Exception as e:
                logger.error(f"Error en clasificación de BD: {e}")
                df = df.with_columns([
                    pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
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
                pl.when(pl.col(Columns.EVENTO.name) == nombre_evento)
                .then(pl.lit(TipoClasificacion.REQUIERE_REVISION))
                .otherwise(pl.col("clasificacion_estrategia"))
                .alias("clasificacion_estrategia")
            ])

        return df

    def _obtener_tipo_eno(self, nombre_evento: str) -> Optional[Dict[str, Any]]:
        """Obtiene tipo ENO desde cache o BD usando código kebab-case."""
        if not nombre_evento or not nombre_evento.strip():
            return None

        # Convertir nombre del evento a slug estable
        slug_evento = generar_slug(nombre_evento)

        # Buscar en cache
        if slug_evento in self._cache_tipo_eno:
            return self._cache_tipo_eno[slug_evento]

        # Buscar en BD por slug (más robusto que buscar por nombre)
        try:
            from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad

            resultado = self.session.execute(
                select(Enfermedad).where(Enfermedad.slug == slug_evento)
            )
            enfermedad = resultado.scalar_one_or_none()

            if enfermedad:
                dict_enfermedad = {
                    "id": enfermedad.id,
                    "nombre": enfermedad.nombre,
                    "slug": enfermedad.slug,
                }

                self._cache_tipo_eno[slug_evento] = dict_enfermedad
                return dict_enfermedad

        except Exception as e:
            logger.debug(f"Enfermedad con slug '{slug_evento}' (evento: '{nombre_evento}') no encontrada en BD: {e}")

        # No encontrado - evento no está en el seed
        self._cache_tipo_eno[slug_evento] = None
        return None

    def _extraer_metadata(
        self, df_completo: pl.DataFrame, df_grupo: pl.DataFrame, nombre_tipo_eno: str
    ):
        """Extrae metadata para tipos específicos."""
        if not self.detector_tipo_sujeto:
            return

        for idx in df_grupo.index:
            try:
                fila = df_grupo.loc[idx]

                # Detectar tipo de sujeto
                tipo_sujeto, confianza, metadata = self.detector_tipo_sujeto.detectar(
                    fila.to_dict()
                )

                df_completo.at[idx, "metadata_extraida"] = metadata if metadata else None
                df_completo.at[idx, "confidence_score"] = confianza

            except Exception as e:
                logger.warning(f"Error extrayendo metadata para fila {idx}: {e}")
                df_completo.at[idx, "metadata_extraida"] = {"error": str(e)}
                df_completo.at[idx, "confidence_score"] = 0.0

    def _agregar_columnas_defecto(self, df: pl.DataFrame) -> pl.DataFrame:
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
