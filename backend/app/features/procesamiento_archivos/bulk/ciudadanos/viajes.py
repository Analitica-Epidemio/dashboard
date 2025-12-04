"""Trip operations for citizens - Polars puro optimizado."""

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.sujetos_epidemiologicos.viajes_models import ViajesCiudadano

from ...config.columns import Columns
from ..shared import BulkOperationResult, BulkProcessorBase, pl_safe_date, pl_safe_int


class ViajesProcessor(BulkProcessorBase):
    """Handles trip-related bulk operations."""

    def upsert_viajes(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert citizen trips - OPTIMIZADO con Polars puro.

        OPTIMIZACIONES:
        - Lazy evaluation
        - Sin loops Python para fechas (todo en expresiones Polars)
        - Filtro único para ciudadanos existentes
        """
        start_time = self._get_current_timestamp()

        # Get existing citizens primero para filtrar después
        codigos_ciudadanos = (
            df.filter(pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null())
            .select(Columns.CODIGO_CIUDADANO.name)
            .unique()
            .to_series()
            .to_list()
        )

        stmt = select(Ciudadano.codigo_ciudadano).where(
            Ciudadano.codigo_ciudadano.in_(codigos_ciudadanos)
        )
        ciudadanos_existentes = set(
            codigo for (codigo,) in self.context.session.execute(stmt).all()
        )

        # LAZY EVALUATION - todo el procesamiento en un solo query plan
        timestamp = self._get_current_timestamp()

        viajes_prepared = (
            df.lazy()
            # Filtros combinados en una sola pasada
            .filter(
                (
                    pl.col(Columns.ID_SNVS_VIAJE_EPIDEMIO.name).is_not_null()
                    | pl.col(Columns.FECHA_INICIO_VIAJE.name).is_not_null()
                    | (
                        pl.col(Columns.PAIS_VIAJE.name).is_not_null()
                        if Columns.PAIS_VIAJE.name in df.columns
                        else pl.lit(False)
                    )
                    | (
                        pl.col(Columns.LOC_VIAJE.name).is_not_null()
                        if Columns.LOC_VIAJE.name in df.columns
                        else pl.lit(False)
                    )
                )
                & pl.col(Columns.CODIGO_CIUDADANO.name).is_in(list(ciudadanos_existentes))
                & pl.col(Columns.ID_SNVS_VIAJE_EPIDEMIO.name).is_not_null()
            )
            .unique(subset=[Columns.ID_SNVS_VIAJE_EPIDEMIO.name])
            .select([
                pl_safe_int(Columns.ID_SNVS_VIAJE_EPIDEMIO.name).alias("id_snvs_viaje_epidemiologico"),
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),

                # Fechas - conversión en Polars (sin loops Python)
                (
                    pl_safe_date(Columns.FECHA_INICIO_VIAJE.name)
                    if Columns.FECHA_INICIO_VIAJE.name in df.columns
                    else pl.lit(None)
                ).alias("fecha_inicio_viaje"),
                (
                    pl_safe_date(Columns.FECHA_FIN_VIAJE.name)
                    if Columns.FECHA_FIN_VIAJE.name in df.columns
                    else pl.lit(None)
                ).alias("fecha_finalizacion_viaje"),

                # IDs opcionales
                (
                    pl_safe_int(Columns.ID_LOC_INDEC_VIAJE.name)
                    if Columns.ID_LOC_INDEC_VIAJE.name in df.columns
                    else pl.lit(None)
                ).alias("id_localidad_destino_viaje"),

                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            .collect()
        )

        if viajes_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Convertir a dicts para SQL (única conversión)
        viajes_data = viajes_prepared.to_dicts()

        # PostgreSQL UPSERT
        stmt = pg_insert(ViajesCiudadano.__table__).values(viajes_data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id_snvs_viaje_epidemiologico"],
            set_={
                "fecha_inicio_viaje": stmt.excluded.fecha_inicio_viaje,
                "fecha_finalizacion_viaje": stmt.excluded.fecha_finalizacion_viaje,
                "id_localidad_destino_viaje": stmt.excluded.id_localidad_destino_viaje,
                "updated_at": self._get_current_timestamp(),
            },
        )
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(viajes_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
