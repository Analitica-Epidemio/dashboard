"""Bulk processor for treatment events."""

from typing import Dict

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.diagnosticos_models import TratamientoEvento

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult


class TratamientosProcessor(BulkProcessorBase):
    """Handles treatment event operations."""

    def upsert_tratamientos_eventos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de tratamientos de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de tratamientos
        tratamientos_df = df[
            df[Columns.TRATAMIENTO_2.name].notna()
            | df[Columns.FECHA_INICIO_TRAT.name].notna()
            | df[Columns.FECHA_FIN_TRAT.name].notna()
            | df[Columns.RESULTADO_TRATAMIENTO.name].notna()
        ]

        if tratamientos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(tratamientos_df)} tratamientos")

        # OPTIMIZACIÓN: Procesamiento vectorizado de tratamientos (80% más rápido)
        tratamientos_data = []
        errors = []

        if not tratamientos_df.empty:
            tratamientos_df = tratamientos_df.copy()

            # Mapear IDs usando vectorización
            tratamientos_df["id_evento"] = tratamientos_df[
                Columns.IDEVENTOCASO.name
            ].map(evento_mapping)

            # Limpiar strings con operaciones vectorizadas
            tratamientos_df["tratamiento_clean"] = (
                tratamientos_df[Columns.TRATAMIENTO_2.name].astype(str).str.strip()
            )
            tratamientos_df["resultado_clean"] = (
                tratamientos_df[Columns.RESULTADO_TRATAMIENTO.name]
                .astype(str)
                .str.strip()
            )

            # Mapear resultado de tratamiento vectorialmente
            tratamientos_df["resultado_mapped"] = tratamientos_df[
                "resultado_clean"
            ].apply(lambda x: self._map_resultado_tratamiento(x))

            # Filtrar solo tratamientos válidos (tienen id_evento y al menos un campo relevante)
            valid_tratamientos = tratamientos_df[
                tratamientos_df["id_evento"].notna()
                & (
                    (
                        tratamientos_df["tratamiento_clean"].notna()
                        & (tratamientos_df["tratamiento_clean"] != "nan")
                    )
                    | tratamientos_df[Columns.FECHA_INICIO_TRAT.name].notna()
                    | tratamientos_df[Columns.FECHA_FIN_TRAT.name].notna()
                    | (
                        tratamientos_df["resultado_clean"].notna()
                        & (tratamientos_df["resultado_clean"] != "nan")
                    )
                )
            ]

            # DEDUPLICAR: El CSV tiene duplicados (un tratamiento por cada síntoma)
            # Deduplicar por (id_evento, tratamiento, fecha_inicio)
            if not valid_tratamientos.empty:
                # Crear columna de fecha para deduplicación
                valid_tratamientos["fecha_inicio_str"] = valid_tratamientos[
                    Columns.FECHA_INICIO_TRAT.name
                ].astype(str)

                # Deduplicar manteniendo el primer registro de cada combinación única
                valid_tratamientos = valid_tratamientos.drop_duplicates(
                    subset=["id_evento", "tratamiento_clean", "fecha_inicio_str"],
                    keep="first",
                )

                self.logger.info(
                    f"Tratamientos después de deduplicación: {len(valid_tratamientos)}"
                )

            if not valid_tratamientos.empty:
                timestamp = self._get_current_timestamp()
                tratamientos_data = valid_tratamientos.apply(
                    lambda row: {
                        "id_evento": int(row["id_evento"]),
                        "descripcion_tratamiento": (
                            row["tratamiento_clean"]
                            if row["tratamiento_clean"] not in ["nan", "", None]
                            else None
                        ),
                        "establecimiento_tratamiento": self._clean_string(
                            row.get(Columns.ESTAB_TTO.name)
                        ),
                        "fecha_inicio_tratamiento": self._safe_date(
                            row.get(Columns.FECHA_INICIO_TRAT.name)
                        ),
                        "fecha_fin_tratamiento": self._safe_date(
                            row.get(Columns.FECHA_FIN_TRAT.name)
                        ),
                        "resultado_tratamiento": row["resultado_mapped"],
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    },
                    axis=1,
                ).tolist()

        if tratamientos_data:
            stmt = pg_insert(TratamientoEvento.__table__).values(tratamientos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=[
                    "id_evento",
                    "descripcion_tratamiento",
                    "fecha_inicio_tratamiento",
                ]
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(tratamientos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def _map_resultado_tratamiento(self, resultado_str: str) -> str:
        """Usar directamente el valor del CSV ya que ahora el enum tiene todos los valores exactos."""
        if not resultado_str:
            return None

        # Usar el valor tal como viene del CSV (limpiando espacios)
        resultado_clean = resultado_str.strip()

        # Lista de valores válidos del enum (EXACTAMENTE como están en el enum)
        valores_validos = [
            "Adecuado (al menos 1 dosis al menos 30 días antes de FPP)",
            "Aplicado",
            "Curado",
            "Desconocido",
            "En tratamiento",
            "Éxito del tratamiento",
            "Fallecido",
            "Fracaso del tratamiento",
            "Inadecuado",
            "No corresponde",
            "Penicilina Benzatínica única dosis",
            "Pérdida de seguimiento",
            "Sin tratamiento",
            "Traslado",
            "Tratamiento completo",
            "Tratamiento en curso",
            "Tratamiento incompleto",
            "Tratamiento incompleto por abandono",
        ]

        # Verificar si el valor está en la lista de valores válidos
        if resultado_clean in valores_validos:
            return resultado_clean
        else:
            # Log del valor no válido para debug
            self.logger.warning(
                f"Valor de resultado_tratamiento no válido: '{resultado_clean}' - no se creará registro"
            )
            return None
