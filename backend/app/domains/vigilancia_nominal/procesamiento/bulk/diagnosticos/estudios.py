"""Bulk processor for study events - POLARS PURO."""

import polars as pl
from sqlalchemy import inspect, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col

from app.domains.vigilancia_nominal.models.salud import (
    EstudioCasoEpidemiologico,
    MuestraCasoEpidemiologico,
)

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    pl_clean_string,
    pl_safe_date,
)


class EstudiosProcessor(BulkProcessorBase):
    """Handles study event operations - POLARS PURO con lazy evaluation."""

    def upsert_estudios_eventos(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert de estudios de eventos - POLARS PURO.

        Optimizaciones:
        - Lazy evaluation para filtrado y transformaciones
        - Usa id_evento directamente desde df (ya viene del JOIN en main.py)
        - Join en Polars para muestra_mapping
        - Validación y limpieza con expresiones Polars
        - CERO loops Python
        """
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de estudios - POLARS LAZY
        estudios_df = (
            df.lazy()
            .filter(
                (
                    pl.col(Columns.DETERMINACION.name).is_not_null()
                    if Columns.DETERMINACION.name in df.columns
                    else pl.lit(False)
                )
                | (
                    pl.col(Columns.TECNICA.name).is_not_null()
                    if Columns.TECNICA.name in df.columns
                    else pl.lit(False)
                )
                | (
                    pl.col(Columns.RESULTADO.name).is_not_null()
                    if Columns.RESULTADO.name in df.columns
                    else pl.lit(False)
                )
                | (
                    pl.col(Columns.FECHA_ESTUDIO.name).is_not_null()
                    if Columns.FECHA_ESTUDIO.name in df.columns
                    else pl.lit(False)
                )
            )
            .collect()
        )

        if estudios_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {estudios_df.height} estudios")

        # ===== MAPEO DE MUESTRAS: Query SQL -> Polars DataFrame =====
        # Obtener mapping de muestras_evento desde BD
        stmt = select(
            col(MuestraCasoEpidemiologico.id),
            col(MuestraCasoEpidemiologico.id_snvs_muestra),
            col(MuestraCasoEpidemiologico.id_caso),  # Cambiado de id_evento a id_caso
        )
        muestra_rows = self.context.session.execute(stmt).all()

        # Convertir a DataFrame de Polars con schema explícito
        muestra_map_df = pl.DataFrame(
            {
                "id_muestra": [row[0] for row in muestra_rows],
                "id_snvs_muestra_join": [row[1] for row in muestra_rows],
                "id_caso_join": [
                    row[2] for row in muestra_rows
                ],  # Cambiado de id_evento_join a id_caso_join
            },
            schema={
                "id_muestra": pl.Int64,
                "id_snvs_muestra_join": pl.Int64,
                "id_caso_join": pl.Int64,  # Cambiado de id_evento_join a id_caso_join
            },
        )

        # ===== PREPARACIÓN Y TRANSFORMACIÓN CON POLARS LAZY =====
        timestamp = self._get_current_timestamp()

        estudios_prepared = (
            estudios_df.lazy()
            # 1. Extraer y limpiar columnas base
            .select(
                [
                    pl.col("id_caso"),  # Ya existe del JOIN en main.py
                    (
                        pl.col(Columns.ID_SNVS_MUESTRA.name).cast(
                            pl.Int64, strict=False
                        )
                        if Columns.ID_SNVS_MUESTRA.name in estudios_df.columns
                        else pl.lit(None, dtype=pl.Int64)
                    ).alias("id_snvs_muestra"),
                    (
                        pl_clean_string(Columns.DETERMINACION.name)
                        if Columns.DETERMINACION.name in estudios_df.columns
                        else pl.lit(None)
                    ).alias("determinacion"),
                    (
                        pl_clean_string(Columns.TECNICA.name)
                        if Columns.TECNICA.name in estudios_df.columns
                        else pl.lit(None)
                    ).alias("tecnica"),
                    (
                        pl_safe_date(Columns.FECHA_ESTUDIO.name)
                        if Columns.FECHA_ESTUDIO.name in estudios_df.columns
                        else pl.lit(None, dtype=pl.Date)
                    ).alias("fecha_estudio"),
                    (
                        pl_clean_string(Columns.RESULTADO.name)
                        if Columns.RESULTADO.name in estudios_df.columns
                        else pl.lit(None)
                    ).alias("resultado"),
                    (
                        pl_safe_date(Columns.FECHA_RECEPCION.name)
                        if Columns.FECHA_RECEPCION.name in estudios_df.columns
                        else pl.lit(None, dtype=pl.Date)
                    ).alias("fecha_recepcion"),
                ]
            )
            # 2. JOIN con muestra_mapping para obtener id_muestra (left join porque id_muestra es opcional)
            .join(
                muestra_map_df.lazy(),
                left_on=["id_snvs_muestra", "id_caso"],
                right_on=[
                    "id_snvs_muestra_join",
                    "id_caso_join",
                ],  # Cambiado de id_evento_join a id_caso_join
                how="left",
            )
            # 3. Filtrar registros que tienen al menos un dato relevante
            .filter(
                pl.col("determinacion").is_not_null()
                | pl.col("tecnica").is_not_null()
                | pl.col("fecha_estudio").is_not_null()
                | pl.col("resultado").is_not_null()
            )
            # 4. Seleccionar solo las columnas finales necesarias
            .select(
                [
                    "id_muestra",  # FK requerido
                    "determinacion",
                    "tecnica",
                    "fecha_estudio",
                    "resultado",
                    "fecha_recepcion",
                    pl.lit(timestamp).alias("created_at"),
                    pl.lit(timestamp).alias("updated_at"),
                ]
            )
            # 5. Filtrar solo estudios con id_muestra válido (FK requerido)
            .filter(pl.col("id_muestra").is_not_null())
            # 6. Remover duplicados (si existen)
            .unique(
                subset=["id_muestra", "determinacion", "tecnica", "fecha_estudio"],
                maintain_order=True,
            )
            .collect()
        )

        # Convertir a dict para inserción en BD
        valid_records = estudios_prepared.to_dicts()

        # ===== UPSERT EN BASE DE DATOS =====
        if valid_records:
            table = inspect(EstudioCasoEpidemiologico).local_table
            stmt = pg_insert(table).values(valid_records)
            # EstudioCasoEpidemiologico no tiene unique constraint explícito, usar do_nothing
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(valid_records),
            updated_count=0,
            skipped_count=estudios_df.height - len(valid_records),
            errors=[],
            duration_seconds=duration,
        )
