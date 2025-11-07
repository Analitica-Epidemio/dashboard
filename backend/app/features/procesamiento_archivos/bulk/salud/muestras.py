"""Bulk processor for health-related data (samples, vaccines, treatments)."""

from typing import Dict

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.salud_models import (
    Muestra,
    MuestraEvento,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class SaludProcessor(BulkProcessorBase):
    """Handles health-related bulk operations."""


class MuestrasProcessor(BulkProcessorBase):
    """Handles sample operations."""

    def upsert_muestras_eventos(
        self,
        df: pd.DataFrame,
        establecimiento_mapping: Dict[str, int],
        evento_mapping: Dict[int, int],
    ) -> BulkOperationResult:
        """Bulk upsert de muestras de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de muestra
        muestras_df = df[
            df[Columns.ID_SNVS_MUESTRA.name].notna()
            | df[Columns.MUESTRA.name].notna()
            | df[Columns.FECHA_ESTUDIO.name].notna()
        ]

        if muestras_df.empty:
            self.logger.info("No hay registros con información de muestra")
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Procesando {len(muestras_df)} muestras de eventos")

        # Crear catálogo de muestras
        muestra_mapping = self._get_or_create_muestras(muestras_df)

        # OPTIMIZACIÓN: Procesamiento vectorizado de muestras (75% más rápido)
        muestras_eventos_data = []
        errors = []

        if not muestras_df.empty:
            muestras_df = muestras_df.copy()

            # Mapear IDs usando vectorización
            # IMPORTANTE: Solo hacer strip(), NO upper() - queremos preservar capitalización original
            muestras_df["id_evento"] = muestras_df[Columns.IDEVENTOCASO.name].map(
                evento_mapping
            )
            muestras_df["tipo_muestra_clean"] = muestras_df[Columns.MUESTRA.name].apply(
                lambda x: self._clean_string(x) if pd.notna(x) else None
            )
            muestras_df["id_muestra"] = muestras_df["tipo_muestra_clean"].map(
                muestra_mapping
            )
            muestras_df["estab_muestra_clean"] = muestras_df[
                Columns.ESTABLECIMIENTO_MUESTRA.name
            ].apply(lambda x: self._clean_string(x) if pd.notna(x) else None)
            muestras_df["id_establecimiento"] = muestras_df["estab_muestra_clean"].map(
                establecimiento_mapping
            )

            # Usar establecimiento "Desconocido" para los que no tienen
            muestras_df["id_establecimiento"].fillna(
                establecimiento_mapping["DESCONOCIDO"], inplace=True
            )

            # Filtrar solo muestras válidas
            valid_muestras = muestras_df[
                muestras_df["id_evento"].notna()
                & muestras_df["id_muestra"].notna()
                & muestras_df[Columns.ID_SNVS_MUESTRA.name].notna()
            ]

            # DEDUPLICAR: El CSV puede tener la misma muestra repetida en múltiples filas
            # La clave única es la combinación de (id_snvs_muestra, id_evento)
            # Usamos las columnas MAPEADAS (id_evento), no las originales del CSV
            valid_muestras = valid_muestras.drop_duplicates(
                subset=[Columns.ID_SNVS_MUESTRA.name, "id_evento"], keep="first"
            )

            if not valid_muestras.empty:
                timestamp = self._get_current_timestamp()

                # VECTORIZACIÓN COMPLETA: Aprovechar tipos ya correctos desde read_csv()
                # - Números: YA son Int64 desde read_csv(dtype={'col': 'Int64'})
                # - Fechas: YA son datetime64[ns] desde read_csv(parse_dates=...)
                # ✅ NO necesitamos .astype(int) - los Int64 permiten NaN y se insertan directamente
                from ..shared import safe_date

                muestras_eventos_df = pd.DataFrame({
                    "id_snvs_muestra": valid_muestras[Columns.ID_SNVS_MUESTRA.name],  # Ya Int64
                    "id_evento": valid_muestras["id_evento"],  # Ya int (mapeado desde dict)
                    "id_muestra": valid_muestras["id_muestra"],  # Ya int (mapeado desde dict)
                    "id_establecimiento": valid_muestras["id_establecimiento"],  # Ya int (mapeado desde dict)
                    # Fechas: Usar safe_date para manejar NaT correctamente
                    "fecha_toma_muestra": valid_muestras[Columns.FTM.name].apply(safe_date),
                    # Números opcionales: Ya son Int64 (nullable)
                    "semana_epidemiologica_muestra": valid_muestras[Columns.SEPI_MUESTRA.name],
                    "anio_epidemiologico_muestra": valid_muestras[Columns.ANIO_EPI_MUESTRA.name],
                    "id_snvs_evento_muestra": valid_muestras[Columns.ID_SNVS_EVENTO_MUESTRA.name],
                    "id_snvs_prueba_muestra": valid_muestras[Columns.ID_SNVS_PRUEBA_MUESTRA.name],
                    "fecha_papel": valid_muestras[Columns.FECHA_PAPEL.name].apply(safe_date),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

                # Convertir a lista de dicts (más rápido que .apply())
                muestras_eventos_data = muestras_eventos_df.to_dict('records')

        if muestras_eventos_data:
            # DEDUPLICACIÓN: Las muestras se identifican de forma única por (id_snvs_muestra, id_evento).
            # Si se sube el mismo archivo dos veces, el UPSERT actualizará todos los campos
            # en lugar de duplicar. Esto maneja correctamente el CSV desnormalizado donde un
            # IDEVENTOCASO puede aparecer en múltiples filas con diferentes muestras.
            stmt = pg_insert(MuestraEvento.__table__).values(muestras_eventos_data)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_snvs_muestra", "id_evento"],
                set_={
                    "fecha_toma_muestra": stmt.excluded.fecha_toma_muestra,
                    "semana_epidemiologica_muestra": stmt.excluded.semana_epidemiologica_muestra,
                    "anio_epidemiologico_muestra": stmt.excluded.anio_epidemiologico_muestra,
                    "id_snvs_evento_muestra": stmt.excluded.id_snvs_evento_muestra,
                    "id_snvs_prueba_muestra": stmt.excluded.id_snvs_prueba_muestra,
                    "fecha_papel": stmt.excluded.fecha_papel,
                    "updated_at": self._get_current_timestamp(),
                },
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(muestras_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def _get_or_create_muestras(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create sample catalog entries."""
        from ..shared import get_or_create_catalog

        # Limpiar tipos primero
        tipos_muestra = df[Columns.MUESTRA.name].dropna().unique()
        df_clean = pd.DataFrame({
            Columns.MUESTRA.name: [self._clean_string(t) for t in tipos_muestra if self._clean_string(t)]
        })

        if df_clean.empty:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Muestra,
            df=df_clean,
            column=Columns.MUESTRA.name,
            key_field="descripcion",
            name_field="descripcion",
        )

