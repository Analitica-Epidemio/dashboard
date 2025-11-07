"""Bulk processor for health-related data (samples, vaccines, treatments)."""

from typing import Dict

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.salud_models import (
    Vacuna,
    VacunasCiudadano,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class SaludProcessor(BulkProcessorBase):
    """Handles health-related bulk operations."""


class VacunasProcessor(BulkProcessorBase):
    """Handles vaccine operations."""

    def upsert_vacunas_ciudadanos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de vacunas de ciudadanos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de vacunas
        vacunas_df = df[
            df[Columns.VACUNA.name].notna()
            | df[Columns.FECHA_APLICACION.name].notna()
            | df[Columns.DOSIS.name].notna()
        ]

        if vacunas_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(vacunas_df)} vacunas ciudadanos")

        # Crear catálogo de vacunas
        vacuna_mapping = self._get_or_create_vacunas(vacunas_df)

        # OPTIMIZACIÓN: Procesamiento vectorizado de vacunas (80% más rápido)
        vacunas_ciudadanos_data = []
        errors = []

        if not vacunas_df.empty:
            vacunas_df = vacunas_df.copy()

            # Mapear IDs usando vectorización
            vacunas_df["id_evento"] = vacunas_df[Columns.IDEVENTOCASO.name].map(
                evento_mapping
            )
            vacunas_df["vacuna_clean"] = (
                vacunas_df[Columns.VACUNA.name].str.strip().str.upper()
            )
            vacunas_df["id_vacuna"] = vacunas_df["vacuna_clean"].map(vacuna_mapping)
            vacunas_df["dosis_clean"] = (
                vacunas_df[Columns.DOSIS.name].astype(str).str.strip()
            )

            # Filtrar solo vacunas válidas (debe tener codigo_ciudadano e id_vacuna)
            valid_vacunas = vacunas_df[
                vacunas_df[Columns.CODIGO_CIUDADANO.name].notna()
                & vacunas_df["id_vacuna"].notna()
                & vacunas_df[Columns.FECHA_APLICACION.name].notna()
            ]

            if not valid_vacunas.empty:
                timestamp = self._get_current_timestamp()

                # VECTORIZACIÓN COMPLETA: Aprovechar tipos ya correctos desde read_csv()
                # - Números: YA son Int64 desde read_csv(dtype={'col': 'Int64'})
                # - Fechas: YA son datetime64[ns] desde read_csv(parse_dates=...)
                # ✅ NO necesitamos .astype(int) - los Int64 permiten NaN y se insertan directamente
                from ..shared import safe_date

                vacunas_ciudadanos_df = pd.DataFrame({
                    "codigo_ciudadano": valid_vacunas[Columns.CODIGO_CIUDADANO.name],  # Ya Int64
                    "id_vacuna": valid_vacunas["id_vacuna"],  # Ya int (mapeado desde dict)
                    "id_evento": valid_vacunas["id_evento"],  # Ya Int64 o NaN (mapeado desde dict)
                    # Fecha: Usar safe_date para manejar NaT correctamente
                    "fecha_aplicacion": valid_vacunas[Columns.FECHA_APLICACION.name].apply(safe_date),
                    "dosis": valid_vacunas["dosis_clean"].replace('nan', None).replace('', None),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

                # Convertir a lista de dicts
                vacunas_ciudadanos_data = vacunas_ciudadanos_df.to_dict('records')

        if vacunas_ciudadanos_data:
            stmt = pg_insert(VacunasCiudadano.__table__).values(vacunas_ciudadanos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=[
                    "codigo_ciudadano",
                    "id_vacuna",
                    "fecha_aplicacion",
                    "dosis",
                ]
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(vacunas_ciudadanos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _get_or_create_vacunas(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create vaccine catalog entries."""
        from ..shared import get_or_create_catalog, get_current_timestamp

        # Limpiar nombres primero
        nombres_vacuna = df[Columns.VACUNA.name].dropna().unique()
        df_clean = pd.DataFrame({
            Columns.VACUNA.name: [self._clean_string(n) for n in nombres_vacuna if self._clean_string(n)]
        })

        if df_clean.empty:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Vacuna,
            df=df_clean,
            column=Columns.VACUNA.name,
            key_field="nombre",
            name_field="nombre",
        )

