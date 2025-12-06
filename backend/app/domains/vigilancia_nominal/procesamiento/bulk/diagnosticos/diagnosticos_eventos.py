"""Bulk processor for diagnostic events - POLARS PURO."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.vigilancia_nominal.models.atencion import DiagnosticoCasoEpidemiologico

from ...config.columns import Columns
from ..shared import BulkOperationResult, BulkProcessorBase


class DiagnosticosCasoEpidemiologicosProcessor(BulkProcessorBase):
    """Handles diagnostic event operations."""

    def upsert_diagnosticos_eventos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de diagnósticos de eventos - POLARS PURO."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de diagnóstico - POLARS
        has_clasif_manual = Columns.CLASIFICACION_MANUAL.name in df.columns
        has_clasif_auto = Columns.CLASIFICACION_AUTOMATICA.name in df.columns
        has_diag_referido = Columns.DIAG_REFERIDO.name in df.columns

        filter_expr = pl.lit(False)
        if has_clasif_manual:
            filter_expr = filter_expr | pl.col(Columns.CLASIFICACION_MANUAL.name).is_not_null()
        if has_clasif_auto:
            filter_expr = filter_expr | pl.col(Columns.CLASIFICACION_AUTOMATICA.name).is_not_null()
        if has_diag_referido:
            filter_expr = filter_expr | pl.col(Columns.DIAG_REFERIDO.name).is_not_null()

        diagnosticos_df = df.filter(filter_expr)

        if diagnosticos_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {diagnosticos_df.height} diagnósticos")

        # POLARS: Preparar data con lazy evaluation
        timestamp = self._get_current_timestamp()

        # Construir selección dinámica basada en columnas disponibles
        # NOTE: id_evento already added by main.py via JOIN, use it directly
        select_exprs = [
            pl.col("id_caso"),
        ]

        # Clasificación manual
        if has_clasif_manual:
            select_exprs.append(
                pl.col(Columns.CLASIFICACION_MANUAL.name)
                .cast(pl.Utf8)
                .str.strip_chars()
                .replace("", None)
                .replace("nan", None)
                .replace("None", None)
                .alias("clasificacion_manual")
            )
        else:
            select_exprs.append(pl.lit(None).alias("clasificacion_manual"))

        # Clasificación automática
        if has_clasif_auto:
            select_exprs.append(
                pl.col(Columns.CLASIFICACION_AUTOMATICA.name)
                .cast(pl.Utf8)
                .str.strip_chars()
                .replace("", None)
                .replace("nan", None)
                .replace("None", None)
                .alias("clasificacion_automatica")
            )
        else:
            select_exprs.append(pl.lit(None).alias("clasificacion_automatica"))

        # Diagnóstico referido
        if has_diag_referido:
            select_exprs.append(
                pl.col(Columns.DIAG_REFERIDO.name)
                .cast(pl.Utf8)
                .str.strip_chars()
                .replace("", None)
                .replace("nan", None)
                .replace("None", None)
                .alias("diagnostico_referido")
            )
        else:
            select_exprs.append(pl.lit(None).alias("diagnostico_referido"))

        # Clasificación algoritmo (opcional)
        if Columns.CLASIFICACION_ALGORITMO.name in diagnosticos_df.columns:
            select_exprs.append(
                pl.col(Columns.CLASIFICACION_ALGORITMO.name)
                .str.strip_chars()
                .replace("", None)
                .alias("clasificacion_algoritmo")
            )
        else:
            select_exprs.append(pl.lit(None).alias("clasificacion_algoritmo"))

        # Validación (opcional)
        if Columns.VALIDACION.name in diagnosticos_df.columns:
            select_exprs.append(
                pl.col(Columns.VALIDACION.name)
                .str.strip_chars()
                .replace("", None)
                .alias("validacion")
            )
        else:
            select_exprs.append(pl.lit(None).alias("validacion"))

        # Timestamps
        select_exprs.extend([
            pl.lit(timestamp).alias("created_at"),
            pl.lit(timestamp).alias("updated_at"),
        ])

        # Aplicar selección
        diagnosticos_prepared = diagnosticos_df.select(select_exprs)

        # Filtrar registros que tienen al menos un campo de diagnóstico válido - POLARS PURO
        # Also filter out records without id_evento (left join nulls from main.py)
        diagnosticos_valid = diagnosticos_prepared.filter(
            (pl.col("id_caso").is_not_null())
            & (
                pl.col("clasificacion_manual").is_not_null()
                | pl.col("clasificacion_automatica").is_not_null()
                | pl.col("diagnostico_referido").is_not_null()
            )
        )

        # Aplicar default "Sin clasificar" para clasificacion_manual si es null
        diagnosticos_final = diagnosticos_valid.with_columns(
            pl.when(pl.col("clasificacion_manual").is_null())
            .then(pl.lit("Sin clasificar"))
            .otherwise(pl.col("clasificacion_manual"))
            .alias("clasificacion_manual")
        )

        # IMPORTANTE: Remover duplicados por id_evento (relación 1:1 con evento)
        # Si hay múltiples filas por evento, quedarse con la última
        diagnosticos_insert = diagnosticos_final.unique(subset=["id_caso"], keep="last")

        # Convertir a dicts para insert
        valid_records = diagnosticos_insert.to_dicts()

        if valid_records:
            stmt = pg_insert(DiagnosticoCasoEpidemiologico.__table__).values(valid_records)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_caso"],
                set_={
                    "clasificacion_manual": stmt.excluded.clasificacion_manual,
                    "clasificacion_automatica": stmt.excluded.clasificacion_automatica,
                    "clasificacion_algoritmo": stmt.excluded.clasificacion_algoritmo,
                    "validacion": stmt.excluded.validacion,
                    "diagnostico_referido": stmt.excluded.diagnostico_referido,
                    "updated_at": self._get_current_timestamp(),
                },
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
