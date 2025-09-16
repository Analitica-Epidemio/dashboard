"""Bulk processor for health-related data (samples, vaccines, treatments)."""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.establecimientos.models import Establecimiento
from app.domains.eventos.models import Evento
from app.domains.salud.models import Muestra, MuestraEvento, Vacuna, VacunasCiudadano

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class SaludBulkProcessor(BulkProcessorBase):
    """Handles health-related bulk operations."""

    def bulk_upsert_muestras_eventos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de muestras de eventos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de muestra
        muestras_df = df[
            df[Columns.ID_SNVS_MUESTRA].notna()
            | df[Columns.MUESTRA].notna()
            | df[Columns.FECHA_ESTUDIO].notna()
        ]

        if muestras_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(muestras_df)} muestras")

        # Obtener mapping de eventos
        id_eventos_casos = muestras_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        # Crear catálogo de muestras
        muestra_mapping = self._get_or_create_muestras(muestras_df)
        
        # Crear catálogo de establecimientos de muestra 
        establecimiento_mapping = self._get_or_create_establecimientos_muestra(muestras_df)

        muestras_eventos_data = []
        errors = []

        for _, row in muestras_df.iterrows():
            try:
                muestra_evento_dict = self._row_to_muestra_evento_dict(row, evento_mapping, muestra_mapping, establecimiento_mapping)
                if muestra_evento_dict:
                    muestras_eventos_data.append(muestra_evento_dict)
            except Exception as e:
                errors.append(f"Error preparando muestra evento: {e}")

        if muestras_eventos_data:
            stmt = pg_insert(MuestraEvento.__table__).values(muestras_eventos_data)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_snvs_muestra"],
                set_={
                    "fecha_toma_muestra": stmt.excluded.fecha_toma_muestra,
                    "updated_at": self._get_current_timestamp(),
                },
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(muestras_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_vacunas_ciudadanos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de vacunas de ciudadanos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de vacunas
        vacunas_df = df[
            df[Columns.VACUNA].notna()
            | df[Columns.FECHA_APLICACION].notna()
            | df[Columns.DOSIS].notna()
        ]

        if vacunas_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(vacunas_df)} vacunas ciudadanos")

        # Obtener mapping de eventos
        id_eventos_casos = vacunas_df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        # Crear catálogo de vacunas
        vacuna_mapping = self._get_or_create_vacunas(vacunas_df)

        vacunas_ciudadanos_data = []
        errors = []

        for _, row in vacunas_df.iterrows():
            try:
                vacuna_ciudadano_dict = self._row_to_vacuna_ciudadano_dict(row, vacuna_mapping, evento_mapping)
                if vacuna_ciudadano_dict:
                    vacunas_ciudadanos_data.append(vacuna_ciudadano_dict)
            except Exception as e:
                errors.append(f"Error preparando vacuna ciudadano: {e}")

        if vacunas_ciudadanos_data:
            stmt = pg_insert(VacunasCiudadano.__table__).values(vacunas_ciudadanos_data)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(vacunas_ciudadanos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _get_or_create_muestras(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create sample catalog entries."""
        tipos_muestra = df[Columns.MUESTRA].dropna().unique()
        
        muestra_mapping = {}
        for tipo in tipos_muestra:
            tipo_limpio = self._clean_string(tipo)
            if not tipo_limpio:
                continue

            # Buscar existente
            stmt = select(Muestra.id).where(
                Muestra.tipo == tipo_limpio
            ).limit(1)
            muestra_id = self.context.session.execute(stmt).scalar()

            if not muestra_id:
                # Crear nueva
                stmt = pg_insert(Muestra.__table__).values({
                    "tipo": tipo_limpio,
                    "descripcion": tipo_limpio,
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
                self.context.session.execute(stmt.on_conflict_do_nothing())

                # Obtener ID
                stmt = select(Muestra.id).where(
                    Muestra.tipo == tipo_limpio
                ).limit(1)
                muestra_id = self.context.session.execute(stmt).scalar()

            if muestra_id:
                muestra_mapping[tipo_limpio] = muestra_id

        return muestra_mapping

    def _get_or_create_establecimientos_muestra(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create establishment catalog entries for samples."""
        establecimientos = df[Columns.ESTABLECIMIENTO_MUESTRA].dropna().unique()
        
        establecimiento_mapping = {}
        for nombre in establecimientos:
            nombre_limpio = self._clean_string(nombre)
            if not nombre_limpio:
                continue

            # Buscar existente
            stmt = select(Establecimiento.id).where(
                Establecimiento.nombre == nombre_limpio
            ).limit(1)
            est_id = self.context.session.execute(stmt).scalar()

            if not est_id:
                # Crear nuevo
                stmt = pg_insert(Establecimiento.__table__).values({
                    "nombre": nombre_limpio,
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
                self.context.session.execute(stmt.on_conflict_do_nothing())

                # Obtener ID
                stmt = select(Establecimiento.id).where(
                    Establecimiento.nombre == nombre_limpio
                ).limit(1)
                est_id = self.context.session.execute(stmt).scalar()

            if est_id:
                establecimiento_mapping[nombre_limpio] = est_id

        return establecimiento_mapping

    def _get_or_create_vacunas(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create vaccine catalog entries."""
        nombres_vacuna = df[Columns.VACUNA].dropna().unique()
        
        vacuna_mapping = {}
        for nombre in nombres_vacuna:
            nombre_limpio = self._clean_string(nombre)
            if not nombre_limpio:
                continue

            # Buscar existente
            stmt = select(Vacuna.id).where(
                Vacuna.nombre == nombre_limpio
            ).limit(1)
            vacuna_id = self.context.session.execute(stmt).scalar()

            if not vacuna_id:
                # Crear nueva
                stmt = pg_insert(Vacuna.__table__).values({
                    "nombre": nombre_limpio,
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
                self.context.session.execute(stmt.on_conflict_do_nothing())

                # Obtener ID
                stmt = select(Vacuna.id).where(
                    Vacuna.nombre == nombre_limpio
                ).limit(1)
                vacuna_id = self.context.session.execute(stmt).scalar()

            if vacuna_id:
                vacuna_mapping[nombre_limpio] = vacuna_id

        return vacuna_mapping

    def _row_to_muestra_evento_dict(self, row: pd.Series, evento_mapping: Dict[int, int], muestra_mapping: Dict[str, int], establecimiento_mapping: Dict[str, int]) -> Optional[Dict]:
        """Convert row to muestra evento dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        id_snvs_muestra = self._safe_int(row.get(Columns.ID_SNVS_MUESTRA))
        if not id_snvs_muestra:
            return None

        tipo_muestra = self._clean_string(row.get(Columns.MUESTRA))
        id_muestra = muestra_mapping.get(tipo_muestra) if tipo_muestra else None
        
        # Si no hay muestra válida, no crear el registro de MuestraEvento
        if not id_muestra:
            return None

        establecimiento_muestra = self._clean_string(row.get(Columns.ESTABLECIMIENTO_MUESTRA))
        id_establecimiento = establecimiento_mapping.get(establecimiento_muestra) if establecimiento_muestra else None

        # Si no hay establecimiento, usar un establecimiento por defecto
        if not id_establecimiento:
            # Crear/obtener establecimiento "Desconocido"
            if "DESCONOCIDO" not in establecimiento_mapping:
                stmt = pg_insert(Establecimiento.__table__).values({
                    "nombre": "Desconocido",
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
                self.context.session.execute(stmt.on_conflict_do_nothing())
                
                stmt = select(Establecimiento.id).where(
                    Establecimiento.nombre == "Desconocido"
                ).limit(1)
                id_establecimiento = self.context.session.execute(stmt).scalar()
                establecimiento_mapping["DESCONOCIDO"] = id_establecimiento
            else:
                id_establecimiento = establecimiento_mapping["DESCONOCIDO"]

        return {
            "id_snvs_muestra": id_snvs_muestra,
            "id_evento": evento_mapping[id_evento_caso],
            "id_muestra": id_muestra,
            "id_establecimiento": id_establecimiento,
            "fecha_toma_muestra": self._safe_date(row.get(Columns.FECHA_ESTUDIO)),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

    def _row_to_vacuna_ciudadano_dict(self, row: pd.Series, vacuna_mapping: Dict[str, int], evento_mapping: Dict[int, int]) -> Optional[Dict]:
        """Convert row to vacuna ciudadano dict."""
        codigo_ciudadano = self._safe_int(row.get(Columns.CODIGO_CIUDADANO))
        if not codigo_ciudadano:
            return None

        nombre_vacuna = self._clean_string(row.get(Columns.VACUNA))
        if not nombre_vacuna or nombre_vacuna not in vacuna_mapping:
            return None

        # Obtener el evento asociado
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        id_evento = evento_mapping.get(id_evento_caso) if id_evento_caso else None

        return {
            "codigo_ciudadano": codigo_ciudadano,
            "id_vacuna": vacuna_mapping[nombre_vacuna],
            "id_evento": id_evento,
            "fecha_aplicacion": self._safe_date(row.get(Columns.FECHA_APLICACION)),
            "dosis": self._clean_string(row.get(Columns.DOSIS)),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }