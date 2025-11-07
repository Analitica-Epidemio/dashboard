"""
Bulk processor para investigaciones epidemiológicas.

OPTIMIZADO: Usa .apply() en lugar de iterrows().
"""

from typing import Dict

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.investigaciones_models import InvestigacionEvento

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult
from . import shared


class InvestigacionesEventosProcessor(BulkProcessorBase):
    """Procesa investigaciones epidemiológicas de eventos."""

    def upsert_investigaciones_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de investigaciones de eventos."""
        start_time = shared.get_current_timestamp()

        # Filtrar registros con al menos un campo de investigación
        investigaciones_df = df[
            df[Columns.INVESTIGACION_TERRENO.name].notna()
            | df[Columns.FECHA_INVESTIGACION.name].notna()
            | df[Columns.TIPO_Y_LUGAR_INVESTIGACION.name].notna()
            | df[Columns.ORIGEN_FINANCIAMIENTO.name].notna()
            | df[Columns.ID_SNVS_EVENTO.name].notna()
            | df[Columns.USER_CENTINELA.name].notna()
            | df[Columns.EVENTO_CENTINELA.name].notna()
        ]

        if investigaciones_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Preparar datos vectorialmente
        investigaciones_data = self._prepare_investigaciones_data(
            investigaciones_df, evento_mapping
        )

        # Bulk insert
        if investigaciones_data:
            stmt = pg_insert(InvestigacionEvento.__table__).values(investigaciones_data)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        duration = (shared.get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(investigaciones_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    # ===== HELPERS INTERNOS =====

    def _prepare_investigaciones_data(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> list:
        """Prepara datos de investigaciones vectorialmente."""
        # Mapear id_evento
        df = df.copy()
        df["id_evento"] = df[Columns.IDEVENTOCASO.name].apply(
            lambda x: evento_mapping.get(shared.safe_int(x))
        )

        # Filtrar solo registros con evento válido
        df = df[df["id_evento"].notna()]

        if df.empty:
            return []

        # Preparar columnas vectorialmente
        timestamp = shared.get_current_timestamp()
        df["origen_fin"] = df[Columns.ORIGEN_FINANCIAMIENTO.name].apply(
            shared.map_origen_financiamiento
        )

        # Construir dicts usando .apply() (más rápido que iterrows)
        investigaciones = df.apply(
            lambda row: self._row_to_investigacion_dict(row, timestamp), axis=1
        ).tolist()

        # Filtrar None values
        investigaciones = [inv for inv in investigaciones if inv is not None]

        return investigaciones

    def _row_to_investigacion_dict(self, row: pd.Series, timestamp) -> dict:
        """Convierte una fila a dict de investigación."""
        inv_dict = {
            "id_evento": int(row["id_evento"]),
            "es_investigacion_terreno": shared.safe_bool(
                row.get(Columns.INVESTIGACION_TERRENO.name)
            ),
            "fecha_investigacion": shared.safe_date(
                row.get(Columns.FECHA_INVESTIGACION.name)
            ),
            "tipo_y_lugar_investigacion": shared.clean_string(
                row.get(Columns.TIPO_Y_LUGAR_INVESTIGACION.name)
            ),
            "origen_financiamiento": row["origen_fin"],
            "id_snvs_evento": shared.safe_int(row.get(Columns.ID_SNVS_EVENTO.name)),
            "es_usuario_centinela": shared.safe_bool(row.get(Columns.USER_CENTINELA.name)),
            "es_evento_centinela": shared.safe_bool(row.get(Columns.EVENTO_CENTINELA.name)),
            "id_usuario_registro": shared.safe_int(row.get(Columns.ID_USER_REGISTRO.name)),
            "participo_usuario_centinela": shared.safe_bool(
                row.get(Columns.USER_CENT_PARTICIPO.name)
            ),
            "id_usuario_centinela_participante": shared.safe_int(
                row.get(Columns.ID_USER_CENT_PARTICIPO.name)
            ),
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Solo retornar si tiene al menos un campo relevante
        if shared.has_any_value(
            [
                inv_dict["es_investigacion_terreno"],
                inv_dict["fecha_investigacion"],
                inv_dict["tipo_y_lugar_investigacion"],
                inv_dict["origen_financiamiento"],
                inv_dict["id_snvs_evento"],
                inv_dict["es_usuario_centinela"],
                inv_dict["es_evento_centinela"],
            ]
        ):
            return inv_dict
        return None
