"""Bulk processor for health-related data (samples, vaccines, treatments)."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.vigilancia_nominal.models.salud import (
    Vacuna,
    VacunasCiudadano,
)

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    get_or_create_catalog,
    pl_clean_string,
    pl_safe_date,
    pl_safe_int,
)


class SaludProcessor(BulkProcessorBase):
    """Handles health-related bulk operations."""


class VacunasProcessor(BulkProcessorBase):
    """Handles vaccine operations."""

    def upsert_vacunas_ciudadanos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de vacunas de ciudadanos - POLARS PURO."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de vacunas - POLARS LAZY
        has_dosis = Columns.DOSIS.name in df.columns

        vacunas_df = (
            df.lazy()
            .filter(
                pl.col(Columns.VACUNA.name).is_not_null()
                | pl.col(Columns.FECHA_APLICACION.name).is_not_null()
                | (pl.col(Columns.DOSIS.name).is_not_null() if has_dosis else pl.lit(False))
            )
            .collect()
        )

        if vacunas_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {vacunas_df.height} vacunas ciudadanos")

        # Crear catálogo de vacunas
        vacuna_mapping = self._get_or_create_vacunas(vacunas_df)

        # POLARS PURO: Prepare data with lazy evaluation
        timestamp = self._get_current_timestamp()

        # Crear mapping de vacunas para join: {vacuna_clean -> id_vacuna}
        vacuna_df = pl.DataFrame({
            "vacuna_clean": list(vacuna_mapping.keys()),
            "id_vacuna": list(vacuna_mapping.values())
        })

        # Pipeline completo con Polars
        vacunas_prepared = (
            vacunas_df.lazy()
            # 1. Transformaciones básicas
            .select([
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                pl.col("id_caso"),
                pl_clean_string(Columns.VACUNA.name).str.to_uppercase().alias("vacuna_clean"),
                pl_safe_date(Columns.FECHA_APLICACION.name).alias("fecha_aplicacion"),
                (
                    pl.col(Columns.DOSIS.name).cast(pl.Utf8).str.strip_chars()
                    if has_dosis
                    else pl.lit(None, dtype=pl.Utf8)
                ).alias("dosis"),
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            # 2. Join con vacuna_mapping
            .join(
                vacuna_df.lazy(),
                on="vacuna_clean",
                how="left"
            )
            # 4. Filtrar registros válidos (must have ciudadano, vacuna, and fecha)
            .filter(
                pl.col("codigo_ciudadano").is_not_null()
                & pl.col("id_vacuna").is_not_null()
                & pl.col("fecha_aplicacion").is_not_null()
            )
            # 5. Limpiar dosis: convertir valores vacíos/nan a None
            .with_columns([
                pl.when(
                    pl.col("dosis").is_null()
                    | (pl.col("dosis") == "")
                    | (pl.col("dosis").str.to_lowercase() == "nan")
                    | (pl.col("dosis").str.to_lowercase() == "none")
                )
                .then(None)
                .otherwise(pl.col("dosis"))
                .alias("dosis")
            ])
            # 6. Seleccionar solo columnas finales
            .select([
                "codigo_ciudadano",
                "id_caso",
                "id_vacuna",
                "fecha_aplicacion",
                "dosis",
                "created_at",
                "updated_at",
            ])
            .collect()
        )

        # UNA SOLA conversión to_dicts al final
        valid_records = vacunas_prepared.to_dicts()

        if valid_records:
            stmt = pg_insert(VacunasCiudadano.__table__).values(valid_records)
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
            inserted_count=len(valid_records),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _get_or_create_vacunas(self, df: pl.DataFrame) -> dict[str, int]:
        """Get or create vaccine catalog entries - POLARS PURO."""
        # Extraer y limpiar nombres con POLARS PURO
        df_clean = (
            df.lazy()
            .filter(pl.col(Columns.VACUNA.name).is_not_null())
            .select(pl_clean_string(Columns.VACUNA.name).str.to_uppercase().alias(Columns.VACUNA.name))
            .unique()
            .filter(pl.col(Columns.VACUNA.name).is_not_null())  # Filtrar strings vacíos convertidos a null
            .collect()
        )

        if df_clean.height == 0:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Vacuna,
            df=df_clean,
            column=Columns.VACUNA.name,
            key_field="nombre",
            name_field="nombre",
        )
