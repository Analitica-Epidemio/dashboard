"""Comorbidity operations for citizens."""

from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.salud_models import Comorbilidad
from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
    Ciudadano,
    CiudadanoComorbilidades,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class ComorbilidadesProcessor(BulkProcessorBase):
    """Handles comorbidity-related bulk operations."""

    def upsert_comorbilidades(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert of citizen comorbidities."""
        start_time = self._get_current_timestamp()

        # Filter records with comorbidities
        comorbilidades_df = df[df[Columns.COMORBILIDAD.name].notna()]

        if comorbilidades_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Create comorbidity mapping
        comorbilidad_mapping = self._get_or_create_comorbilidades(comorbilidades_df)

        # Get existing citizens
        codigos_ciudadanos = (
            comorbilidades_df[Columns.CODIGO_CIUDADANO.name].dropna().unique().tolist()
        )

        stmt = select(Ciudadano.codigo_ciudadano).where(
            Ciudadano.codigo_ciudadano.in_(codigos_ciudadanos)
        )
        ciudadanos_existentes = set(
            codigo for (codigo,) in self.context.session.execute(stmt).all()
        )

        # VECTORIZED: Process comorbidities (10-50x faster than .apply())
        comorbilidades_df = comorbilidades_df.copy()

        # Clean and map comorbidities vectorially
        comorbilidades_df['comorbilidad_clean'] = comorbilidades_df[Columns.COMORBILIDAD.name].astype(str).str.strip().str.upper()
        comorbilidades_df['id_comorbilidad'] = comorbilidades_df['comorbilidad_clean'].map(comorbilidad_mapping)

        # Filter only comorbidities with existing citizen and valid ID
        valid_comorbilidades = comorbilidades_df[
            comorbilidades_df[Columns.CODIGO_CIUDADANO.name].isin(ciudadanos_existentes) &
            comorbilidades_df['id_comorbilidad'].notna()
        ]

        if valid_comorbilidades.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # VECTORIZED: Build data dict using pure column operations
        timestamp = self._get_current_timestamp()
        comorbilidades_ciudadano_data = {
            "codigo_ciudadano": pd.to_numeric(valid_comorbilidades[Columns.CODIGO_CIUDADANO.name], errors='coerce').astype('Int64'),
            "id_comorbilidad": valid_comorbilidades['id_comorbilidad'].astype(int),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        comorbilidades_ciudadano_data = pd.DataFrame(comorbilidades_ciudadano_data).to_dict('records')

        if comorbilidades_ciudadano_data:
            stmt = pg_insert(CiudadanoComorbilidades.__table__).values(
                comorbilidades_ciudadano_data
            )
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(comorbilidades_ciudadano_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    def _get_or_create_comorbilidades(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Get or create comorbidity catalog entries.

        OPTIMIZACIÓN: Usa get_or_create_catalog() para hacer:
        - 1 query para traer existentes (en vez de N queries)
        - 1 bulk insert para faltantes (en vez de N inserts)
        - 1 query final para IDs (en vez de N queries)

        Antes: O(n) queries → Ahora: O(1) queries (3 queries totales)
        """
        from ..shared import get_or_create_catalog

        # Limpiar descripciones primero
        tipos_comorbilidad = df[Columns.COMORBILIDAD.name].dropna().unique()
        df_clean = pd.DataFrame({
            Columns.COMORBILIDAD.name: [
                self._clean_string(desc)
                for desc in tipos_comorbilidad
                if self._clean_string(desc)
            ]
        })

        if df_clean.empty:
            return {}

        return get_or_create_catalog(
            session=self.context.session,
            model=Comorbilidad,
            df=df_clean,
            column=Columns.COMORBILIDAD.name,
            key_field="descripcion",
            name_field="descripcion",
        )
