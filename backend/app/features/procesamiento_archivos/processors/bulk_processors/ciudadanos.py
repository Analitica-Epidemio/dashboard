"""Bulk processor for citizens and related data."""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.ciudadanos.models import (
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
    ViajesCiudadano,
)
from app.domains.salud.models import Comorbilidad

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class CiudadanosBulkProcessor(BulkProcessorBase):
    """Handles all citizen-related bulk operations."""

    def bulk_upsert_ciudadanos(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de ciudadanos usando PostgreSQL ON CONFLICT."""
        start_time = self._get_current_timestamp()

        # Filtrar registros únicos
        ciudadanos_df = df.dropna(subset=[Columns.CODIGO_CIUDADANO]).drop_duplicates(
            subset=[Columns.CODIGO_CIUDADANO]
        )

        if ciudadanos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(ciudadanos_df)} ciudadanos")

        # Preparar datos usando el modelo real
        ciudadanos_data = []
        errors = []

        for _, row in ciudadanos_df.iterrows():
            try:
                ciudadano_dict = self._row_to_ciudadano_dict(row)
                if ciudadano_dict:
                    ciudadanos_data.append(ciudadano_dict)
            except Exception as e:
                errors.append(
                    f"Error preparando ciudadano {row.get(Columns.CODIGO_CIUDADANO)}: {e}"
                )

        if not ciudadanos_data:
            return BulkOperationResult(0, 0, len(errors), errors, 0.0)

        # PostgreSQL UPSERT usando SQLAlchemy 2.0
        stmt = pg_insert(Ciudadano.__table__).values(ciudadanos_data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["codigo_ciudadano"],
            set_={
                "nombre": stmt.excluded.nombre,
                "apellido": stmt.excluded.apellido,
                "tipo_documento": stmt.excluded.tipo_documento,
                "numero_documento": stmt.excluded.numero_documento,
                "fecha_nacimiento": stmt.excluded.fecha_nacimiento,
                "sexo_biologico_al_nacer": stmt.excluded.sexo_biologico_al_nacer,
                "sexo_biologico": stmt.excluded.sexo_biologico,
                "genero_autopercibido": stmt.excluded.genero_autopercibido,
                "etnia": stmt.excluded.etnia,
                "updated_at": self._get_current_timestamp(),
            },
        )

        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(ciudadanos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_ciudadanos_domicilios(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de domicilios de ciudadanos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con datos de domicilio Y localidad válida (requerida)
        domicilios_df = df.dropna(subset=[Columns.CODIGO_CIUDADANO, Columns.ID_LOC_INDEC_RESIDENCIA])
        domicilios_df = domicilios_df[
            (domicilios_df[Columns.CALLE_DOMICILIO].notna()
            | domicilios_df[Columns.NUMERO_DOMICILIO].notna()
            | domicilios_df[Columns.BARRIO_POPULAR].notna())
        ]

        if domicilios_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(domicilios_df)} domicilios")

        domicilios_data = []
        errors = []

        for _, row in domicilios_df.iterrows():
            try:
                domicilio_dict = self._row_to_domicilio_dict(row)
                if domicilio_dict:
                    domicilios_data.append(domicilio_dict)
            except Exception as e:
                errors.append(
                    f"Error preparando domicilio para {row.get(Columns.CODIGO_CIUDADANO)}: {e}"
                )

        if not domicilios_data:
            return BulkOperationResult(0, 0, len(errors), errors, 0.0)

        # UPSERT usando el modelo real - usar DO NOTHING ya que no hay constraint único
        stmt = pg_insert(CiudadanoDomicilio.__table__).values(domicilios_data)
        upsert_stmt = stmt.on_conflict_do_nothing()
        
        try:
            self.context.session.execute(upsert_stmt)
        except Exception as insert_error:
            self.logger.error(f"Failed to insert domicilios: {insert_error}")
            # Log first few rows for debugging
            self.logger.error(
                f"Sample data: {domicilios_data[:3] if domicilios_data else 'No data'}"
            )
            raise insert_error

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(domicilios_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_ciudadanos_datos(
        self, df: pd.DataFrame, evento_mapping: Dict[int, int]
    ) -> BulkOperationResult:
        """Bulk upsert de CiudadanoDatos con foreign key a Evento."""
        start_time = self._get_current_timestamp()

        datos_df = df.dropna(subset=[Columns.CODIGO_CIUDADANO, Columns.IDEVENTOCASO])

        if datos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(datos_df)} ciudadanos datos")

        datos_data = []
        errors = []

        for _, row in datos_df.iterrows():
            try:
                datos_dict = self._row_to_datos_dict(row, evento_mapping)
                if datos_dict:
                    datos_data.append(datos_dict)
            except Exception as e:
                errors.append(f"Error preparando datos ciudadano: {e}")

        if not datos_data:
            return BulkOperationResult(0, 0, len(errors), errors, 0.0)

        # Bulk insert usando el modelo real
        stmt = pg_insert(CiudadanoDatos.__table__).values(datos_data)
        upsert_stmt = stmt.on_conflict_do_nothing()
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(datos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_viajes(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de viajes de ciudadanos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de viaje
        viajes_df = df[
            df[Columns.ID_SNVS_VIAJE_EPIDEMIO].notna()
            | df[Columns.FECHA_INICIO_VIAJE].notna()
            | df[Columns.PAIS_VIAJE].notna()
            | df[Columns.LOC_VIAJE].notna()
        ]

        if viajes_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(viajes_df)} viajes")

        # Obtener ciudadanos existentes
        codigos_ciudadanos = (
            viajes_df[Columns.CODIGO_CIUDADANO].dropna().unique().tolist()
        )

        stmt = select(Ciudadano.codigo_ciudadano).where(
            Ciudadano.codigo_ciudadano.in_(codigos_ciudadanos)
        )
        ciudadanos_existentes = set(
            codigo for (codigo,) in self.context.session.execute(stmt).all()
        )

        viajes_data = []
        errors = []
        viajes_seen = set()  # Para deduplicar por id_snvs

        for _, row in viajes_df.iterrows():
            try:
                viaje_dict = self._row_to_viaje_dict(row, ciudadanos_existentes)
                if viaje_dict:
                    # Deduplicar por id_snvs_viaje_epidemiologico
                    viaje_key = viaje_dict["id_snvs_viaje_epidemiologico"]
                    
                    if viaje_key not in viajes_seen:
                        viajes_data.append(viaje_dict)
                        viajes_seen.add(viaje_key)
            except Exception as e:
                errors.append(f"Error preparando viaje: {e}")

        if viajes_data:
            stmt = pg_insert(ViajesCiudadano.__table__).values(viajes_data)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_snvs_viaje_epidemiologico"],
                set_={
                    "fecha_inicio_viaje": stmt.excluded.fecha_inicio_viaje,
                    "fecha_finalizacion_viaje": stmt.excluded.fecha_finalizacion_viaje,
                    "id_localidad_destino_viaje": stmt.excluded.id_localidad_destino_viaje,
                    "updated_at": self._get_current_timestamp(),
                },
            )
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(viajes_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_comorbilidades(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de comorbilidades de ciudadanos."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con comorbilidades
        comorbilidades_df = df[df[Columns.COMORBILIDAD].notna()]

        if comorbilidades_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(comorbilidades_df)} comorbilidades")

        # Crear mapping de comorbilidades
        comorbilidad_mapping = self._get_or_create_comorbilidades(comorbilidades_df)

        # Obtener ciudadanos existentes
        codigos_ciudadanos = (
            comorbilidades_df[Columns.CODIGO_CIUDADANO].dropna().unique().tolist()
        )

        stmt = select(Ciudadano.codigo_ciudadano).where(
            Ciudadano.codigo_ciudadano.in_(codigos_ciudadanos)
        )
        ciudadanos_existentes = set(
            codigo for (codigo,) in self.context.session.execute(stmt).all()
        )

        # Crear relaciones
        comorbilidades_ciudadano_data = []
        errors = []

        for _, row in comorbilidades_df.iterrows():
            try:
                relacion_dict = self._row_to_comorbilidad_dict(
                    row, ciudadanos_existentes, comorbilidad_mapping
                )
                if relacion_dict:
                    comorbilidades_ciudadano_data.append(relacion_dict)
            except Exception as e:
                errors.append(f"Error preparando comorbilidad: {e}")

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
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _row_to_ciudadano_dict(self, row: pd.Series) -> Optional[Dict]:
        """Convert row to ciudadano dict."""
        try:
            return {
                "codigo_ciudadano": self._safe_int(row.get(Columns.CODIGO_CIUDADANO)),
                "nombre": self._clean_string(row.get(Columns.NOMBRE)),
                "apellido": self._clean_string(row.get(Columns.APELLIDO)),
                "tipo_documento": self._map_tipo_documento(row.get(Columns.TIPO_DOC)),
                "numero_documento": self._safe_int(row.get(Columns.NRO_DOC)),
                "fecha_nacimiento": self._safe_date(row.get(Columns.FECHA_NACIMIENTO)),
                "sexo_biologico_al_nacer": self._map_sexo(
                    row.get(Columns.SEXO_AL_NACER)
                )
                or self._map_sexo(row.get(Columns.SEXO)),
                "sexo_biologico": self._map_sexo(row.get(Columns.SEXO)),
                "genero_autopercibido": self._clean_string(row.get(Columns.GENERO)),
                "etnia": self._clean_string(row.get(Columns.ETNIA)),
                "created_at": self._get_current_timestamp(),
                "updated_at": self._get_current_timestamp(),
            }
        except Exception as e:
            self.logger.warning(f"Error convirtiendo ciudadano: {e}")
            return None

    def _row_to_domicilio_dict(self, row: pd.Series) -> Optional[Dict]:
        """Convert row to domicilio dict."""
        domicilio_dict = {
            "codigo_ciudadano": self._safe_int(row.get(Columns.CODIGO_CIUDADANO)),
            "id_localidad_indec": self._safe_int(
                row.get(Columns.ID_LOC_INDEC_RESIDENCIA)
            ),
            "calle_domicilio": self._clean_string(row.get(Columns.CALLE_DOMICILIO)),
            "numero_domicilio": self._clean_string(row.get(Columns.NUMERO_DOMICILIO)),
            "barrio_popular": self._clean_string(row.get(Columns.BARRIO_POPULAR)),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

        # Solo agregar si tiene localidad válida Y datos de domicilio
        if (domicilio_dict["id_localidad_indec"] and 
            (domicilio_dict["calle_domicilio"] or 
             domicilio_dict["numero_domicilio"] or 
             domicilio_dict["barrio_popular"])):
            return domicilio_dict
        return None

    def _row_to_datos_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to ciudadano datos dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        return {
            "codigo_ciudadano": self._safe_int(row.get(Columns.CODIGO_CIUDADANO)),
            "id_evento": evento_mapping[id_evento_caso],
            "cobertura_social_obra_social": self._clean_string(
                row.get(Columns.COBERTURA_SOCIAL)
            ),
            "edad_anos_actual": self._safe_int(row.get(Columns.EDAD_ACTUAL)),
            "ocupacion_laboral": self._clean_string(row.get(Columns.OCUPACION)),
            "informacion_contacto": self._clean_string(row.get(Columns.INFO_CONTACTO)),
            "es_declarado_pueblo_indigena": self._safe_bool(
                row.get(Columns.SE_DECLARA_PUEBLO_INDIGENA)
            ),
            "es_embarazada": self._safe_bool(row.get(Columns.EMBARAZADA)),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

    def _row_to_viaje_dict(
        self, row: pd.Series, ciudadanos_existentes: set
    ) -> Optional[Dict]:
        """Convert row to viaje dict."""
        codigo_ciudadano = self._safe_int(row.get(Columns.CODIGO_CIUDADANO))
        if not codigo_ciudadano or codigo_ciudadano not in ciudadanos_existentes:
            return None

        id_snvs_viaje = self._safe_int(row.get(Columns.ID_SNVS_VIAJE_EPIDEMIO))
        if not id_snvs_viaje:
            return None

        return {
            "id_snvs_viaje_epidemiologico": id_snvs_viaje,
            "codigo_ciudadano": codigo_ciudadano,
            "fecha_inicio_viaje": self._safe_date(row.get(Columns.FECHA_INICIO_VIAJE)),
            "fecha_finalizacion_viaje": self._safe_date(
                row.get(Columns.FECHA_FIN_VIAJE)
            ),
            "id_localidad_destino_viaje": self._safe_int(
                row.get(Columns.ID_LOC_INDEC_VIAJE)
            ),
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

    def _get_or_create_comorbilidades(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create comorbidity catalog entries."""
        tipos_comorbilidad = df[Columns.COMORBILIDAD].dropna().unique()

        comorbilidad_mapping = {}
        for descripcion in tipos_comorbilidad:
            descripcion_limpia = self._clean_string(descripcion)
            if not descripcion_limpia:
                continue

            # Buscar existente
            stmt = (
                select(Comorbilidad.id)
                .where(Comorbilidad.descripcion == descripcion_limpia)
                .limit(1)
            )
            comorbilidad_id = self.context.session.execute(stmt).scalar()

            if not comorbilidad_id:
                # Crear nueva
                stmt = pg_insert(Comorbilidad.__table__).values(
                    {
                        "descripcion": descripcion_limpia,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )
                self.context.session.execute(stmt.on_conflict_do_nothing())

                # Obtener ID
                stmt = (
                    select(Comorbilidad.id)
                    .where(Comorbilidad.descripcion == descripcion_limpia)
                    .limit(1)
                )
                comorbilidad_id = self.context.session.execute(stmt).scalar()

            if comorbilidad_id:
                comorbilidad_mapping[descripcion_limpia] = comorbilidad_id

        return comorbilidad_mapping

    def _row_to_comorbilidad_dict(
        self,
        row: pd.Series,
        ciudadanos_existentes: set,
        comorbilidad_mapping: Dict[str, int],
    ) -> Optional[Dict]:
        """Convert row to comorbilidad relation dict."""
        codigo_ciudadano = self._safe_int(row.get(Columns.CODIGO_CIUDADANO))
        if not codigo_ciudadano or codigo_ciudadano not in ciudadanos_existentes:
            return None

        descripcion_comorbilidad = self._clean_string(row.get(Columns.COMORBILIDAD))
        id_comorbilidad = comorbilidad_mapping.get(descripcion_comorbilidad)

        if not id_comorbilidad:
            return None

        return {
            "codigo_ciudadano": codigo_ciudadano,
            "id_comorbilidad": id_comorbilidad,
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }
