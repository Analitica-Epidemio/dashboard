"""
Bulk processor para investigaciones epidemiológicas.

POLARS PURO - Optimizado con lazy evaluation y joins.
"""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.investigaciones_models import InvestigacionEvento

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    get_current_timestamp,
    pl_col_or_null,
)


def pl_map_origen_financiamiento(col_name: str) -> pl.Expr:
    """
    Expresión Polars para mapear origen financiamiento a enum.

    Mapea valores a OrigenFinanciamiento enum, removiendo acentos.
    """
    return (
        pl.col(col_name)
        .str.to_uppercase()
        .str.strip_chars()
        .str.replace_all("Ú", "U")
        .str.replace_all("Í", "I")
        .str.replace_all("Ó", "O")
        .str.replace_all("Á", "A")
        .str.replace_all("É", "E")
    )


def pl_has_any_investigacion_field() -> pl.Expr:
    """
    Expresión Polars para verificar si hay al menos un campo de investigación.

    Returns:
        Expresión booleana que es True si hay al menos un campo relevante.
    """
    conditions = []

    # Lista de campos a verificar
    field_checks = [
        ("investigacion_terreno_bool", lambda: pl.col("investigacion_terreno_bool").is_not_null()),
        ("fecha_investigacion", lambda: pl.col("fecha_investigacion").is_not_null()),
        ("tipo_y_lugar_investigacion", lambda: pl.col("tipo_y_lugar_investigacion").is_not_null()),
        ("origen_financiamiento", lambda: pl.col("origen_financiamiento").is_not_null()),
        ("id_snvs_evento", lambda: pl.col("id_snvs_evento").is_not_null()),
        ("usuario_centinela_bool", lambda: pl.col("usuario_centinela_bool").is_not_null()),
        ("evento_centinela_bool", lambda: pl.col("evento_centinela_bool").is_not_null()),
    ]

    for _, check_fn in field_checks:
        conditions.append(check_fn())

    # Combinar todas las condiciones con OR
    result = conditions[0]
    for condition in conditions[1:]:
        result = result | condition

    return result


class InvestigacionesEventosProcessor(BulkProcessorBase):
    """Procesa investigaciones epidemiológicas de eventos."""

    def upsert_investigaciones_eventos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """
        Bulk upsert de investigaciones de eventos - POLARS PURO.

        Optimizaciones:
        - Lazy evaluation completa
        - Join en Polars para evento_mapping (NO loops Python)
        - Una sola conversión to_dicts() al final
        - Expresiones Polars para todas las transformaciones
        """
        start_time = get_current_timestamp()

        # POLARS: Filtrar registros con al menos un campo de investigación
        # Verificar que las columnas existan antes de filtrar
        has_data = False
        filter_conditions = []

        columns_to_check = [
            Columns.INVESTIGACION_TERRENO.name,
            Columns.FECHA_INVESTIGACION.name,
            Columns.TIPO_Y_LUGAR_INVESTIGACION.name,
            Columns.ORIGEN_FINANCIAMIENTO.name,
            Columns.ID_SNVS_EVENTO.name,
            Columns.USER_CENTINELA.name,
            Columns.EVENTO_CENTINELA.name,
        ]

        for col_name in columns_to_check:
            if col_name in df.columns:
                filter_conditions.append(pl.col(col_name).is_not_null())
                has_data = True

        if not has_data:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Combinar condiciones con OR
        filter_expr = filter_conditions[0]
        for condition in filter_conditions[1:]:
            filter_expr = filter_expr | condition

        investigaciones_df = df.filter(filter_expr)

        if investigaciones_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # POLARS: Preparar datos con lazy evaluation
        timestamp = get_current_timestamp()

        # POLARS: Transformaciones completas en una sola operación
        investigaciones_prepared = (
            investigaciones_df.lazy()
            # id_evento ya está presente gracias al JOIN centralizado en main.py
            .filter(pl.col("id_evento").is_not_null())
            # Transformar todos los campos con expresiones Polars
            .with_columns([
                # Booleans - usar pl_map_boolean pattern
                pl_col_or_null(
                    investigaciones_df,
                    Columns.INVESTIGACION_TERRENO.name,
                    lambda col_name: (
                        pl.when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "SI")
                        .then(pl.lit(True))
                        .when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "NO")
                        .then(pl.lit(False))
                        .otherwise(None)
                    )
                ).alias("investigacion_terreno_bool"),

                pl_col_or_null(
                    investigaciones_df,
                    Columns.USER_CENTINELA.name,
                    lambda col_name: (
                        pl.when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "SI")
                        .then(pl.lit(True))
                        .when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "NO")
                        .then(pl.lit(False))
                        .otherwise(None)
                    )
                ).alias("usuario_centinela_bool"),

                pl_col_or_null(
                    investigaciones_df,
                    Columns.EVENTO_CENTINELA.name,
                    lambda col_name: (
                        pl.when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "SI")
                        .then(pl.lit(True))
                        .when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "NO")
                        .then(pl.lit(False))
                        .otherwise(None)
                    )
                ).alias("evento_centinela_bool"),

                pl_col_or_null(
                    investigaciones_df,
                    Columns.USER_CENT_PARTICIPO.name,
                    lambda col_name: (
                        pl.when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "SI")
                        .then(pl.lit(True))
                        .when(pl.col(col_name).str.to_uppercase().str.strip_chars() == "NO")
                        .then(pl.lit(False))
                        .otherwise(None)
                    )
                ).alias("usuario_cent_participo_bool"),

                # Fecha
                pl_col_or_null(
                    investigaciones_df,
                    Columns.FECHA_INVESTIGACION.name,
                    lambda col_name: pl.col(col_name).cast(pl.Date, strict=False)
                ).alias("fecha_investigacion"),

                # String limpio
                pl_col_or_null(
                    investigaciones_df,
                    Columns.TIPO_Y_LUGAR_INVESTIGACION.name,
                    lambda col_name: pl.col(col_name).str.strip_chars().replace("", None)
                ).alias("tipo_y_lugar_investigacion"),

                # Origen financiamiento con mapeo
                pl_col_or_null(
                    investigaciones_df,
                    Columns.ORIGEN_FINANCIAMIENTO.name,
                    lambda col_name: (
                        pl.col(col_name).str.to_uppercase()
                        .str.strip_chars()
                        .str.replace_all("Ú", "U")
                        .str.replace_all("Í", "I")
                        .str.replace_all("Ó", "O")
                        .str.replace_all("Á", "A")
                        .str.replace_all("É", "E")
                    )
                ).alias("origen_financiamiento"),

                # IDs
                pl_col_or_null(
                    investigaciones_df,
                    Columns.ID_SNVS_EVENTO.name,
                    lambda col_name: pl.col(col_name).cast(pl.Int64, strict=False)
                ).alias("id_snvs_evento"),

                pl_col_or_null(
                    investigaciones_df,
                    Columns.ID_USER_REGISTRO.name,
                    lambda col_name: pl.col(col_name).cast(pl.Int64, strict=False)
                ).alias("id_usuario_registro"),

                pl_col_or_null(
                    investigaciones_df,
                    Columns.ID_USER_CENT_PARTICIPO.name,
                    lambda col_name: pl.col(col_name).cast(pl.Int64, strict=False)
                ).alias("id_user_cent_participo"),

                # Timestamps
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            # Filtrar solo registros con al menos un campo relevante
            .filter(pl_has_any_investigacion_field())
            # Seleccionar solo columnas finales
            .select([
                "id_evento",
                pl.col("investigacion_terreno_bool").alias("es_investigacion_terreno"),
                "fecha_investigacion",
                "tipo_y_lugar_investigacion",
                "origen_financiamiento",
                "id_snvs_evento",
                pl.col("usuario_centinela_bool").alias("es_usuario_centinela"),
                pl.col("evento_centinela_bool").alias("es_evento_centinela"),
                "id_usuario_registro",
                pl.col("usuario_cent_participo_bool").alias("participo_usuario_centinela"),
                pl.col("id_user_cent_participo").alias("id_usuario_centinela_participante"),
                "created_at",
                "updated_at",
            ])
        ).collect()

        # Una sola conversión to_dicts() al final
        investigaciones_data = investigaciones_prepared.to_dicts()

        # Bulk insert
        if investigaciones_data:
            stmt = pg_insert(InvestigacionEvento.__table__).values(investigaciones_data)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        duration = (get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(investigaciones_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
