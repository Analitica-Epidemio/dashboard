"""Bulk processor for treatment events - POLARS PURO OPTIMIZADO."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.diagnosticos_models import TratamientoEvento

from ...config.columns import Columns
from ..shared import (
    BulkProcessorBase,
    BulkOperationResult,
    pl_safe_date,
    pl_clean_string,
)


class TratamientosProcessor(BulkProcessorBase):
    """Handles treatment event operations."""

    def upsert_tratamientos_eventos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """
        Bulk upsert de tratamientos de eventos - POLARS PURO OPTIMIZADO.

        OPTIMIZACIONES:
        - Lazy evaluation para query optimization
        - Usa id_evento directamente desde df (ya viene del JOIN en main.py)
        - Deduplicación en Polars con .unique()
        - Validación y mapeo en expresiones Polars
        - Sin loops Python
        """
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de tratamientos - POLARS
        tratamientos_df = df.filter(
            (pl.col(Columns.TRATAMIENTO_2.name).is_not_null() if Columns.TRATAMIENTO_2.name in df.columns else pl.lit(False))
            | (pl.col(Columns.FECHA_INICIO_TRAT.name).is_not_null() if Columns.FECHA_INICIO_TRAT.name in df.columns else pl.lit(False))
            | (pl.col(Columns.FECHA_FIN_TRAT.name).is_not_null() if Columns.FECHA_FIN_TRAT.name in df.columns else pl.lit(False))
            | (pl.col(Columns.RESULTADO_TRATAMIENTO.name).is_not_null() if Columns.RESULTADO_TRATAMIENTO.name in df.columns else pl.lit(False))
        )

        if tratamientos_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {tratamientos_df.height} tratamientos")

        # Valores válidos del enum ResultadoTratamiento
        valores_validos = [
            "Adecuado (al menos 1 dosis al menos 30 días antes de FPP)",
            "Aplicado",
            "Curado",
            "Desconocido",
            "En tratamiento",
            "Éxito del tratamiento",
            "Fallecido",
            "Fracaso del tratamiento",
            "Inadecuado",
            "No corresponde",
            "Penicilina Benzatínica única dosis",
            "Pérdida de seguimiento",
            "Sin tratamiento",
            "Traslado",
            "Tratamiento completo",
            "Tratamiento en curso",
            "Tratamiento incompleto",
            "Tratamiento incompleto por abandono",
        ]

        # LAZY EVALUATION - Polars optimiza todo el query plan
        timestamp = self._get_current_timestamp()

        tratamientos_prepared = (
            tratamientos_df.lazy()
            # Agregar campos base
            .select([
                pl.col("id_evento"),  # Ya existe del JOIN en main.py
                (
                    pl_clean_string(Columns.TRATAMIENTO_2.name)
                    if Columns.TRATAMIENTO_2.name in tratamientos_df.columns
                    else pl.lit(None)
                ).alias("descripcion_tratamiento"),
                (
                    pl_clean_string(Columns.RESULTADO_TRATAMIENTO.name)
                    if Columns.RESULTADO_TRATAMIENTO.name in tratamientos_df.columns
                    else pl.lit(None)
                ).alias("resultado_tratamiento_raw"),
                (
                    pl_clean_string(Columns.ESTAB_TTO.name)
                    if Columns.ESTAB_TTO.name in tratamientos_df.columns
                    else pl.lit(None)
                ).alias("establecimiento_tratamiento"),
                (
                    pl_safe_date(Columns.FECHA_INICIO_TRAT.name)
                    if Columns.FECHA_INICIO_TRAT.name in tratamientos_df.columns
                    else pl.lit(None)
                ).alias("fecha_inicio_tratamiento"),
                (
                    pl_safe_date(Columns.FECHA_FIN_TRAT.name)
                    if Columns.FECHA_FIN_TRAT.name in tratamientos_df.columns
                    else pl.lit(None)
                ).alias("fecha_fin_tratamiento"),
            ])
            # Mapear resultado_tratamiento a valores válidos del enum
            .with_columns([
                pl.when(pl.col("resultado_tratamiento_raw").is_in(valores_validos))
                .then(pl.col("resultado_tratamiento_raw"))
                .otherwise(None)
                .alias("resultado_tratamiento")
            ])
            .drop("resultado_tratamiento_raw")
            # Filtrar registros inválidos - debe tener evento y al menos un campo
            .filter(
                pl.col("id_evento").is_not_null()
                & (
                    # Al menos uno de estos campos debe tener valor
                    (
                        pl.col("descripcion_tratamiento").is_not_null()
                        & (pl.col("descripcion_tratamiento") != "")
                        & (pl.col("descripcion_tratamiento") != "nan")
                        & (pl.col("descripcion_tratamiento") != "None")
                    )
                    | pl.col("fecha_inicio_tratamiento").is_not_null()
                    | pl.col("fecha_fin_tratamiento").is_not_null()
                    | pl.col("resultado_tratamiento").is_not_null()
                )
            )
            # Limpiar valores inválidos en descripcion_tratamiento
            .with_columns([
                pl.when(
                    (pl.col("descripcion_tratamiento") == "nan")
                    | (pl.col("descripcion_tratamiento") == "")
                    | (pl.col("descripcion_tratamiento") == "None")
                )
                .then(None)
                .otherwise(pl.col("descripcion_tratamiento"))
                .alias("descripcion_tratamiento")
            ])
            # Deduplicación en Polars (elimina loop Python + set)
            .unique(
                subset=[
                    "id_evento",
                    "descripcion_tratamiento",
                    "fecha_inicio_tratamiento",
                ],
                keep="first"
            )
            # Agregar timestamps
            .with_columns([
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            .collect()  # Aquí se ejecuta todo el query plan optimizado
        )

        if tratamientos_prepared.height == 0:
            self.logger.info("No hay tratamientos válidos después de filtrado y deduplicación")
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Tratamientos después de deduplicación: {tratamientos_prepared.height}")

        # Convertir a dicts para PostgreSQL insert
        valid_records = tratamientos_prepared.to_dicts()

        # PostgreSQL UPSERT
        stmt = pg_insert(TratamientoEvento.__table__).values(valid_records)
        upsert_stmt = stmt.on_conflict_do_nothing(
            index_elements=[
                "id_evento",
                "descripcion_tratamiento",
                "fecha_inicio_tratamiento",
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
