"""Bulk processor for investigation-related data (investigations, contacts)."""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.eventos_epidemiologicos.eventos.models import Evento
from app.domains.investigaciones.models import (
    ContactosNotificacion,
    InvestigacionEvento,
)

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class InvestigacionesBulkProcessor(BulkProcessorBase):
    """Handles investigation-related bulk operations."""

    def bulk_upsert_investigaciones_eventos(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de investigaciones de eventos (INVESTIGACION fields)."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de investigación
        investigaciones_df = df[
            df[Columns.INVESTIGACION_TERRENO].notna()
            | df[Columns.FECHA_INVESTIGACION].notna()
            | df[Columns.TIPO_Y_LUGAR_INVESTIGACION].notna()
            | df[Columns.ORIGEN_FINANCIAMIENTO].notna()
            | df[Columns.ID_SNVS_EVENTO].notna()
            | df[Columns.USER_CENTINELA].notna()
            | df[Columns.EVENTO_CENTINELA].notna()
        ]

        if investigaciones_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(investigaciones_df)} investigaciones")

        # Obtener mapping de eventos
        id_eventos_casos = investigaciones_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        investigaciones_data = []
        errors = []

        for _, row in investigaciones_df.iterrows():
            try:
                investigacion_dict = self._row_to_investigacion_dict(
                    row, evento_mapping
                )
                if investigacion_dict:
                    investigaciones_data.append(investigacion_dict)
            except Exception as e:
                errors.append(f"Error preparando investigación evento: {e}")

        if investigaciones_data:
            stmt = pg_insert(InvestigacionEvento.__table__).values(investigaciones_data)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(investigaciones_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_contactos_notificaciones(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de contactos y notificaciones (CONTACTOS fields)."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de contactos
        contactos_df = df[
            df[Columns.CONTACTO_CON_CONFIR].notna()
            | df[Columns.CONTACTO_CON_SOSPECHOSO].notna()
            | df[Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS].notna()
            | df[Columns.CONTACTOS_MENORES_1].notna()
            | df[Columns.CONTACTOS_VACUNADOS].notna()
            | df[Columns.CONTACTO_EMBARAZADAS].notna()
        ]

        if contactos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(contactos_df)} contactos")

        # Obtener mapping de eventos
        id_eventos_casos = contactos_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        contactos_data = []
        errors = []

        for _, row in contactos_df.iterrows():
            try:
                contacto_dict = self._row_to_contacto_dict(row, evento_mapping)
                if contacto_dict:
                    contactos_data.append(contacto_dict)
            except Exception as e:
                errors.append(f"Error preparando contactos evento: {e}")

        if contactos_data:
            stmt = pg_insert(ContactosNotificacion.__table__).values(contactos_data)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(contactos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _row_to_investigacion_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to investigacion evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Mapear origen de financiamiento a enum
        origen_financiamiento = self._map_origen_financiamiento(
            row.get(Columns.ORIGEN_FINANCIAMIENTO)
        )

        investigacion_dict = {
            "id_evento": evento_mapping[id_evento_caso],
            "es_investigacion_terreno": self._safe_bool(
                row.get(Columns.INVESTIGACION_TERRENO)
            ),
            "fecha_investigacion": self._safe_date(
                row.get(Columns.FECHA_INVESTIGACION)
            ),
            "tipo_y_lugar_investigacion": self._clean_string(
                row.get(Columns.TIPO_Y_LUGAR_INVESTIGACION)
            ),
            "origen_financiamiento": origen_financiamiento,
            "id_snvs_evento": self._safe_int(row.get(Columns.ID_SNVS_EVENTO)),
            "es_usuario_centinela": self._safe_bool(row.get(Columns.USER_CENTINELA)),
            "es_evento_centinela": self._safe_bool(row.get(Columns.EVENTO_CENTINELA)),
            "id_usuario_registro": self._safe_int(row.get(Columns.ID_USER_REGISTRO)),
            "participo_usuario_centinela": self._safe_bool(
                row.get(Columns.USER_CENT_PARTICIPO)
            ),
            "id_usuario_centinela_participante": self._safe_int(
                row.get(Columns.ID_USER_CENT_PARTICIPO)
            ),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

        # Solo agregar si hay datos relevantes
        if any(
            [
                investigacion_dict["es_investigacion_terreno"],
                investigacion_dict["fecha_investigacion"],
                investigacion_dict["tipo_y_lugar_investigacion"],
                investigacion_dict["origen_financiamiento"],
                investigacion_dict["id_snvs_evento"],
                investigacion_dict["es_usuario_centinela"],
                investigacion_dict["es_evento_centinela"],
            ]
        ):
            return investigacion_dict
        return None

    def _row_to_contacto_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to contacto notificacion dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        contacto_dict = {
            "id_evento": evento_mapping[id_evento_caso],
            "hubo_contacto_con_caso_confirmado": self._safe_bool(
                row.get(Columns.CONTACTO_CON_CONFIR)
            ),
            "hubo_contacto_con_caso_sospechoso": self._safe_bool(
                row.get(Columns.CONTACTO_CON_SOSPECHOSO)
            ),
            "contactos_relevados_contactos_detectados": self._clean_string(
                row.get(Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS)
            ),
            "cantidad_contactos_menores_un_anio": self._safe_int(
                row.get(Columns.CONTACTOS_MENORES_1)
            ),
            "cantidad_contactos_vacunados": self._safe_int(
                row.get(Columns.CONTACTOS_VACUNADOS)
            ),
            "cantidad_contactos_embarazadas": self._safe_int(
                row.get(Columns.CONTACTO_EMBARAZADAS)
            ),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

        # Solo agregar si hay datos relevantes
        if any(
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
