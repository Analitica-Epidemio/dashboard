"""Bulk processor for study events."""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.diagnosticos_models import EstudioEvento
from app.domains.atencion_medica.salud_models import MuestraEvento

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class EstudiosProcessor(BulkProcessorBase):
    """Handles study event operations."""

    def upsert_estudios_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de estudios de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de estudios
        estudios_df = df[
            df[Columns.DETERMINACION.name].notna()
            | df[Columns.TECNICA.name].notna()
            | df[Columns.RESULTADO.name].notna()
            | df[Columns.FECHA_ESTUDIO.name].notna()
        ]

        if estudios_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(estudios_df)} estudios")

        # Obtener mapping de muestras_evento (necesario para EstudioEvento)
        # Clave: (id_snvs_muestra, id_evento) → id_muestra_evento
        stmt = select(
            MuestraEvento.id, MuestraEvento.id_snvs_muestra, MuestraEvento.id_evento
        )
        muestra_mapping = {}
        for muestra_id, id_snvs_muestra, id_evento in self.context.session.execute(
            stmt
        ).all():
            muestra_mapping[(id_snvs_muestra, id_evento)] = muestra_id

        # OPTIMIZACIÓN: Usar .apply() en vez de iterrows() (2-5x más rápido)
        estudios_data = []
        errors = []

        def process_row(row):
            try:
                return self._row_to_estudio_dict(row, evento_mapping, muestra_mapping)
            except Exception as e:
                errors.append(f"Error preparando estudio evento: {e}")
                return None

        estudios_results = estudios_df.apply(process_row, axis=1)
        estudios_data = [e for e in estudios_results if e is not None]

        if estudios_data:
            stmt = pg_insert(EstudioEvento.__table__).values(estudios_data)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(estudios_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def _row_to_estudio_dict(
        self,
        row: pd.Series,
        evento_mapping: Dict[int, int],
        muestra_mapping: Dict[tuple, int],
    ) -> Optional[Dict]:
        """Convert row to estudio evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO.name))
        if id_evento_caso not in evento_mapping:
            return None

        # Solo agregar si hay datos relevantes
        determinacion = self._clean_string(row.get(Columns.DETERMINACION.name))
        tecnica = self._clean_string(row.get(Columns.TECNICA.name))
        fecha = self._safe_date(row.get(Columns.FECHA_ESTUDIO.name))
        resultado = self._clean_string(row.get(Columns.RESULTADO.name))

        if not any([determinacion, tecnica, fecha, resultado]):
            return None

        # EstudioEvento requiere id_muestra (de muestra_evento)
        id_snvs_muestra = self._safe_int(row.get(Columns.ID_SNVS_MUESTRA.name))
        id_evento = evento_mapping[id_evento_caso]

        # Buscar el ID de muestra_evento usando la clave compuesta
        id_muestra_evento = muestra_mapping.get((id_snvs_muestra, id_evento))

        if not id_muestra_evento:
            # No hay muestra asociada, skip este estudio
            return None

        return {
            "id_muestra": id_muestra_evento,
            "fecha_estudio": fecha,
            "determinacion": determinacion,
            "tecnica": tecnica,
            "resultado": resultado,
            "fecha_recepcion": self._safe_date(row.get(Columns.FECHA_RECEPCION.name)),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }
