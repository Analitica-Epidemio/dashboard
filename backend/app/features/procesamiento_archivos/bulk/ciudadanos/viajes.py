"""Trip operations for citizens."""

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.sujetos_epidemiologicos.viajes_models import ViajesCiudadano

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class ViajesProcessor(BulkProcessorBase):
    """Handles trip-related bulk operations."""

    def upsert_viajes(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert citizen trips."""
        start_time = self._get_current_timestamp()

        # Filter records with trip information
        viajes_df = df[
            df[Columns.ID_SNVS_VIAJE_EPIDEMIO.name].notna()
            | df[Columns.FECHA_INICIO_VIAJE.name].notna()
            | df[Columns.PAIS_VIAJE.name].notna()
            | df[Columns.LOC_VIAJE.name].notna()
        ]

        if viajes_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Get existing citizens
        codigos_ciudadanos = (
            viajes_df[Columns.CODIGO_CIUDADANO.name].dropna().unique().tolist()
        )

        stmt = select(Ciudadano.codigo_ciudadano).where(
            Ciudadano.codigo_ciudadano.in_(codigos_ciudadanos)
        )
        ciudadanos_existentes = set(
            codigo for (codigo,) in self.context.session.execute(stmt).all()
        )

        # VECTORIZED: Process trips (10-50x faster than .apply())
        viajes_df = viajes_df.copy()

        # Filter only trips with existing citizen and valid trip ID
        viajes_df = viajes_df[
            viajes_df[Columns.CODIGO_CIUDADANO.name].isin(ciudadanos_existentes) &
            viajes_df[Columns.ID_SNVS_VIAJE_EPIDEMIO.name].notna()
        ]

        if viajes_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Deduplicate by id_snvs_viaje_epidemiologico
        viajes_df = viajes_df.drop_duplicates(subset=[Columns.ID_SNVS_VIAJE_EPIDEMIO.name])

        # VECTORIZED: Build data dict using pure column operations
        timestamp = self._get_current_timestamp()
        viajes_data = {
            "id_snvs_viaje_epidemiologico": pd.to_numeric(viajes_df[Columns.ID_SNVS_VIAJE_EPIDEMIO.name], errors='coerce').astype('Int64'),
            "codigo_ciudadano": pd.to_numeric(viajes_df[Columns.CODIGO_CIUDADANO.name], errors='coerce').astype('Int64'),
            "fecha_inicio_viaje": pd.to_datetime(viajes_df[Columns.FECHA_INICIO_VIAJE.name], errors='coerce', dayfirst=True) if Columns.FECHA_INICIO_VIAJE in viajes_df else None,
            "fecha_finalizacion_viaje": pd.to_datetime(viajes_df[Columns.FECHA_FIN_VIAJE.name], errors='coerce', dayfirst=True) if Columns.FECHA_FIN_VIAJE in viajes_df else None,
            "id_localidad_destino_viaje": pd.to_numeric(viajes_df[Columns.ID_LOC_INDEC_VIAJE.name], errors='coerce').astype('Int64') if Columns.ID_LOC_INDEC_VIAJE in viajes_df else None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        viajes_data = pd.DataFrame(viajes_data).to_dict('records')

        if viajes_data:
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
