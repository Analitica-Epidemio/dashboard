"""Bulk processor for health-related data (samples, vaccines, treatments)."""

from typing import Dict

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import SQLModel

from app.domains.vigilancia_nominal.models.salud import (
    Muestra,
    MuestraCasoEpidemiologico,
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


class MuestrasProcessor(BulkProcessorBase):
    """Handles sample operations."""

    def upsert_muestras_eventos(
        self,
        df: pl.DataFrame,
        establecimiento_mapping: Dict[str, int],
        evento_mapping: Dict[int, int],
    ) -> BulkOperationResult:
        """Bulk upsert de muestras de eventos - POLARS PURO."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de muestra - POLARS LAZY
        muestras_df = (
            df.lazy()
            .filter(
                pl.col(Columns.ID_SNVS_MUESTRA.name).is_not_null()
                | pl.col(Columns.MUESTRA.name).is_not_null()
                | (
                    pl.col(Columns.FECHA_ESTUDIO.name).is_not_null()
                    if Columns.FECHA_ESTUDIO.name in df.columns
                    else pl.lit(False)
                )
            )
            .collect()
        )

        if muestras_df.height == 0:
            self.logger.info("No hay registros con información de muestra")
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Procesando {muestras_df.height} muestras de eventos")

        # Crear catálogo de muestras
        muestra_mapping = self._get_or_create_muestras(muestras_df)

        # POLARS LAZY: Prepare data con expresiones optimizadas
        timestamp = self._get_current_timestamp()

        # Construir establecimiento_mapping como DataFrame para JOIN
        establecimiento_mapping_df = pl.DataFrame(
            {
                "estab_clean": list(establecimiento_mapping.keys()),
                "id_establecimiento": list(establecimiento_mapping.values()),
            }
        )

        # Construir muestra_mapping como DataFrame para JOIN
        muestra_mapping_df = pl.DataFrame(
            {
                "tipo_muestra_clean": list(muestra_mapping.keys()),
                "id_muestra": list(muestra_mapping.values()),
            }
        )

        # Preparar columnas base con lazy evaluation
        muestras_prepared = (
            muestras_df.lazy()
            .select(
                [
                    pl_safe_int(Columns.ID_SNVS_MUESTRA.name).alias("id_snvs_muestra"),
                    # Use id_evento directly - already added by main.py via JOIN
                    pl.col("id_caso"),
                    # Limpiar tipo de muestra
                    (
                        pl_clean_string(Columns.MUESTRA.name).str.to_uppercase()
                        if Columns.MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("tipo_muestra_clean"),
                    # Limpiar establecimiento
                    (
                        pl_clean_string(
                            Columns.ESTABLECIMIENTO_MUESTRA.name
                        ).str.to_uppercase()
                        if Columns.ESTABLECIMIENTO_MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("estab_clean"),
                    # Fecha de toma
                    (
                        pl_safe_date(Columns.FTM.name)
                        if Columns.FTM.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("fecha_toma_muestra"),
                    # Semana epidemiológica
                    (
                        pl_safe_int(Columns.SEPI_MUESTRA.name)
                        if Columns.SEPI_MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("semana_epidemiologica_muestra"),
                    # Año epidemiológico
                    (
                        pl_safe_int(Columns.ANIO_EPI_MUESTRA.name)
                        if Columns.ANIO_EPI_MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("anio_epidemiologico_muestra"),
                    # ID SNVS caso muestra
                    (
                        pl_safe_int(Columns.ID_SNVS_EVENTO_MUESTRA.name)
                        if Columns.ID_SNVS_EVENTO_MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias(
                        "id_snvs_caso_muestra"
                    ),  # Cambiado de id_snvs_evento_muestra a id_snvs_caso_muestra
                    # ID SNVS prueba muestra
                    (
                        pl_safe_int(Columns.ID_SNVS_PRUEBA_MUESTRA.name)
                        if Columns.ID_SNVS_PRUEBA_MUESTRA.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("id_snvs_prueba_muestra"),
                    # Fecha papel
                    (
                        pl_safe_date(Columns.FECHA_PAPEL.name)
                        if Columns.FECHA_PAPEL.name in muestras_df.columns
                        else pl.lit(None)
                    ).alias("fecha_papel"),
                    pl.lit(timestamp).alias("created_at"),
                    pl.lit(timestamp).alias("updated_at"),
                ]
            )
            # JOIN con muestra_mapping
            .join(muestra_mapping_df.lazy(), on="tipo_muestra_clean", how="left")
            # JOIN con establecimiento_mapping
            .join(establecimiento_mapping_df.lazy(), on="estab_clean", how="left")
            # Usar "Desconocido" si no hay establecimiento
            .with_columns(
                [
                    pl.when(pl.col("id_establecimiento").is_null())
                    .then(pl.lit(establecimiento_mapping.get("DESCONOCIDO")))
                    .otherwise(pl.col("id_establecimiento"))
                    .alias("id_establecimiento")
                ]
            )
            # Filtrar registros válidos: debe tener id_snvs_muestra, id_evento, y id_muestra
            .filter(
                pl.col("id_snvs_muestra").is_not_null()
                & pl.col("id_caso").is_not_null()
                & pl.col("id_muestra").is_not_null()
            )
            # Deduplicar por (id_snvs_muestra, id_evento) - mantener primer registro
            .unique(subset=["id_snvs_muestra", "id_caso"], keep="first")
            # Seleccionar columnas finales
            .select(
                [
                    "id_snvs_muestra",
                    "id_caso",
                    "id_muestra",
                    "id_establecimiento",
                    "fecha_toma_muestra",
                    "semana_epidemiologica_muestra",
                    "anio_epidemiologico_muestra",
                    "id_snvs_caso_muestra",  # Cambiado de id_snvs_evento_muestra a id_snvs_caso_muestra
                    "id_snvs_prueba_muestra",
                    "fecha_papel",
                    "created_at",
                    "updated_at",
                ]
            )
            .collect()
        )

        # Convertir a dicts para inserción
        muestras_eventos_data = muestras_prepared.to_dicts()

        if muestras_eventos_data:
            # DEDUPLICACIÓN: Las muestras se identifican de forma única por (id_snvs_muestra, id_evento).
            # Si se sube el mismo archivo dos veces, el UPSERT actualizará todos los campos
            # en lugar de duplicar. Esto maneja correctamente el CSV desnormalizado donde un
            # IDEVENTOCASO puede aparecer en múltiples filas con diferentes muestras.
            table = SQLModel.metadata.tables[MuestraCasoEpidemiologico.__tablename__]
            stmt = pg_insert(table).values(muestras_eventos_data)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_snvs_muestra", "id_caso"],
                set_={
                    "id_muestra": stmt.excluded.id_muestra,
                    "id_establecimiento": stmt.excluded.id_establecimiento,
                    "fecha_toma_muestra": stmt.excluded.fecha_toma_muestra,
                    "semana_epidemiologica_muestra": stmt.excluded.semana_epidemiologica_muestra,
                    "anio_epidemiologico_muestra": stmt.excluded.anio_epidemiologico_muestra,
                    "id_snvs_caso_muestra": stmt.excluded.id_snvs_caso_muestra,  # Cambiado de id_snvs_evento_muestra a id_snvs_caso_muestra
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
            errors=[],
            duration_seconds=duration,
        )

    def _get_or_create_muestras(self, df: pl.DataFrame) -> Dict[str, int]:
        """Get or create sample catalog entries - POLARS PURO."""
        # Limpiar tipos con POLARS LAZY
        tipos_muestra_clean = (
            df.lazy()
            .filter(pl.col(Columns.MUESTRA.name).is_not_null())
            .select(
                [
                    pl_clean_string(Columns.MUESTRA.name)
                    .str.to_uppercase()
                    .alias(Columns.MUESTRA.name)
                ]
            )
            .unique()
            .filter(pl.col(Columns.MUESTRA.name).is_not_null())
            .collect()
        )

        if tipos_muestra_clean.height == 0:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Muestra,
            df=tipos_muestra_clean,
            column=Columns.MUESTRA.name,
            key_field="descripcion",
            name_field="descripcion",
        )
