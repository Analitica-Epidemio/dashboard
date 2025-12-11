"""Bulk processor for hospitalization events - POLARS PURO."""

import polars as pl
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.vigilancia_nominal.models.atencion import InternacionCasoEpidemiologico

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    pl_clean_string,
    pl_map_boolean,
    pl_safe_date,
)


class InternacionesProcessor(BulkProcessorBase):
    """Handles hospitalization event operations."""

    def upsert_internaciones_eventos(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert de internaciones de eventos - POLARS PURO con lazy evaluation."""
        start_time = self._get_current_timestamp()

        # Construir filtro de columnas existentes
        filter_conditions = []
        if Columns.FECHA_INTERNACION.name in df.columns:
            filter_conditions.append(
                pl.col(Columns.FECHA_INTERNACION.name).is_not_null()
            )
        if Columns.FECHA_ALTA_MEDICA.name in df.columns:
            filter_conditions.append(
                pl.col(Columns.FECHA_ALTA_MEDICA.name).is_not_null()
            )
        if Columns.CUIDADO_INTENSIVO.name in df.columns:
            filter_conditions.append(
                pl.col(Columns.CUIDADO_INTENSIVO.name).is_not_null()
            )
        if Columns.FECHA_CUI_INTENSIVOS.name in df.columns:
            filter_conditions.append(
                pl.col(Columns.FECHA_CUI_INTENSIVOS.name).is_not_null()
            )

        # Si no hay columnas de internaciones, retornar vacío
        if not filter_conditions:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Combinar condiciones con OR
        combined_filter = filter_conditions[0]
        for condition in filter_conditions[1:]:
            combined_filter = combined_filter | condition

        # POLARS LAZY: Filtrar y preparar datos en una sola pipeline
        timestamp = self._get_current_timestamp()

        # Pipeline completa con lazy evaluation
        # NOTA: id_evento ya viene del JOIN en main.py, no necesitamos crearlo aquí
        internaciones_prepared = (
            df.lazy()
            .filter(combined_filter)
            # Filtrar solo registros con id_evento válido (ya viene del JOIN en main.py)
            .filter(pl.col("id_caso").is_not_null())
            # Seleccionar y transformar todas las columnas en una sola operación
            .select(
                [
                    pl.col("id_caso"),
                    # Booleans: usar pl_map_boolean helper
                    (
                        pl_map_boolean(Columns.INTERNADO.name)
                        if Columns.INTERNADO.name in df.columns
                        else pl.lit(None)
                    ).alias("fue_internado"),
                    (
                        pl_map_boolean(Columns.CURADO.name)
                        if Columns.CURADO.name in df.columns
                        else pl.lit(None)
                    ).alias("fue_curado"),
                    (
                        pl_map_boolean(Columns.CUIDADO_INTENSIVO.name)
                        if Columns.CUIDADO_INTENSIVO.name in df.columns
                        else pl.lit(None)
                    ).alias("requirio_cuidado_intensivo"),
                    (
                        pl_map_boolean(Columns.FALLECIDO.name)
                        if Columns.FALLECIDO.name in df.columns
                        else pl.lit(None)
                    ).alias("es_fallecido"),
                    # Fechas: usar pl_safe_date helper
                    (
                        pl_safe_date(Columns.FECHA_INTERNACION.name)
                        if Columns.FECHA_INTERNACION.name in df.columns
                        else pl.lit(None)
                    ).alias("fecha_internacion"),
                    (
                        pl_safe_date(Columns.FECHA_ALTA_MEDICA.name)
                        if Columns.FECHA_ALTA_MEDICA.name in df.columns
                        else pl.lit(None)
                    ).alias("fecha_alta_medica"),
                    (
                        pl_safe_date(Columns.FECHA_CUI_INTENSIVOS.name)
                        if Columns.FECHA_CUI_INTENSIVOS.name in df.columns
                        else pl.lit(None)
                    ).alias("fecha_cuidados_intensivos"),
                    (
                        pl_safe_date(Columns.FECHA_FALLECIMIENTO.name)
                        if Columns.FECHA_FALLECIMIENTO.name in df.columns
                        else pl.lit(None)
                    ).alias("fecha_fallecimiento"),
                    # String: usar pl_clean_string helper
                    (
                        pl_clean_string(Columns.ESTABLECIMIENTO_INTERNACION.name)
                        if Columns.ESTABLECIMIENTO_INTERNACION.name in df.columns
                        else pl.lit(None)
                    ).alias("establecimiento_internacion"),
                    # Timestamps
                    pl.lit(timestamp).alias("created_at"),
                    pl.lit(timestamp).alias("updated_at"),
                ]
            )
            # Filtrar registros que tienen al menos un dato relevante
            .filter(
                pl.col("fecha_internacion").is_not_null()
                | pl.col("fecha_alta_medica").is_not_null()
                | pl.col("requirio_cuidado_intensivo").is_not_null()
                | pl.col("fecha_cuidados_intensivos").is_not_null()
            )
            .collect()  # Ejecutar la pipeline lazy
        )

        if internaciones_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(
            f"Bulk upserting {internaciones_prepared.height} internaciones"
        )

        # Convertir a dicts para inserción
        valid_records = internaciones_prepared.to_dicts()

        # Insertar en BD
        if valid_records:
            table = inspect(InternacionCasoEpidemiologico).local_table
            stmt = pg_insert(table).values(valid_records)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["id_caso"])
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(valid_records),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
