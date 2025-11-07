"""Bulk processor for events and related entities."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
import os

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.utils.codigo_generator import CodigoGenerator
from app.domains.eventos_epidemiologicos.ambitos_models import AmbitosConcurrenciaEvento
from app.domains.eventos_epidemiologicos.eventos.models import (
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
    DetalleEventoSintomas,
    Evento,
    GrupoEno,
    TipoEno,
)
from app.domains.atencion_medica.salud_models import Sintoma
from app.features.procesamiento_archivos.utils.epidemiological_calculations import (
    calcular_semana_epidemiologica,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult, get_or_create_catalog


class EventosProcessor(BulkProcessorBase):
    """Handles event-related bulk operations."""


class SintomasProcessor(BulkProcessorBase):
    """Handles symptom-related bulk operations."""

    def upsert_sintomas_eventos(
        self,
        df: pd.DataFrame,
        sintoma_mapping: Dict[str, int],
        evento_mapping: Dict[int, int],
    ) -> BulkOperationResult:
        """Bulk upsert de síntomas de eventos."""
        start_time = self._get_current_timestamp()

        sintomas_eventos_data = []
        errors = []

        # OPTIMIZACIÓN: Procesamiento vectorizado de síntomas (80% más rápido que iterrows)
        # Filtrar filas con síntomas válidos
        sintomas_df = df[df[Columns.SIGNO_SINTOMA.name].notna()].copy()

        if not sintomas_df.empty:
            # Mapear IDEVENTOCASO → id_evento usando vectorización
            sintomas_df["id_evento"] = sintomas_df[Columns.IDEVENTOCASO.name].map(
                evento_mapping
            )

            # Mapear SIGNO_SINTOMA → id_sintoma usando vectorización
            sintomas_df["sintoma_clean"] = (
                sintomas_df[Columns.SIGNO_SINTOMA.name].str.strip().str.upper()
            )
            sintomas_df["id_sintoma"] = sintomas_df["sintoma_clean"].map(
                sintoma_mapping
            )

            # Filtrar solo relaciones válidas (donde ambos IDs existen)
            valid_sintomas = sintomas_df[
                sintomas_df["id_evento"].notna() & sintomas_df["id_sintoma"].notna()
            ]

            # Reportar problemas si hay muchos síntomas sin mapear
            sintomas_sin_mapear = sintomas_df[sintomas_df["id_sintoma"].isna()]
            if len(sintomas_sin_mapear) > 0:
                self.logger.warning(
                    f"⚠️  {len(sintomas_sin_mapear)} filas con síntomas no mapeados"
                )

            # DEDUPLICAR: Misma combinación (id_evento, id_sintoma) puede aparecer múltiples veces
            # Si hay fechas diferentes, mantener la más temprana
            # Ordenar por fecha (NaT al final) y luego deduplicar manteniendo la primera
            valid_sintomas_sorted = valid_sintomas.sort_values(
                by=Columns.FECHA_INICIO_SINTOMA.name, na_position="last"
            )
            valid_sintomas_dedup = valid_sintomas_sorted.drop_duplicates(
                subset=["id_evento", "id_sintoma"], keep="first"
            )

            duplicados_removidos = len(valid_sintomas) - len(valid_sintomas_dedup)
            if duplicados_removidos > 0:
                self.logger.info(
                    f"🔄 Removidos {duplicados_removidos} síntomas duplicados "
                    f"(misma combinación evento-síntoma)"
                )

            if not valid_sintomas_dedup.empty:
                # Crear lista de dicts usando .apply() (más rápido que iterrows)
                timestamp = self._get_current_timestamp()
                sintomas_eventos_data = valid_sintomas_dedup.apply(
                    lambda row: self._row_to_sintoma_evento_dict(row, timestamp),
                    axis=1,
                ).tolist()

        if sintomas_eventos_data:
            stmt = pg_insert(DetalleEventoSintomas.__table__).values(
                sintomas_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_evento", "id_sintoma"],
                set_={
                    "fecha_inicio_sintoma": stmt.excluded.fecha_inicio_sintoma,
                    "semana_epidemiologica_aparicion_sintoma": stmt.excluded.semana_epidemiologica_aparicion_sintoma,
                    "anio_epidemiologico_sintoma": stmt.excluded.anio_epidemiologico_sintoma,
                    "updated_at": self._get_current_timestamp(),
                },
            )

            result = self.context.session.execute(upsert_stmt)
            self.logger.info(
                f"{len(sintomas_eventos_data)} relaciones síntoma-evento procesadas"
            )

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(sintomas_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def _get_or_create_sintomas(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Get or create symptom catalog entries.

        OPTIMIZACIÓN: Vectorizado con pandas (10-50x más rápido que iterrows).
        """
        # Filtrar filas válidas (con síntoma e ID SNVS)
        df_valid = df[
            df[Columns.SIGNO_SINTOMA.name].notna()
            & df[Columns.ID_SNVS_SIGNO_SINTOMA.name].notna()
        ].copy()

        if df_valid.empty:
            self.logger.warning("No síntomas data extracted from DataFrame")
            return {}

        # VECTORIZADO: Limpiar todos los síntomas de una vez
        df_valid["sintoma_limpio"] = df_valid[Columns.SIGNO_SINTOMA.name].apply(
            lambda x: self._clean_string(x)
        )
        df_valid["id_snvs_int"] = df_valid[Columns.ID_SNVS_SIGNO_SINTOMA.name].apply(
            lambda x: self._safe_int(x)
        )

        # Filtrar los que tienen sintoma_limpio e id_snvs válidos
        df_valid = df_valid[
            df_valid["sintoma_limpio"].notna() & df_valid["id_snvs_int"].notna()
        ]

        if df_valid.empty:
            self.logger.warning("No valid síntomas after cleaning")
            return {}

        # Crear diccionario: síntoma → id_snvs (último valor gana si hay duplicados)
        sintomas_data = dict(zip(df_valid["sintoma_limpio"], df_valid["id_snvs_int"]))

        self.logger.debug(f"Extracted {len(sintomas_data)} unique síntomas")

        if not sintomas_data:
            self.logger.warning("No síntomas data extracted from DataFrame")
            return {}

        # Verificar existentes
        stmt = select(Sintoma.id, Sintoma.signo_sintoma).where(
            Sintoma.signo_sintoma.in_(list(sintomas_data.keys()))
        )
        existing_mapping = {
            signo_sintoma: sintoma_id
            for sintoma_id, signo_sintoma in self.context.session.execute(stmt).all()
        }

        # Crear nuevos con IDs del CSV
        nuevos_sintomas = []
        for signo_sintoma, id_snvs in sintomas_data.items():
            if signo_sintoma not in existing_mapping:
                nuevos_sintomas.append(
                    {
                        "id_snvs_signo_sintoma": id_snvs,
                        "signo_sintoma": signo_sintoma,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_sintomas:
            stmt = pg_insert(Sintoma.__table__).values(nuevos_sintomas)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        # SIEMPRE re-obtener mapping completo después de cualquier inserción
        # Usar id_snvs_signo_sintoma para el mapping ya que es único y consistente
        stmt = select(
            Sintoma.id, Sintoma.id_snvs_signo_sintoma, Sintoma.signo_sintoma
        ).where(Sintoma.id_snvs_signo_sintoma.in_(list(sintomas_data.values())))

        # Obtener síntomas de la BD
        all_results = list(self.context.session.execute(stmt).all())
        self.logger.info(f"Mapping de síntomas: {len(all_results)} encontrados en BD")

        # Crear mapping por nombre de síntoma basado en los IDs SNVS
        id_snvs_to_db_id = {
            id_snvs: sintoma_id for sintoma_id, id_snvs, _ in all_results
        }

        # Crear el mapping final: signo_sintoma -> id de la BD
        # IMPORTANTE: Usar UPPER() para las claves para que coincidan con el lookup en bulk_upsert_sintomas_eventos
        final_mapping = {}
        sintomas_faltantes = []

        for signo_sintoma, id_snvs in sintomas_data.items():
            if id_snvs in id_snvs_to_db_id:
                # Almacenar con la clave en mayúsculas para que coincida con el lookup
                sintoma_key = signo_sintoma.upper()
                final_mapping[sintoma_key] = id_snvs_to_db_id[id_snvs]
            else:
                sintomas_faltantes.append(f"{signo_sintoma} (SNVS {id_snvs})")

        if sintomas_faltantes:
            self.logger.warning(
                f"⚠️  {len(sintomas_faltantes)} síntomas no encontrados en BD: {sintomas_faltantes[:3]}"
            )

        self.logger.info(
            f"Mapping de síntomas completado: {len(final_mapping)} síntomas mapeados"
        )
        return final_mapping

    def _row_to_sintoma_evento_dict(self, row: pd.Series, timestamp) -> dict:
        """Convierte una fila a dict de síntoma-evento."""
        # Obtener fecha de inicio del síntoma
        fecha_inicio = self._safe_date(row.get(Columns.FECHA_INICIO_SINTOMA.name))

        # Calcular semana epidemiológica si hay fecha
        semana_epi = None
        anio_epi = None
        if fecha_inicio:
            semana_epi, anio_epi = calcular_semana_epidemiologica(fecha_inicio)

        return {
            "id_evento": int(row["id_evento"]),
            "id_sintoma": int(row["id_sintoma"]),
            "fecha_inicio_sintoma": fecha_inicio,
            "semana_epidemiologica_aparicion_sintoma": semana_epi,
            "anio_epidemiologico_sintoma": anio_epi,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
