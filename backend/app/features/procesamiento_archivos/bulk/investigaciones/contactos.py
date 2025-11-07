"""
Bulk processor para contactos y notificaciones epidemiológicas.

OPTIMIZADO: Usa .apply() en lugar de iterrows().
"""

from typing import Dict

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.investigaciones_models import ContactosNotificacion
from app.domains.eventos_epidemiologicos.eventos.models import Evento

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult
from . import shared


class ContactosProcessor(BulkProcessorBase):
    """Procesa contactos y notificaciones de casos epidemiológicos."""

    def upsert_contactos_notificaciones(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de contactos y notificaciones."""
        start_time = shared.get_current_timestamp()

        # Filtrar registros con al menos un campo de contacto
        contactos_df = df[
            df[Columns.CONTACTO_CON_CONFIR.name].notna()
            | df[Columns.CONTACTO_CON_SOSPECHOSO.name].notna()
            | df[Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name].notna()
            | df[Columns.CONTACTOS_MENORES_1.name].notna()
            | df[Columns.CONTACTOS_VACUNADOS.name].notna()
            | df[Columns.CONTACTO_EMBARAZADAS.name].notna()
        ]

        if contactos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Obtener mapeo de eventos
        evento_mapping = self._get_evento_mapping(contactos_df)

        # Preparar datos vectorialmente
        contactos_data = self._prepare_contactos_data(contactos_df, evento_mapping)

        # Bulk insert
        if contactos_data:
            stmt = pg_insert(ContactosNotificacion.__table__).values(contactos_data)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        duration = (shared.get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(contactos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    # ===== HELPERS INTERNOS =====

    def _get_evento_mapping(self, df: pd.DataFrame) -> Dict[int, int]:
        """Obtiene mapeo: id_evento_caso → evento.id"""
        from sqlalchemy import select

        id_eventos_casos = df[Columns.IDEVENTOCASO.name].dropna().unique().tolist()

        if not id_eventos_casos:
            return {}

        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )

        return {
            row.id_evento_caso: row.id for row in self.context.session.execute(stmt)
        }

    def _prepare_contactos_data(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> list:
        """Prepara datos de contactos vectorialmente."""
        # Mapear id_evento
        df = df.copy()
        df["id_evento"] = df[Columns.IDEVENTOCASO.name].apply(
            lambda x: evento_mapping.get(shared.safe_int(x))
        )

        # Filtrar solo registros con evento válido
        df = df[df["id_evento"].notna()]

        if df.empty:
            return []

        # Construir dicts usando .apply() (más rápido que iterrows)
        timestamp = shared.get_current_timestamp()

        contactos = df.apply(
            lambda row: self._row_to_contacto_dict(row, timestamp), axis=1
        ).tolist()

        # Filtrar None values
        contactos = [c for c in contactos if c is not None]

        return contactos

    def _row_to_contacto_dict(self, row: pd.Series, timestamp) -> dict:
        """Convierte una fila a dict de contacto."""
        contacto_dict = {
            "id_evento": int(row["id_evento"]),
            "hubo_contacto_con_caso_confirmado": shared.safe_bool(
                row.get(Columns.CONTACTO_CON_CONFIR.name)
            ),
            "hubo_contacto_con_caso_sospechoso": shared.safe_bool(
                row.get(Columns.CONTACTO_CON_SOSPECHOSO.name)
            ),
            "contactos_relevados_contactos_detectados": shared.clean_string(
                row.get(Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name)
            ),
            "cantidad_contactos_menores_un_anio": shared.safe_int(
                row.get(Columns.CONTACTOS_MENORES_1.name)
            ),
            "cantidad_contactos_vacunados": shared.safe_int(
                row.get(Columns.CONTACTOS_VACUNADOS.name)
            ),
            "cantidad_contactos_embarazadas": shared.safe_int(
                row.get(Columns.CONTACTO_EMBARAZADAS.name)
            ),
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Solo retornar si tiene al menos un campo relevante
        if shared.has_any_value(
            [
                contacto_dict["hubo_contacto_con_caso_confirmado"],
                contacto_dict["hubo_contacto_con_caso_sospechoso"],
                contacto_dict["contactos_relevados_contactos_detectados"],
                contacto_dict["cantidad_contactos_menores_un_anio"],
                contacto_dict["cantidad_contactos_vacunados"],
                contacto_dict["cantidad_contactos_embarazadas"],
            ]
        ):
            return contacto_dict
        return None
