"""Bulk processor for events and related entities."""

from datetime import date
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.ciudadanos.models import AmbitosConcurrenciaEvento
from app.domains.eventos.models import (
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
    DetalleEventoSintomas,
    Evento,
    GrupoEno,
    TipoEno,
)
from app.domains.salud.models import Sintoma

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class EventosBulkProcessor(BulkProcessorBase):
    """Handles event-related bulk operations."""

    def _get_or_create_grupos_eno(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create grupo ENO entries from DataFrame."""
        grupos_set = set()

        # Extraer grupos únicos de la columna GRUPO_EVENTO
        for grupo in df[Columns.GRUPO_EVENTO].dropna().unique():
            grupo_str = str(grupo).strip().upper()  # Normalizar a mayúsculas
            if grupo_str:
                grupos_set.add(grupo_str)

        if not grupos_set:
            return {}

        # Verificar existentes por código (que ahora está en mayúsculas)
        stmt = select(GrupoEno.id, GrupoEno.codigo).where(
            GrupoEno.codigo.in_(list(grupos_set))
        )
        existing_mapping = {
            codigo: grupo_id
            for grupo_id, codigo in self.context.session.execute(stmt).all()
        }

        # Crear nuevos grupos
        nuevos_grupos = []
        for grupo_codigo in grupos_set:
            if grupo_codigo not in existing_mapping:
                nuevos_grupos.append(
                    {
                        "nombre": grupo_codigo,  # Nombre en mayúsculas
                        "codigo": grupo_codigo,  # Código en mayúsculas
                        "descripcion": f"Grupo {grupo_codigo} (importado del CSV)",
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_grupos:
            stmt = pg_insert(GrupoEno.__table__).values(nuevos_grupos)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["codigo"])
            self.context.session.execute(upsert_stmt)

            # Re-obtener el mapping completo
            stmt = select(GrupoEno.id, GrupoEno.codigo).where(
                GrupoEno.codigo.in_(list(grupos_set))
            )
            existing_mapping = {
                codigo: grupo_id
                for grupo_id, codigo in self.context.session.execute(stmt).all()
            }

        return existing_mapping

    def _get_or_create_tipos_eno(
        self, df: pd.DataFrame, grupo_mapping: Dict[str, int]
    ) -> Dict[str, int]:
        """Get or create tipo ENO entries from DataFrame."""
        tipos_data = {}  # {nombre_tipo: grupo_codigo}

        # Extraer tipos únicos con sus grupos
        for _, row in df.iterrows():
            tipo = self._clean_string(row.get(Columns.EVENTO))
            grupo = self._clean_string(row.get(Columns.GRUPO_EVENTO))

            if tipo and grupo:
                # Normalizar ambos a mayúsculas
                tipo_upper = tipo.upper()
                grupo_upper = grupo.upper()

                if grupo_upper in grupo_mapping:
                    tipos_data[tipo_upper] = grupo_upper

        if not tipos_data:
            return {}

        # Verificar existentes (los nombres ahora están en mayúsculas)
        tipos_nombres = list(tipos_data.keys())
        stmt = select(TipoEno.id, TipoEno.nombre).where(
            TipoEno.nombre.in_(tipos_nombres)
        )
        existing_mapping = {
            nombre: tipo_id
            for tipo_id, nombre in self.context.session.execute(stmt).all()
        }

        # Crear nuevos tipos
        nuevos_tipos = []
        for tipo_nombre, grupo_codigo in tipos_data.items():
            if tipo_nombre not in existing_mapping:
                # Generar código slug desde el nombre (ya está en mayúsculas)
                codigo_slug = tipo_nombre.replace(" ", "_").replace("-", "_")
                nuevos_tipos.append(
                    {
                        "nombre": tipo_nombre,  # Ya está en mayúsculas
                        "codigo": codigo_slug,  # También en mayúsculas
                        "descripcion": f"Tipo {tipo_nombre} (importado del CSV)",
                        "id_grupo_eno": grupo_mapping[grupo_codigo],
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_tipos:
            stmt = pg_insert(TipoEno.__table__).values(nuevos_tipos)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["codigo"])
            self.context.session.execute(upsert_stmt)

            # Re-obtener el mapping completo
            stmt = select(TipoEno.id, TipoEno.nombre).where(
                TipoEno.nombre.in_(tipos_nombres)
            )
            existing_mapping = {
                nombre: tipo_id
                for tipo_id, nombre in self.context.session.execute(stmt).all()
            }

        return existing_mapping

    def bulk_upsert_eventos(
        self, df: pd.DataFrame, establecimiento_mapping: Dict[str, int]
    ) -> Dict[int, int]:
        """Bulk upsert de eventos principales."""
        if df.empty:
            return {}

        self.logger.info(f"Procesando {len(df)} filas de eventos")

        # Primero crear grupos y tipos ENO
        grupo_mapping = self._get_or_create_grupos_eno(df)
        tipo_mapping = self._get_or_create_tipos_eno(df, grupo_mapping)

        self.logger.info(
            f"Creados/verificados {len(grupo_mapping)} grupos ENO y {len(tipo_mapping)} tipos ENO"
        )

        # Deduplicar eventos por id_evento_caso (tomar la primera ocurrencia)
        eventos_data = []
        eventos_vistos = set()

        for _, row in df.iterrows():
            id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))

            # Solo procesar si no hemos visto este evento antes
            if id_evento_caso and id_evento_caso not in eventos_vistos:
                evento_dict = self._row_to_evento_dict(
                    row, establecimiento_mapping, tipo_mapping
                )
                if evento_dict:
                    eventos_data.append(evento_dict)
                    eventos_vistos.add(id_evento_caso)

        if not eventos_data:
            return {}

        self.logger.info(
            f"Bulk upserting {len(eventos_data)} eventos únicos (de {len(df)} filas totales)"
        )

        # PostgreSQL UPSERT
        stmt = pg_insert(Evento.__table__).values(eventos_data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id_evento_caso"],
            set_={
                "fecha_inicio_sintomas": stmt.excluded.fecha_inicio_sintomas,
                "clasificacion_estrategia": stmt.excluded.clasificacion_estrategia,
                "fecha_minima_evento": stmt.excluded.fecha_minima_evento,
                "id_establecimiento_consulta": stmt.excluded.id_establecimiento_consulta,
                "id_establecimiento_notificacion": stmt.excluded.id_establecimiento_notificacion,
                "id_establecimiento_carga": stmt.excluded.id_establecimiento_carga,
                "updated_at": self._get_current_timestamp(),
            },
        )

        self.context.session.execute(upsert_stmt)

        # Obtener mapping de IDs
        id_eventos_casos = [e["id_evento_caso"] for e in eventos_data]
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )

        return {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

    def bulk_upsert_ambitos_concurrencia(self, df: pd.DataFrame) -> BulkOperationResult:
        """Bulk upsert de ámbitos de concurrencia (OCURRENCIA columns)."""
        start_time = self._get_current_timestamp()

        # Filtrar registros con información de ámbitos/ocurrencia
        ambitos_df = df[
            df[Columns.TIPO_LUGAR_OCURRENCIA].notna()
            | df[Columns.NOMBRE_LUGAR_OCURRENCIA].notna()
            | df[Columns.LOCALIDAD_AMBITO_OCURRENCIA].notna()
            | df[Columns.SITIO_PROBABLE_ADQUISICION].notna()
            | df[Columns.SITIO_PROBABLE_DISEMINACION].notna()
            | df[Columns.FRECUENCIA].notna()
            | df[Columns.FECHA_AMBITO_OCURRENCIA].notna()
        ]

        if ambitos_df.empty:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        self.logger.info(f"Bulk upserting {len(ambitos_df)} ámbitos de concurrencia")

        # Obtener mapping de eventos
        id_eventos_casos = ambitos_df[Columns.IDEVENTOCASO].unique().tolist()

        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        ambitos_data = []
        errors = []

        for _, row in ambitos_df.iterrows():
            try:
                ambito_dict = self._row_to_ambito_dict(row, evento_mapping)
                if ambito_dict:
                    ambitos_data.append(ambito_dict)
            except Exception as e:
                errors.append(f"Error preparando ámbito concurrencia: {e}")

        if ambitos_data:
            stmt = pg_insert(AmbitosConcurrenciaEvento.__table__).values(ambitos_data)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(ambitos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_sintomas_eventos(
        self, df: pd.DataFrame, sintoma_mapping: Dict[str, int] = None
    ) -> BulkOperationResult:
        """Bulk upsert de síntomas de eventos."""
        start_time = self._get_current_timestamp()

        # Usar el mapping provisto o crear uno nuevo si no se provee
        if sintoma_mapping is None:
            sintoma_mapping = self._get_or_create_sintomas(df)

        # Obtener mapping de eventos
        id_eventos_casos = df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        sintomas_eventos_data = []
        errors = []

        # Procesar síntomas de la columna SIGNO_SINTOMA
        sintomas_df = df[df[Columns.SIGNO_SINTOMA].notna()]

        for _, row in sintomas_df.iterrows():
            try:
                sintoma_evento = self._row_to_sintoma_evento(
                    row, evento_mapping, sintoma_mapping
                )
                if sintoma_evento:
                    sintomas_eventos_data.append(sintoma_evento)
            except Exception as e:
                errors.append(f"Error preparando síntomas evento: {e}")

        if sintomas_eventos_data:
            # LOGGING DETALLADO: Verificar estado EXACTO antes del INSERT
            self.logger.error(f"=== DEBUGGING FOREIGN KEY ISSUE ===")
            self.logger.error(
                f"Intentando insertar {len(sintomas_eventos_data)} relaciones síntoma-evento"
            )

            # Verificar cada síntoma individualmente
            for i, data in enumerate(sintomas_eventos_data):
                sintoma_id = data["id_sintoma"]
                evento_id = data["id_evento"]

                # Check síntoma exists
                stmt_sintoma = select(
                    Sintoma.id, Sintoma.signo_sintoma, Sintoma.id_snvs_signo_sintoma
                ).where(Sintoma.id == sintoma_id)
                sintoma_result = self.context.session.execute(stmt_sintoma).first()

                # Check evento exists
                stmt_evento = select(Evento.id, Evento.id_evento_caso).where(
                    Evento.id == evento_id
                )

            self.context.session.flush()

            # Verificar OTRA VEZ después del flush
            for i, data in enumerate(
                sintomas_eventos_data[:1]
            ):  # Solo verificar el primero
                sintoma_id = data["id_sintoma"]
                stmt_check = select(Sintoma.id).where(Sintoma.id == sintoma_id)
                exists_post_flush = self.context.session.execute(stmt_check).first()
                self.logger.error(
                    f"Post-flush check: sintoma_id={sintoma_id} {'EXISTS' if exists_post_flush else 'NO EXISTS'}"
                )

            stmt = pg_insert(DetalleEventoSintomas.__table__).values(
                sintomas_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.logger.error(f"Ejecutando INSERT...")
            self.context.session.execute(upsert_stmt)
            self.logger.error(f"INSERT completado sin error aparente")

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(sintomas_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    def bulk_upsert_antecedentes_epidemiologicos(
        self, df: pd.DataFrame
    ) -> BulkOperationResult:
        """Bulk upsert de antecedentes epidemiológicos."""
        start_time = self._get_current_timestamp()

        # Obtener mapeo de antecedentes
        antecedentes_mapping = self._get_or_create_antecedentes(df)

        # Obtener mapping de eventos
        id_eventos_casos = df[Columns.IDEVENTOCASO].unique().tolist()
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )
        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        antecedentes_eventos_data = []
        errors = []

        # Procesar antecedentes
        antecedentes_df = df[df[Columns.ANTECEDENTE_EPIDEMIOLOGICO].notna()]

        for _, row in antecedentes_df.iterrows():
            try:
                antecedentes_list = self._row_to_antecedentes_list(
                    row, evento_mapping, antecedentes_mapping
                )
                antecedentes_eventos_data.extend(antecedentes_list)
            except Exception as e:
                errors.append(f"Error preparando antecedentes epidemiológicos: {e}")

        if antecedentes_eventos_data:
            stmt = pg_insert(AntecedentesEpidemiologicosEvento.__table__).values(
                antecedentes_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(antecedentes_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _row_to_evento_dict(
        self,
        row: pd.Series,
        establecimiento_mapping: Dict[str, int],
        tipo_mapping: Dict[str, int],
    ) -> Optional[Dict]:
        """Convert row to evento dict."""
        try:
            # Resolver establecimientos
            estab_consulta = self._clean_string(row.get(Columns.ESTAB_CLINICA))
            estab_notificacion = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_EPI)
            )
            estab_carga = self._clean_string(row.get(Columns.ESTABLECIMIENTO_CARGA))

            # Obtener tipo ENO desde el nombre del evento
            evento_nombre = self._clean_string(row.get(Columns.EVENTO))
            id_tipo_eno = tipo_mapping.get(evento_nombre)

            # No debería fallar ya que creamos todos los tipos dinámicamente
            if not id_tipo_eno:
                # Esto solo podría pasar si el evento es None/vacío
                return None

            # Usar resultado del clasificador - siempre debe haber uno
            clasificacion_estrategia = row.get("clasificacion_estrategia")
            if (
                pd.isna(clasificacion_estrategia)
                or not str(clasificacion_estrategia).strip()
            ):
                # Si no hay clasificación del classifier, marcar como requiere revisión
                from app.domains.estrategias.models import TipoClasificacion

                clasificacion_estrategia = TipoClasificacion.REQUIERE_REVISION

            return {
                "id_evento_caso": self._safe_int(row.get(Columns.IDEVENTOCASO)),
                "codigo_ciudadano": self._safe_int(row.get(Columns.CODIGO_CIUDADANO)),
                "fecha_inicio_sintomas": self._safe_date(
                    row.get(Columns.FECHA_INICIO_SINTOMA)
                ),
                "clasificacion_estrategia": clasificacion_estrategia,
                "fecha_minima_evento": self._safe_date(
                    row.get(Columns.FECHA_INICIO_SINTOMA)
                )
                or self._safe_date(row.get(Columns.FECHA_DIAG_REFERIDO))
                or date.today(),  # Campo requerido
                "id_tipo_eno": id_tipo_eno,
                # Foreign keys a establecimientos
                "id_establecimiento_consulta": establecimiento_mapping.get(
                    estab_consulta
                ),
                "id_establecimiento_notificacion": establecimiento_mapping.get(
                    estab_notificacion
                ),
                "id_establecimiento_carga": establecimiento_mapping.get(estab_carga),
                "created_at": self._get_current_timestamp(),
                "updated_at": self._get_current_timestamp(),
            }
        except Exception as e:
            self.logger.warning(f"Error convirtiendo evento: {e}")
            return None

    def _row_to_ambito_dict(
        self, row: pd.Series, evento_mapping: Dict[int, int]
    ) -> Optional[Dict]:
        """Convert row to ambito concurrencia dict."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        frecuencia_enum = self._map_frecuencia_ocurrencia(row.get(Columns.FRECUENCIA))

        ambito_dict = {
            "id_evento": evento_mapping[id_evento_caso],
            "nombre_lugar_ocurrencia": self._clean_string(
                row.get(Columns.NOMBRE_LUGAR_OCURRENCIA)
            ),
            "tipo_lugar_ocurrencia": self._clean_string(
                row.get(Columns.TIPO_LUGAR_OCURRENCIA)
            ),
            "localidad_ambito_ocurrencia": self._clean_string(
                row.get(Columns.LOCALIDAD_AMBITO_OCURRENCIA)
            ),
            "fecha_ambito_ocurrencia": self._safe_date(
                row.get(Columns.FECHA_AMBITO_OCURRENCIA)
            ),
            "es_sitio_probable_adquisicion_infeccion": self._safe_bool(
                row.get(Columns.SITIO_PROBABLE_ADQUISICION)
            ),
            "es_sitio_probable_diseminacion_infeccion": self._safe_bool(
                row.get(Columns.SITIO_PROBABLE_DISEMINACION)
            ),
            "frecuencia_concurrencia": frecuencia_enum,
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

        # Solo agregar si hay algún dato relevante
        if any(
            [
                ambito_dict["nombre_lugar_ocurrencia"],
                ambito_dict["tipo_lugar_ocurrencia"],
                ambito_dict["localidad_ambito_ocurrencia"],
                ambito_dict["fecha_ambito_ocurrencia"],
                ambito_dict["es_sitio_probable_adquisicion_infeccion"],
                ambito_dict["es_sitio_probable_diseminacion_infeccion"],
                ambito_dict["frecuencia_concurrencia"],
            ]
        ):
            return ambito_dict
        return None

    def _get_or_create_sintomas(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create symptom catalog entries."""
        # Extraer síntomas únicos con sus IDs SNVS del CSV
        # Cada fila tiene un síntoma con su ID SNVS único
        sintomas_data = {}

        for _, row in df.iterrows():
            sintoma_str = row.get(Columns.SIGNO_SINTOMA)
            id_snvs = self._safe_int(row.get(Columns.ID_SNVS_SIGNO_SINTOMA))

            # Debug logging
            self.logger.debug(
                f"Processing síntoma: {sintoma_str} with ID SNVS: {id_snvs}"
            )

            if pd.notna(sintoma_str) and sintoma_str and id_snvs:
                sintoma_limpio = self._clean_string(sintoma_str)
                if sintoma_limpio:
                    # Un síntoma por fila con su ID SNVS
                    sintomas_data[sintoma_limpio] = id_snvs
                    self.logger.debug(f"Added síntoma: {sintoma_limpio} -> {id_snvs}")

        if not sintomas_data:
            self.logger.warning("No síntomas data extracted from DataFrame")
            return {}

        # Verificar existentes
        stmt = select(Sintoma.id, Sintoma.signo_sintoma).where(
            Sintoma.signo_sintoma.in_(list(sintomas_data.keys()))
        )
        existing_mapping = {
            signo_sintoma: sintoma_id
            for sintoma_id, signo_sintoma in self.context.session.execute(stmt).all()
        }

        # Crear nuevos con IDs del CSV
        nuevos_sintomas = []
        for signo_sintoma, id_snvs in sintomas_data.items():
            if signo_sintoma not in existing_mapping:
                nuevos_sintomas.append(
                    {
                        "id_snvs_signo_sintoma": id_snvs,
                        "signo_sintoma": signo_sintoma,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_sintomas:
            stmt = pg_insert(Sintoma.__table__).values(nuevos_sintomas)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        # SIEMPRE re-obtener mapping completo después de cualquier inserción
        # Usar id_snvs_signo_sintoma para el mapping ya que es único y consistente
        stmt = select(
            Sintoma.id, Sintoma.id_snvs_signo_sintoma, Sintoma.signo_sintoma
        ).where(Sintoma.id_snvs_signo_sintoma.in_(list(sintomas_data.values())))

        # LOGGING: Ver qué síntomas encontramos en la BD después del INSERT
        all_results = list(self.context.session.execute(stmt).all())
        self.logger.error(f"=== MAPPING DE SÍNTOMAS POST-INSERT ===")
        self.logger.error(
            f"Buscando síntomas con SNVS IDs: {list(sintomas_data.values())}"
        )
        self.logger.error(f"Encontrados {len(all_results)} síntomas en la BD:")
        for sintoma_id, id_snvs, nombre in all_results:
            self.logger.error(
                f"  BD: ID={sintoma_id}, SNVS={id_snvs}, nombre='{nombre}'"
            )

        # Crear mapping por nombre de síntoma basado en los IDs SNVS
        id_snvs_to_db_id = {
            id_snvs: sintoma_id for sintoma_id, id_snvs, _ in all_results
        }

        # Crear el mapping final: signo_sintoma -> id de la BD
        final_mapping = {}
        for signo_sintoma, id_snvs in sintomas_data.items():
            if id_snvs in id_snvs_to_db_id:
                final_mapping[signo_sintoma] = id_snvs_to_db_id[id_snvs]
                self.logger.error(
                    f"  MAPPING: '{signo_sintoma}' (SNVS {id_snvs}) -> BD ID {id_snvs_to_db_id[id_snvs]}"
                )
            else:
                self.logger.error(
                    f"  ❌ FALTA: '{signo_sintoma}' (SNVS {id_snvs}) no encontrado en BD"
                )

        self.logger.error(f"Final mapping: {final_mapping}")
        return final_mapping

    def _row_to_sintoma_evento(
        self,
        row: pd.Series,
        evento_mapping: Dict[int, int],
        sintoma_mapping: Dict[str, int],
    ) -> Optional[Dict]:
        """Convert row to sintoma-evento relation (one symptom per row)."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return None

        # Un síntoma por fila (no es lista separada por comas)
        sintoma_str = self._clean_string(row.get(Columns.SIGNO_SINTOMA))
        if not sintoma_str:
            return None

        sintoma_id = sintoma_mapping.get(sintoma_str)
        if not sintoma_id:
            return None

        # Una sola relación por fila
        return {
            "id_evento": evento_mapping[id_evento_caso],
            "id_sintoma": sintoma_id,
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp(),
        }

    def _get_or_create_antecedentes(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create antecedent catalog entries."""
        antecedentes_set = set()

        for antecedente_str in df[Columns.ANTECEDENTE_EPIDEMIOLOGICO].dropna():
            if antecedente_str and str(antecedente_str).strip():
                antecedentes_list = (
                    str(antecedente_str).replace(",", "|").replace(";", "|").split("|")
                )
                for antecedente in antecedentes_list:
                    antecedente_limpio = self._clean_string(antecedente)
                    if antecedente_limpio:
                        antecedentes_set.add(antecedente_limpio)

        if not antecedentes_set:
            return {}

        # Verificar existentes
        stmt = select(
            AntecedenteEpidemiologico.id, AntecedenteEpidemiologico.descripcion
        ).where(AntecedenteEpidemiologico.descripcion.in_(list(antecedentes_set)))
        existing_mapping = {
            descripcion: ant_id
            for ant_id, descripcion in self.context.session.execute(stmt).all()
        }

        # Crear nuevos
        nuevos_antecedentes = []
        for descripcion in antecedentes_set:
            if descripcion not in existing_mapping:
                nuevos_antecedentes.append(
                    {
                        "descripcion": descripcion,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_antecedentes:
            stmt = pg_insert(AntecedenteEpidemiologico.__table__).values(
                nuevos_antecedentes
            )
            self.context.session.execute(stmt.on_conflict_do_nothing())

            # Re-obtener mapping
            stmt = select(
                AntecedenteEpidemiologico.id, AntecedenteEpidemiologico.descripcion
            ).where(AntecedenteEpidemiologico.descripcion.in_(list(antecedentes_set)))
            existing_mapping = {
                descripcion: ant_id
                for ant_id, descripcion in self.context.session.execute(stmt).all()
            }

        return existing_mapping

    def _row_to_antecedentes_list(
        self,
        row: pd.Series,
        evento_mapping: Dict[int, int],
        antecedentes_mapping: Dict[str, int],
    ) -> List[Dict]:
        """Convert row to list of antecedente-evento relations."""
        id_evento_caso = self._safe_int(row.get(Columns.IDEVENTOCASO))
        if id_evento_caso not in evento_mapping:
            return []

        antecedentes_str = self._clean_string(
            row.get(Columns.ANTECEDENTE_EPIDEMIOLOGICO)
        )
        if not antecedentes_str:
            return []

        antecedentes_list = (
            antecedentes_str.replace(",", "|").replace(";", "|").split("|")
        )
        relaciones = []

        for antecedente in antecedentes_list:
            antecedente_limpio = self._clean_string(antecedente)
            antecedente_id = antecedentes_mapping.get(antecedente_limpio)

            if antecedente_id:
                relaciones.append(
                    {
                        "id_evento": evento_mapping[id_evento_caso],
                        "id_antecedente_epidemiologico": antecedente_id,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        return relaciones
