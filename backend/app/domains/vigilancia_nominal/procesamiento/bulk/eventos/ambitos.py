"""Bulk processor for ambitos de concurrencia - POLARS PURO OPTIMIZADO."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import SQLModel

from app.core.constants import FrecuenciaOcurrencia
from app.domains.vigilancia_nominal.models.ambitos import AmbitosConcurrenciaCaso

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    pl_col_or_null,
    pl_map_boolean,
    pl_safe_date,
)


class AmbitosProcessor(BulkProcessorBase):
    """Handles place of occurrence operations."""

    def upsert_ambitos_concurrencia(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert de ámbitos de concurrencia con Polars puro.

        Filtra registros con datos de ámbitos, hace join con evento_mapping,
        transforma campos y mapea frecuencia a enum.
        """
        start_time = self._get_current_timestamp()

        # Filtro: registros con cualquier dato de ámbito
        filter_cols = [
            Columns.TIPO_LUGAR_OCURRENCIA.name,
            Columns.NOMBRE_LUGAR_OCURRENCIA.name,
            Columns.LOCALIDAD_AMBITO_OCURRENCIA.name,
            Columns.SITIO_PROBABLE_ADQUISICION.name,
            Columns.SITIO_PROBABLE_DISEMINACION.name,
            Columns.FRECUENCIA.name,
            Columns.FECHA_AMBITO_OCURRENCIA.name,
        ]

        conditions = [pl.col(c).is_not_null() for c in filter_cols if c in df.columns]
        if not conditions:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        ambitos_df = df.filter(pl.any_horizontal(conditions))
        if ambitos_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Transformaciones con expresiones Polars
        timestamp = self._get_current_timestamp()

        # Mapeo de frecuencia
        frecuencia_mapping = {
            "UNICA|ÚNICA|UNA VEZ|1 VEZ": FrecuenciaOcurrencia.UNICA_VEZ.value,
            "DIARI": FrecuenciaOcurrencia.DIARIA.value,
            "SEMAN": FrecuenciaOcurrencia.SEMANAL.value,
            "MENSUAL|MES": FrecuenciaOcurrencia.MENSUAL.value,
            "ANUAL|AÑO": FrecuenciaOcurrencia.ANUAL.value,
            "OCASIONAL|ESPORADIC": FrecuenciaOcurrencia.OCASIONAL.value,
        }

        frecuencia_expr = pl.lit(None)
        if Columns.FRECUENCIA.name in ambitos_df.columns:
            base_expr = (
                pl.col(Columns.FRECUENCIA.name).str.to_uppercase().str.strip_chars()
            )
            for pattern, value in frecuencia_mapping.items():
                frecuencia_expr = (
                    pl.when(base_expr.str.contains(pattern))
                    .then(pl.lit(value))
                    .otherwise(frecuencia_expr)
                )

        ambitos_prepared = ambitos_df.select(
            [
                pl.col("id_caso"),
                pl_col_or_null(ambitos_df, Columns.NOMBRE_LUGAR_OCURRENCIA.name).alias(
                    "nombre_lugar_ocurrencia"
                ),
                pl_col_or_null(ambitos_df, Columns.TIPO_LUGAR_OCURRENCIA.name).alias(
                    "tipo_lugar_ocurrencia"
                ),
                pl_col_or_null(
                    ambitos_df, Columns.LOCALIDAD_AMBITO_OCURRENCIA.name
                ).alias("localidad_ambito_ocurrencia"),
                pl_col_or_null(
                    ambitos_df, Columns.FECHA_AMBITO_OCURRENCIA.name, pl_safe_date
                ).alias("fecha_ambito_ocurrencia"),
                pl_col_or_null(
                    ambitos_df, Columns.SITIO_PROBABLE_ADQUISICION.name, pl_map_boolean
                ).alias("es_sitio_probable_adquisicion_infeccion"),
                pl_col_or_null(
                    ambitos_df, Columns.SITIO_PROBABLE_DISEMINACION.name, pl_map_boolean
                ).alias("es_sitio_probable_diseminacion_infeccion"),
                frecuencia_expr.alias("frecuencia_concurrencia"),
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ]
        ).filter(
            # Solo registros con datos relevantes
            pl.col("nombre_lugar_ocurrencia").is_not_null()
            | pl.col("tipo_lugar_ocurrencia").is_not_null()
            | pl.col("fecha_ambito_ocurrencia").is_not_null()
        )

        if ambitos_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # PostgreSQL UPSERT
        ambitos_data = ambitos_prepared.to_dicts()
        table = SQLModel.metadata.tables[AmbitosConcurrenciaCaso.__tablename__]
        stmt = pg_insert(table).values(ambitos_data)
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["id_caso"])
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(ambitos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
