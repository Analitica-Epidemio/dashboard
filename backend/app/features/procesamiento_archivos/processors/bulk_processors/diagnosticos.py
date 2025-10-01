"""Bulk processor for diagnostic-related data (diagnosis, studies, treatments, hospitalizations)."""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.diagnosticos_models import (
    DiagnosticoEvento,
    EstudioEvento,
    InternacionEvento,
    TratamientoEvento,
)
from app.domains.eventos_epidemiologicos.eventos.models import Evento

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class DiagnosticosBulkProcessor(BulkProcessorBase):
    """Handles diagnostic-related bulk operations."""

    def bulk_upsert_diagnosticos_eventos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de diagnósticos de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de diagnóstico
        diagnosticos_df = df[
            df[Columns.CLASIFICACION_MANUAL].notna()
            | df[Columns.CLASIFICACION_AUTOMATICA].notna()
            | df[Columns.DIAG_REFERIDO].notna()
        ]

        if diagnosticos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(diagnosticos_df)} diagnósticos")

        # Obtener mapping de eventos
        id_eventos_casos = diagnosticos_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        diagnosticos_data = []
        errors = []

        for _, row in diagnosticos_df.iterrows():
            try:
                diagnostico_dict = self._row_to_diagnostico_dict(row, evento_mapping)
                if diagnostico_dict:
                    diagnosticos_data.append(diagnostico_dict)
            except Exception as e:
                errors.append(f"Error preparando diagnóstico evento: {e}")

        if diagnosticos_data:
            stmt = pg_insert(DiagnosticoEvento.__table__).values(diagnosticos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=['id_evento']
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(diagnosticos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_estudios_eventos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de estudios de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de estudios
        estudios_df = df[
            df[Columns.DETERMINACION].notna()
            | df[Columns.TECNICA].notna()
            | df[Columns.RESULTADO].notna()
            | df[Columns.FECHA_ESTUDIO].notna()
        ]

        if estudios_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(estudios_df)} estudios")

        # Obtener mapping de eventos
        id_eventos_casos = estudios_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        estudios_data = []
        errors = []

        for _, row in estudios_df.iterrows():
            try:
                estudio_dict = self._row_to_estudio_dict(row, evento_mapping)
                if estudio_dict:
                    estudios_data.append(estudio_dict)
            except Exception as e:
                errors.append(f"Error preparando estudio evento: {e}")

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

    def bulk_upsert_tratamientos_eventos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de tratamientos de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de tratamientos
        tratamientos_df = df[
            df[Columns.TRATAMIENTO_2].notna()
            | df[Columns.FECHA_INICIO_TRAT].notna()
            | df[Columns.FECHA_FIN_TRAT].notna()
            | df[Columns.RESULTADO_TRATAMIENTO].notna()
        ]

        if tratamientos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(tratamientos_df)} tratamientos")

        # Obtener mapping de eventos
        id_eventos_casos = tratamientos_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        tratamientos_data = []
        errors = []

        for _, row in tratamientos_df.iterrows():
            try:
                tratamiento_dict = self._row_to_tratamiento_dict(row, evento_mapping)
                if tratamiento_dict:
                    tratamientos_data.append(tratamiento_dict)
            except Exception as e:
                errors.append(f"Error preparando tratamiento evento: {e}")

        if tratamientos_data:
            stmt = pg_insert(TratamientoEvento.__table__).values(tratamientos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=['id_evento', 'descripcion_tratamiento', 'fecha_inicio_tratamiento']
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

    def bulk_upsert_internaciones_eventos(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de internaciones de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de internaciones
        internaciones_df = df[
            df[Columns.FECHA_INTERNACION].notna()
            | df[Columns.FECHA_ALTA_MEDICA].notna()
            | df[Columns.CUIDADO_INTENSIVO].notna()
            | df[Columns.FECHA_CUI_INTENSIVOS].notna()
        ]

        if internaciones_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(internaciones_df)} internaciones")

        # Obtener mapping de eventos
        id_eventos_casos = internaciones_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        internaciones_data = []
        errors = []

        for _, row in internaciones_df.iterrows():
            try:
                internacion_dict = self._row_to_internacion_dict(row, evento_mapping)
                if internacion_dict:
                    internaciones_data.append(internacion_dict)
            except Exception as e:
                errors.append(f"Error preparando internación evento: {e}")

        if internaciones_data:
            stmt = pg_insert(InternacionEvento.__table__).values(internaciones_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=['id_evento']
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(internaciones_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _row_to_diagnostico_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to diagnostico evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Solo agregar si hay datos relevantes
        clasificacion_manual = self._clean_string(row.get(Columns.CLASIFICACION_MANUAL))
        clasificacion_auto = self._clean_string(
            row.get(Columns.CLASIFICACION_AUTOMATICA)
        )
        diag_referido = self._clean_string(row.get(Columns.DIAG_REFERIDO))

        if not any([clasificacion_manual, clasificacion_auto, diag_referido]):
            return None

        return {
            "id_evento": evento_mapping[id_evento_caso],
            "clasificacion_manual": self._clean_string(
                row.get(Columns.CLASIFICACION_MANUAL)
            )
            or "Sin clasificar",
            "clasificacion_automatica": self._clean_string(
                row.get(Columns.CLASIFICACION_AUTOMATICA)
            ),
            "clasificacion_algoritmo": self._clean_string(
                row.get(Columns.CLASIFICACION_ALGORITMO)
            ),
            "validacion": self._clean_string(row.get(Columns.VALIDACION)),
            "diagnostico_referido": self._clean_string(row.get(Columns.DIAG_REFERIDO)),
            "fecha_diagnostico_referido": self._safe_date(
                row.get(Columns.FECHA_DIAG_REFERIDO)
            ),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

    def _row_to_estudio_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to estudio evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Solo agregar si hay datos relevantes
        determinacion = self._clean_string(row.get(Columns.DETERMINACION))
        tecnica = self._clean_string(row.get(Columns.TECNICA))
        fecha = self._safe_date(row.get(Columns.FECHA_ESTUDIO))
        resultado = self._clean_string(row.get(Columns.RESULTADO))

        if not any([determinacion, tecnica, fecha, resultado]):
            return None

        # EstudioEvento requiere id_muestra, no id_evento
        # Necesitaríamos el mapping de muestras para esto
        # Por ahora skip este método hasta tener el mapping correcto
        return None

    def _row_to_tratamiento_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to tratamiento evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Solo agregar si hay datos relevantes
        tratamiento = self._clean_string(row.get(Columns.TRATAMIENTO_2))
        fecha_inicio = self._safe_date(row.get(Columns.FECHA_INICIO_TRAT))
        fecha_fin = self._safe_date(row.get(Columns.FECHA_FIN_TRAT))
        resultado = self._clean_string(row.get(Columns.RESULTADO_TRATAMIENTO))

        if not any([tratamiento, fecha_inicio, fecha_fin, resultado]):
            return None

        return {
            "id_evento": evento_mapping[id_evento_caso],
            "descripcion_tratamiento": tratamiento,
            "establecimiento_tratamiento": self._clean_string(
                row.get(Columns.ESTAB_TTO)
            ),
            "fecha_inicio_tratamiento": fecha_inicio,
            "fecha_fin_tratamiento": fecha_fin,
            "resultado_tratamiento": self._map_resultado_tratamiento(resultado),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

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

    def _row_to_internacion_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to internacion evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Solo agregar si hay datos relevantes
        fecha_internacion = self._safe_date(row.get(Columns.FECHA_INTERNACION))
        fecha_alta = self._safe_date(row.get(Columns.FECHA_ALTA_MEDICA))
        cuidado_intensivo = self._safe_bool(row.get(Columns.CUIDADO_INTENSIVO))
        fecha_uci = self._safe_date(row.get(Columns.FECHA_CUI_INTENSIVOS))

        if not any([fecha_internacion, fecha_alta, cuidado_intensivo, fecha_uci]):
            return None

        return {
            "id_evento": evento_mapping[id_evento_caso],
            "fue_internado": self._safe_bool(row.get(Columns.INTERNADO)),
            "fue_curado": self._safe_bool(row.get(Columns.CURADO)),
            "fecha_internacion": fecha_internacion,
            "fecha_alta_medica": fecha_alta,
            "requirio_cuidado_intensivo": cuidado_intensivo,
            "fecha_cuidados_intensivos": fecha_uci,
            "establecimiento_internacion": self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_INTERNACION)
            ),
            "es_fallecido": self._safe_bool(row.get(Columns.FALLECIDO)),
            "fecha_fallecimiento": self._safe_date(
                row.get(Columns.FECHA_FALLECIMIENTO)
            ),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }
