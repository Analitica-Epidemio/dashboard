"""Comorbidity operations for citizens - Polars puro optimizado."""

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.salud_models import Comorbilidad
from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
    Ciudadano,
    CiudadanoComorbilidades,
)

from ...config.columns import Columns
from ..shared import BulkOperationResult, BulkProcessorBase, pl_safe_int


class ComorbilidadesProcessor(BulkProcessorBase):
    """Handles comorbidity-related bulk operations."""

    def upsert_comorbilidades(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert of citizen comorbidities - OPTIMIZADO con Polars puro.

        OPTIMIZACIONES:
        - Lazy evaluation para query optimization
        - Join en Polars para mapear IDs (sin loop Python)
        - Filtro de ciudadanos existentes en Polars
        - Una sola conversión to_dicts() al final
        """
        start_time = self._get_current_timestamp()

        # Filter records with comorbidities - POLARS
        comorbilidades_df = df.filter(pl.col(Columns.COMORBILIDAD.name).is_not_null())

        if comorbilidades_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Create comorbidity mapping
        comorbilidad_mapping = self._get_or_create_comorbilidades(comorbilidades_df)

        if not comorbilidad_mapping:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Get existing citizens
        codigos_ciudadanos = (
            comorbilidades_df.filter(pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null())
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

        # Crear DataFrame de mapeo para hacer join en Polars
        mapping_df = pl.DataFrame({
            "comorbilidad_clean": list(comorbilidad_mapping.keys()),
            "id_comorbilidad": list(comorbilidad_mapping.values()),
        })

        # LAZY EVALUATION con join - TODO en expresiones Polars
        timestamp = self._get_current_timestamp()

        comorbilidades_prepared = (
            comorbilidades_df.lazy()
            .filter(
                pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null()
                & pl.col(Columns.COMORBILIDAD.name).is_not_null()
                & pl.col(Columns.CODIGO_CIUDADANO.name).is_in(list(ciudadanos_existentes))
            )
            .select([
                # Usar helper functions - sin casts redundantes
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                # Limpiar comorbilidad para join
                (
                    pl.col(Columns.COMORBILIDAD.name)
                    .str.strip_chars()
                    .str.to_uppercase()
                ).alias("comorbilidad_clean"),
            ])
            # JOIN en Polars para mapear IDs - mucho más rápido que loop Python
            .join(mapping_df.lazy(), on="comorbilidad_clean", how="inner")
            .drop("comorbilidad_clean")  # Ya no necesitamos este campo
            .with_columns([
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            .collect()  # Ejecutar todo el query plan optimizado
        )

        if comorbilidades_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Convertir a dicts para SQL (única conversión necesaria)
        valid_records = comorbilidades_prepared.to_dicts()

        # Insert
        stmt = pg_insert(CiudadanoComorbilidades.__table__).values(valid_records)
        upsert_stmt = stmt.on_conflict_do_nothing()
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(valid_records),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    def _get_or_create_comorbilidades(self, df: pl.DataFrame) -> dict[str, int]:
        """
        Get or create comorbidity catalog entries - POLARS PURO.

        OPTIMIZACIÓN: Usa get_or_create_catalog() para hacer:
        - 1 query para traer existentes (en vez de N queries)
        - 1 bulk insert para faltantes (en vez de N inserts)
        - 1 query final para IDs (en vez de N queries)

        Antes: O(n) queries → Ahora: O(1) queries (3 queries totales)
        """
        from ..shared import get_or_create_catalog

        # LAZY EVALUATION - limpiar y obtener valores únicos
        df_clean = (
            df.lazy()
            .filter(pl.col(Columns.COMORBILIDAD.name).is_not_null())
            .select([
                # Limpiar descripciones con expresiones Polars
                (
                    pl.col(Columns.COMORBILIDAD.name)
                    .str.strip_chars()
                    .str.to_uppercase()
                ).alias(Columns.COMORBILIDAD.name)
            ])
            .unique()
            .filter(
                # Filtrar strings vacíos
                pl.col(Columns.COMORBILIDAD.name).str.len_chars() > 0
            )
            .collect()
        )

        if df_clean.height == 0:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Comorbilidad,
            df=df_clean,
            column=Columns.COMORBILIDAD.name,
            key_field="descripcion",
            name_field="descripcion",
        )
