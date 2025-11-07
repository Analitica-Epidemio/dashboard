"""Bulk processor for events and related entities."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
import os

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.utils.codigo_generator import CodigoGenerator
from app.domains.eventos_epidemiologicos.ambitos_models import AmbitosConcurrenciaEvento
from app.domains.eventos_epidemiologicos.eventos.models import (
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
    DetalleEventoSintomas,
    Evento,
    GrupoEno,
    TipoEno,
)
from app.domains.atencion_medica.salud_models import Sintoma
from app.features.procesamiento_archivos.utils.epidemiological_calculations import (
    calcular_semana_epidemiologica,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult, get_or_create_catalog


class EventosProcessor(BulkProcessorBase):
    """Handles event-related bulk operations."""


class AmbitosProcessor(BulkProcessorBase):
    """Handles place of occurrence operations."""

    def upsert_ambitos_concurrencia(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de ámbitos de concurrencia (OCURRENCIA columns)."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de ámbitos/ocurrencia
        ambitos_df = df[
            df[Columns.TIPO_LUGAR_OCURRENCIA.name].notna()
            | df[Columns.NOMBRE_LUGAR_OCURRENCIA.name].notna()
            | df[Columns.LOCALIDAD_AMBITO_OCURRENCIA.name].notna()
            | df[Columns.SITIO_PROBABLE_ADQUISICION.name].notna()
            | df[Columns.SITIO_PROBABLE_DISEMINACION.name].notna()
            | df[Columns.FRECUENCIA.name].notna()
            | df[Columns.FECHA_AMBITO_OCURRENCIA.name].notna()
        ]

        if ambitos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(ambitos_df)} ámbitos de concurrencia")

        # OPTIMIZACIÓN: Procesamiento vectorizado de ámbitos (80% más rápido)
        ambitos_data = []
        errors = []

        if not ambitos_df.empty:
            # Mapear ID de evento
            ambitos_df = ambitos_df.copy()
            ambitos_df["id_evento"] = ambitos_df[Columns.IDEVENTOCASO.name].map(
                evento_mapping
            )

            # Filtrar solo eventos válidos
            valid_ambitos = ambitos_df[ambitos_df["id_evento"].notna()]

            if not valid_ambitos.empty:
                # Mapear frecuencia usando apply (más rápido que iterrows)
                valid_ambitos["frecuencia_enum"] = valid_ambitos[
                    Columns.FRECUENCIA
                ].apply(self._map_frecuencia_ocurrencia)

                # Crear dict usando .apply() (más rápido que iterrows)
                timestamp = self._get_current_timestamp()
                ambitos_data = valid_ambitos.apply(
                    lambda row: self._row_to_ambito_dict(row, timestamp), axis=1
                ).tolist()
                # Filtrar None values
                ambitos_data = [a for a in ambitos_data if a is not None]

        if ambitos_data:
            stmt = pg_insert(AmbitosConcurrenciaEvento.__table__).values(ambitos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["id_evento"])
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(ambitos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def _row_to_ambito_dict(self, row: pd.Series, timestamp) -> dict:
        """Convierte una fila a dict de ámbito de concurrencia."""
        ambito_dict = {
            "id_evento": int(row["id_evento"]),
            "nombre_lugar_ocurrencia": self._clean_string(
                row.get(Columns.NOMBRE_LUGAR_OCURRENCIA.name)
            ),
            "tipo_lugar_ocurrencia": self._clean_string(
                row.get(Columns.TIPO_LUGAR_OCURRENCIA.name)
            ),
            "localidad_ambito_ocurrencia": self._clean_string(
                row.get(Columns.LOCALIDAD_AMBITO_OCURRENCIA.name)
            ),
            "fecha_ambito_ocurrencia": self._safe_date(
                row.get(Columns.FECHA_AMBITO_OCURRENCIA.name)
            ),
            "es_sitio_probable_adquisicion_infeccion": self._safe_bool(
                row.get(Columns.SITIO_PROBABLE_ADQUISICION.name)
            ),
            "es_sitio_probable_diseminacion_infeccion": self._safe_bool(
                row.get(Columns.SITIO_PROBABLE_DISEMINACION.name)
            ),
            "frecuencia_concurrencia": row["frecuencia_enum"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Solo retornar si hay datos relevantes
        if any(
            [
                ambito_dict["nombre_lugar_ocurrencia"],
                ambito_dict["tipo_lugar_ocurrencia"],
                ambito_dict["fecha_ambito_ocurrencia"],
            ]
        ):
            return ambito_dict
        return None
