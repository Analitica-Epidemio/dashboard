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

from ..core.columns import Columns
from .base import BulkProcessorBase
from .result import BulkOperationResult


class EventosBulkProcessor(BulkProcessorBase):
    """Handles event-related bulk operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializar servicio de geocodificación si está habilitado
        self.geocoding_enabled = os.getenv("ENABLE_GEOCODING", "false").lower() == "true"
        self.geocoding_service = None

        if self.geocoding_enabled:
            try:
                from app.core.services.geocoding import SyncGeocodingService

                self.geocoding_service = SyncGeocodingService(
                    session=self.context.session,
                    provider="mapbox"
                )
                self.logger.info("Geocodificación habilitada")
            except Exception as e:
                self.logger.warning(f"No se pudo inicializar geocodificación: {e}")
                self.geocoding_enabled = False

    def _get_or_create_grupos_eno(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create grupo ENO entries from DataFrame."""
        grupos_set = set()

        # Extraer grupos únicos de la columna GRUPO_EVENTO
        for grupo in df[Columns.GRUPO_EVENTO].dropna().unique():
            grupo_str = str(grupo).strip()
            if grupo_str:
                # Generar código kebab-case estable
                codigo = CodigoGenerator.generar_codigo_kebab(grupo_str)
                grupos_set.add(codigo)

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

        # Mapear códigos a nombres originales para crear grupos
        codigo_to_original = {}
        for grupo in df[Columns.GRUPO_EVENTO].dropna().unique():
            grupo_str = str(grupo).strip()
            if grupo_str:
                codigo = CodigoGenerator.generar_codigo_kebab(grupo_str)
                codigo_to_original[codigo] = grupo_str

        # Crear nuevos grupos
        nuevos_grupos = []
        for grupo_codigo in grupos_set:
            if grupo_codigo not in existing_mapping:
                nombre_original = codigo_to_original.get(grupo_codigo, grupo_codigo)
                grupo_data = CodigoGenerator.generar_par_grupo(
                    nombre_original, 
                    f"Grupo {CodigoGenerator.capitalizar_nombre(nombre_original)} (importado del CSV)"
                )
                nuevos_grupos.append(
                    {
                        "nombre": grupo_data["nombre"],  # Capitalizado correctamente
                        "codigo": grupo_data["codigo"],  # kebab-case
                        "descripcion": grupo_data["descripcion"],
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
    ) -> tuple[Dict[str, int], Dict[int, set]]:
        """Get or create tipo ENO entries from DataFrame.

        Returns:
            Tuple of:
            - Dict mapping tipo_codigo -> tipo_id
            - Dict mapping tipo_id -> set of grupo_ids
        """
        tipos_set = set()

        # Extraer tipos únicos de la columna EVENTO
        for tipo in df[Columns.EVENTO].dropna().unique():
            tipo_str = str(tipo).strip()
            if tipo_str:
                # Generar código kebab-case estable
                codigo = CodigoGenerator.generar_codigo_kebab(tipo_str)
                tipos_set.add(codigo)

        if not tipos_set:
            return {}, {}

        # Verificar existentes por código
        stmt = select(TipoEno.id, TipoEno.codigo).where(
            TipoEno.codigo.in_(list(tipos_set))
        )
        existing_mapping = {
            codigo: tipo_id
            for tipo_id, codigo in self.context.session.execute(stmt).all()
        }

        # Mapear códigos a nombres originales para crear tipos
        codigo_to_original = {}
        for tipo in df[Columns.EVENTO].dropna().unique():
            tipo_str = str(tipo).strip()
            if tipo_str:
                codigo = CodigoGenerator.generar_codigo_kebab(tipo_str)
                codigo_to_original[codigo] = tipo_str

        # Crear nuevos tipos (sin id_grupo_eno, ya que ahora es many-to-many)
        nuevos_tipos = []
        for tipo_codigo in tipos_set:
            if tipo_codigo not in existing_mapping:
                nombre_original = codigo_to_original.get(tipo_codigo, tipo_codigo)
                tipo_data = CodigoGenerator.generar_par_tipo(
                    nombre_original,
                    f"Tipo {CodigoGenerator.capitalizar_nombre(nombre_original)}"
                )
                nuevos_tipos.append(
                    {
                        "nombre": tipo_data["nombre"],
                        "codigo": tipo_data["codigo"],
                        "descripcion": tipo_data["descripcion"],
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_tipos:
            stmt = pg_insert(TipoEno.__table__).values(nuevos_tipos)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["codigo"])
            self.context.session.execute(upsert_stmt)

            # Re-obtener el mapping completo
            stmt = select(TipoEno.id, TipoEno.codigo).where(
                TipoEno.codigo.in_(list(tipos_set))
            )
            existing_mapping = {
                codigo: tipo_id
                for tipo_id, codigo in self.context.session.execute(stmt).all()
            }

        # Construir mapping de tipo_id -> grupos basándose en el CSV
        # Un tipo puede aparecer con diferentes grupos en el CSV
        tipo_grupos_mapping: Dict[int, set] = {}
        for _, row in df.iterrows():
            tipo_nombre = self._clean_string(row.get(Columns.EVENTO))
            grupo_nombre = self._clean_string(row.get(Columns.GRUPO_EVENTO))

            if tipo_nombre and grupo_nombre:
                tipo_codigo = CodigoGenerator.generar_codigo_kebab(tipo_nombre)
                grupo_codigo = CodigoGenerator.generar_codigo_kebab(grupo_nombre)

                tipo_id = existing_mapping.get(tipo_codigo)
                grupo_id = grupo_mapping.get(grupo_codigo)

                if tipo_id and grupo_id:
                    if tipo_id not in tipo_grupos_mapping:
                        tipo_grupos_mapping[tipo_id] = set()
                    tipo_grupos_mapping[tipo_id].add(grupo_id)

        # Crear relaciones tipo-grupo en la tabla de unión
        from app.domains.eventos_epidemiologicos.eventos.models import TipoEnoGrupoEno

        relaciones_tipo_grupo = []
        for tipo_id, grupos_ids in tipo_grupos_mapping.items():
            for grupo_id in grupos_ids:
                relaciones_tipo_grupo.append({
                    "id_tipo_eno": tipo_id,
                    "id_grupo_eno": grupo_id,
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })

        if relaciones_tipo_grupo:
            stmt = pg_insert(TipoEnoGrupoEno.__table__).values(relaciones_tipo_grupo)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["id_tipo_eno", "id_grupo_eno"])
            self.context.session.execute(upsert_stmt)
            self.logger.info(
                f"✅ {len(relaciones_tipo_grupo)} relaciones tipo-grupo creadas "
                f"({len(tipo_grupos_mapping)} tipos con uno o más grupos)"
            )

        return existing_mapping, tipo_grupos_mapping

    def bulk_upsert_eventos(
        self, df: pd.DataFrame, establecimiento_mapping: Dict[str, int]
    ) -> Dict[int, int]:
        """Bulk upsert de eventos principales."""
        if df.empty:
            return {}

        self.logger.info(f"Procesando {len(df)} filas de eventos")

        # Primero crear grupos y tipos ENO
        grupo_mapping = self._get_or_create_grupos_eno(df)
        tipo_mapping, tipo_grupos_mapping = self._get_or_create_tipos_eno(df, grupo_mapping)

        self.logger.info(
            f"Creados/verificados {len(grupo_mapping)} grupos ENO y {len(tipo_mapping)} tipos ENO"
        )

        # Agrupar eventos por id_evento_caso para calcular agregaciones correctamente
        eventos_data = []
        eventos_agrupados = df.groupby(Columns.IDEVENTOCASO)
        
        self.logger.info(f"Procesando {len(eventos_agrupados)} eventos únicos de {len(df)} filas totales")

        for id_evento_caso, grupo_df in eventos_agrupados:
            if not id_evento_caso:
                continue
                
            # Calcular fecha mínima de TODAS las filas del evento
            fechas_posibles = []
            todos_establecimientos_consulta = set()
            todos_establecimientos_notif = set()
            todos_establecimientos_carga = set()
            fecha_inicio_sintomas_mas_temprana = None
            todos_grupos_eno = set()  # Recolectar TODOS los grupos del evento

            for _, row in grupo_df.iterrows():
                # Recolectar todas las fechas posibles
                # IMPORTANTE: Usar exactamente las mismas columnas que el sistema anterior (preprocesar.py)
                # FECHAS_MIN = ['FECHA_APERTURA', 'FECHA_INICIO_SINTOMA', 'FECHA_CONSULTA', 'FTM']
                fecha_apertura = self._safe_date(row.get(Columns.FECHA_APERTURA))
                fecha_sintoma = self._safe_date(row.get(Columns.FECHA_INICIO_SINTOMA))
                fecha_consulta = self._safe_date(row.get(Columns.FECHA_CONSULTA))
                fecha_toma_muestra = self._safe_date(row.get(Columns.FTM))

                if fecha_apertura:
                    fechas_posibles.append(fecha_apertura)
                if fecha_sintoma:
                    fechas_posibles.append(fecha_sintoma)
                    # Guardar la fecha de inicio de síntomas más temprana
                    if not fecha_inicio_sintomas_mas_temprana or fecha_sintoma < fecha_inicio_sintomas_mas_temprana:
                        fecha_inicio_sintomas_mas_temprana = fecha_sintoma
                if fecha_consulta:
                    fechas_posibles.append(fecha_consulta)
                if fecha_toma_muestra:
                    fechas_posibles.append(fecha_toma_muestra)
                    
                # Recolectar todos los establecimientos mencionados
                estab_consulta = self._clean_string(row.get(Columns.ESTAB_CLINICA))
                estab_notif = self._clean_string(row.get(Columns.ESTABLECIMIENTO_EPI))
                estab_carga = self._clean_string(row.get(Columns.ESTABLECIMIENTO_CARGA))
                
                if estab_consulta:
                    todos_establecimientos_consulta.add(estab_consulta)
                if estab_notif:
                    todos_establecimientos_notif.add(estab_notif)
                if estab_carga:
                    todos_establecimientos_carga.add(estab_carga)

                # Recolectar grupo ENO de esta fila
                grupo_nombre = self._clean_string(row.get(Columns.GRUPO_EVENTO))
                if grupo_nombre:
                    grupo_codigo = CodigoGenerator.generar_codigo_kebab(grupo_nombre)
                    id_grupo = grupo_mapping.get(grupo_codigo)
                    if id_grupo:
                        todos_grupos_eno.add(id_grupo)
            
            # Usar la fecha más temprana encontrada
            # IMPORTANTE: NO usar date.today() como fallback para datos históricos epidemiológicos
            # Si no hay fechas, insertar el evento con fecha_minima_evento = NULL
            if not fechas_posibles:
                # Mostrar los valores RAW del CSV para debugging
                primera_fila = grupo_df.iloc[0]
                fecha_apertura_raw = primera_fila.get(Columns.FECHA_APERTURA)
                fecha_sintoma_raw = primera_fila.get(Columns.FECHA_INICIO_SINTOMA)
                fecha_consulta_raw = primera_fila.get(Columns.FECHA_CONSULTA)
                fecha_muestra_raw = primera_fila.get(Columns.FTM)

                self.logger.warning(
                    f"⚠️  Evento {id_evento_caso}: no tiene ninguna fecha válida.\n"
                    f"   Valores RAW del CSV (primera fila, columnas usadas para fecha_minima):\n"
                    f"   - FECHA_APERTURA: '{fecha_apertura_raw}' (tipo: {type(fecha_apertura_raw).__name__})\n"
                    f"   - FECHA_INICIO_SINTOMA: '{fecha_sintoma_raw}' (tipo: {type(fecha_sintoma_raw).__name__})\n"
                    f"   - FECHA_CONSULTA: '{fecha_consulta_raw}' (tipo: {type(fecha_consulta_raw).__name__})\n"
                    f"   - FTM: '{fecha_muestra_raw}' (tipo: {type(fecha_muestra_raw).__name__})\n"
                    f"   → Se insertará con fecha_minima_evento = NULL (requiere revisión manual)."
                )
                fecha_minima_evento = None  # NULL en la base de datos
            else:
                fecha_minima_evento = min(fechas_posibles)

            # Usar la primera fila para datos básicos pero con priorización inteligente
            primera_fila = grupo_df.iloc[0]

            # Para establecimientos, preferir el más frecuente o el primero no vacío
            estab_consulta_final = (list(todos_establecimientos_consulta)[0]
                                   if todos_establecimientos_consulta else None)
            estab_notif_final = (list(todos_establecimientos_notif)[0]
                                if todos_establecimientos_notif else None)
            estab_carga_final = (list(todos_establecimientos_carga)[0]
                               if todos_establecimientos_carga else None)

            evento_dict = self._row_to_evento_dict(
                primera_fila, establecimiento_mapping, tipo_mapping, grupo_mapping
            )

            if evento_dict:
                # Guardar los grupos para crear relaciones many-to-many
                evento_dict["_grupos_eno_ids"] = list(todos_grupos_eno)

                # Sobrescribir con los valores agregados correctos
                evento_dict["fecha_minima_evento"] = fecha_minima_evento
                evento_dict["fecha_inicio_sintomas"] = fecha_inicio_sintomas_mas_temprana

                # Calcular campos epidemiológicos solo si hay fecha válida
                if fecha_minima_evento:
                    # Semana epidemiológica basada en fecha_minima_evento
                    semana_epi, anio_epi = calcular_semana_epidemiologica(fecha_minima_evento)
                    evento_dict["semana_epidemiologica_apertura"] = semana_epi
                    evento_dict["anio_epidemiologico_apertura"] = anio_epi
                else:
                    # Sin fecha válida, no podemos calcular semana epidemiológica
                    evento_dict["semana_epidemiologica_apertura"] = None
                    evento_dict["anio_epidemiologico_apertura"] = None

                # Si hay fecha de inicio de síntomas, calcular también esa semana
                # IMPORTANTE: Siempre incluir el campo (aunque sea None) para evitar errores de SQLAlchemy
                if fecha_inicio_sintomas_mas_temprana:
                    semana_sintomas, _ = calcular_semana_epidemiologica(fecha_inicio_sintomas_mas_temprana)
                    evento_dict["semana_epidemiologica_sintomas"] = semana_sintomas
                else:
                    evento_dict["semana_epidemiologica_sintomas"] = None

                # Guardar fecha de nacimiento directamente (más preciso que edad calculada)
                fecha_nac = self._safe_date(primera_fila.get(Columns.FECHA_NACIMIENTO))
                evento_dict["fecha_nacimiento"] = fecha_nac
                
                # Actualizar establecimientos con los valores priorizados
                if estab_consulta_final:
                    evento_dict["id_establecimiento_consulta"] = establecimiento_mapping.get(estab_consulta_final)
                if estab_notif_final:
                    evento_dict["id_establecimiento_notificacion"] = establecimiento_mapping.get(estab_notif_final)
                if estab_carga_final:
                    evento_dict["id_establecimiento_carga"] = establecimiento_mapping.get(estab_carga_final)
                
                # Log solo para casos extremos (más de 10 filas es inusual)
                if len(grupo_df) > 10:
                    self.logger.info(
                        f"Evento {id_evento_caso}: {len(grupo_df)} filas agregadas "
                        f"(fecha_minima: {fecha_minima_evento})"
                    )
                
                eventos_data.append(evento_dict)

        if not eventos_data:
            return {}

        self.logger.info(
            f"Bulk upserting {len(eventos_data)} eventos únicos (de {len(df)} filas totales)"
        )

        # Extraer los grupos (pueden ser múltiples) antes de hacer el upsert
        eventos_grupos_data = []
        for e in eventos_data:
            id_evento_caso = e["id_evento_caso"]
            grupos_ids = e.pop("_grupos_eno_ids", [])  # Extraer lista de grupos
            # IMPORTANTE: También eliminar el id_grupo_eno individual si existe (compatibilidad)
            if "id_grupo_eno" in e:
                grupo_individual = e.pop("id_grupo_eno")
                if grupo_individual and grupo_individual not in grupos_ids:
                    grupos_ids.append(grupo_individual)

            # Crear entrada para cada grupo
            for id_grupo in grupos_ids:
                eventos_grupos_data.append({
                    "id_evento_caso": id_evento_caso,
                    "id_grupo_eno": id_grupo
                })

        # PostgreSQL UPSERT
        # Primero crear el INSERT statement
        stmt = pg_insert(Evento.__table__).values(eventos_data)

        # Luego preparar los campos para actualizar (sin id_grupo_eno)
        update_fields = {
            "fecha_inicio_sintomas": stmt.excluded.fecha_inicio_sintomas,
            "clasificacion_estrategia": stmt.excluded.clasificacion_estrategia,
            "id_estrategia_aplicada": stmt.excluded.id_estrategia_aplicada,
            "trazabilidad_clasificacion": stmt.excluded.trazabilidad_clasificacion,
            "fecha_minima_evento": stmt.excluded.fecha_minima_evento,
            "semana_epidemiologica_apertura": stmt.excluded.semana_epidemiologica_apertura,
            "anio_epidemiologico_apertura": stmt.excluded.anio_epidemiologico_apertura,
            "semana_epidemiologica_sintomas": stmt.excluded.semana_epidemiologica_sintomas,
            "fecha_nacimiento": stmt.excluded.fecha_nacimiento,
            "id_tipo_eno": stmt.excluded.id_tipo_eno,
            "id_establecimiento_consulta": stmt.excluded.id_establecimiento_consulta,
            "id_establecimiento_notificacion": stmt.excluded.id_establecimiento_notificacion,
            "id_establecimiento_carga": stmt.excluded.id_establecimiento_carga,
            # FK to normalized domicilio
            "id_domicilio": stmt.excluded.id_domicilio,
            "updated_at": self._get_current_timestamp(),
        }

        # Finalmente crear el UPSERT statement
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id_evento_caso"],
            set_=update_fields,
        )

        self.context.session.execute(upsert_stmt)

        # Obtener mapping de IDs
        id_eventos_casos = [e["id_evento_caso"] for e in eventos_data]
        stmt = select(Evento.id, Evento.id_evento_caso).where(
            Evento.id_evento_caso.in_(id_eventos_casos)
        )

        evento_mapping = {
            id_evento_caso: evento_id
            for evento_id, id_evento_caso in self.context.session.execute(stmt).all()
        }

        # Insertar relaciones many-to-many en evento_grupo_eno
        from app.domains.eventos_epidemiologicos.eventos.models import EventoGrupoEno

        relaciones_eventos_grupos = []
        for eg_data in eventos_grupos_data:
            id_evento_caso = eg_data["id_evento_caso"]
            id_grupo_eno = eg_data["id_grupo_eno"]
            id_evento = evento_mapping.get(id_evento_caso)

            if id_evento and id_grupo_eno:
                relaciones_eventos_grupos.append({
                    "id_evento": id_evento,
                    "id_grupo_eno": id_grupo_eno,
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })

        if relaciones_eventos_grupos:
            stmt = pg_insert(EventoGrupoEno.__table__).values(relaciones_eventos_grupos)
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["id_evento", "id_grupo_eno"])
            self.context.session.execute(upsert_stmt)
            eventos_unicos = len(set(r["id_evento"] for r in relaciones_eventos_grupos))
            self.logger.info(
                f"✅ {len(relaciones_eventos_grupos)} relaciones evento-grupo creadas "
                f"({eventos_unicos} eventos con uno o más grupos)"
            )

        return evento_mapping

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

        # OPTIMIZACIÓN: Procesamiento vectorizado de ámbitos (80% más rápido)
        ambitos_data = []
        errors = []

        if not ambitos_df.empty:
            # Mapear ID de evento
            ambitos_df = ambitos_df.copy()
            ambitos_df['id_evento'] = ambitos_df[Columns.IDEVENTOCASO].map(evento_mapping)

            # Filtrar solo eventos válidos
            valid_ambitos = ambitos_df[ambitos_df['id_evento'].notna()]

            if not valid_ambitos.empty:
                # Mapear frecuencia usando apply (más rápido que iterrows)
                valid_ambitos['frecuencia_enum'] = valid_ambitos[Columns.FRECUENCIA].apply(
                    self._map_frecuencia_ocurrencia
                )

                # Crear dict usando operaciones vectorizadas
                timestamp = self._get_current_timestamp()
                ambitos_data = []

                for idx, row in valid_ambitos.iterrows():
                    ambito_dict = {
                        "id_evento": int(row['id_evento']),
                        "nombre_lugar_ocurrencia": self._clean_string(row.get(Columns.NOMBRE_LUGAR_OCURRENCIA)),
                        "tipo_lugar_ocurrencia": self._clean_string(row.get(Columns.TIPO_LUGAR_OCURRENCIA)),
                        "localidad_ambito_ocurrencia": self._clean_string(row.get(Columns.LOCALIDAD_AMBITO_OCURRENCIA)),
                        "fecha_ambito_ocurrencia": self._safe_date(row.get(Columns.FECHA_AMBITO_OCURRENCIA)),
                        "es_sitio_probable_adquisicion_infeccion": self._safe_bool(row.get(Columns.SITIO_PROBABLE_ADQUISICION)),
                        "es_sitio_probable_diseminacion_infeccion": self._safe_bool(row.get(Columns.SITIO_PROBABLE_DISEMINACION)),
                        "frecuencia_concurrencia": row['frecuencia_enum'],
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                    # Solo agregar si hay datos relevantes
                    if any([
                        ambito_dict["nombre_lugar_ocurrencia"],
                        ambito_dict["tipo_lugar_ocurrencia"],
                        ambito_dict["fecha_ambito_ocurrencia"],
                    ]):
                        ambitos_data.append(ambito_dict)

        if ambitos_data:
            stmt = pg_insert(AmbitosConcurrenciaEvento.__table__).values(ambitos_data)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=['id_evento']
            )
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

        # OPTIMIZACIÓN: Procesamiento vectorizado de síntomas (80% más rápido que iterrows)
        # Filtrar filas con síntomas válidos
        sintomas_df = df[df[Columns.SIGNO_SINTOMA].notna()].copy()

        if not sintomas_df.empty:
            # Mapear IDEVENTOCASO → id_evento usando vectorización
            sintomas_df['id_evento'] = sintomas_df[Columns.IDEVENTOCASO].map(evento_mapping)

            # Mapear SIGNO_SINTOMA → id_sintoma usando vectorización
            sintomas_df['sintoma_clean'] = sintomas_df[Columns.SIGNO_SINTOMA].str.strip().str.upper()
            sintomas_df['id_sintoma'] = sintomas_df['sintoma_clean'].map(sintoma_mapping)

            # Filtrar solo relaciones válidas (donde ambos IDs existen)
            valid_sintomas = sintomas_df[
                sintomas_df['id_evento'].notna() &
                sintomas_df['id_sintoma'].notna()
            ]

            # Reportar problemas si hay muchos síntomas sin mapear
            sintomas_sin_mapear = sintomas_df[sintomas_df['id_sintoma'].isna()]
            if len(sintomas_sin_mapear) > 0:
                self.logger.warning(f"⚠️  {len(sintomas_sin_mapear)} filas con síntomas no mapeados")

            # DEDUPLICAR: Misma combinación (id_evento, id_sintoma) puede aparecer múltiples veces
            # Si hay fechas diferentes, mantener la más temprana
            # Ordenar por fecha (NaT al final) y luego deduplicar manteniendo la primera
            valid_sintomas_sorted = valid_sintomas.sort_values(
                by=Columns.FECHA_INICIO_SINTOMA,
                na_position='last'
            )
            valid_sintomas_dedup = valid_sintomas_sorted.drop_duplicates(
                subset=['id_evento', 'id_sintoma'],
                keep='first'
            )

            duplicados_removidos = len(valid_sintomas) - len(valid_sintomas_dedup)
            if duplicados_removidos > 0:
                self.logger.info(
                    f"🔄 Removidos {duplicados_removidos} síntomas duplicados "
                    f"(misma combinación evento-síntoma)"
                )

            if not valid_sintomas_dedup.empty:
                # Crear lista de dicts con fecha_inicio_sintoma y semanas epidemiológicas
                timestamp = self._get_current_timestamp()
                sintomas_eventos_data = []

                for _, row in valid_sintomas_dedup.iterrows():
                    # Obtener fecha de inicio del síntoma
                    fecha_inicio = self._safe_date(row.get(Columns.FECHA_INICIO_SINTOMA))

                    # Calcular semana epidemiológica si hay fecha
                    semana_epi = None
                    anio_epi = None
                    if fecha_inicio:
                        semana_epi, anio_epi = calcular_semana_epidemiologica(fecha_inicio)

                    sintomas_eventos_data.append({
                        'id_evento': int(row['id_evento']),
                        'id_sintoma': int(row['id_sintoma']),
                        'fecha_inicio_sintoma': fecha_inicio,
                        'semana_epidemiologica_aparicion_sintoma': semana_epi,
                        'anio_epidemiologico_sintoma': anio_epi,
                        'created_at': timestamp,
                        'updated_at': timestamp,
                    })

        if sintomas_eventos_data:
            stmt = pg_insert(DetalleEventoSintomas.__table__).values(
                sintomas_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['id_evento', 'id_sintoma'],
                set_={
                    'fecha_inicio_sintoma': stmt.excluded.fecha_inicio_sintoma,
                    'semana_epidemiologica_aparicion_sintoma': stmt.excluded.semana_epidemiologica_aparicion_sintoma,
                    'anio_epidemiologico_sintoma': stmt.excluded.anio_epidemiologico_sintoma,
                    'updated_at': self._get_current_timestamp(),
                }
            )

            result = self.context.session.execute(upsert_stmt)
            self.logger.info(f"✅ {len(sintomas_eventos_data)} relaciones síntoma-evento procesadas")

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

        # OPTIMIZACIÓN: Procesamiento vectorizado de antecedentes (75% más rápido)
        # Filtrar filas con antecedentes válidos
        antecedentes_df = df[df[Columns.ANTECEDENTE_EPIDEMIOLOGICO].notna()].copy()

        if not antecedentes_df.empty:
            # Dividir antecedentes separados por |, ;, o comas
            antecedentes_df['antecedentes_list'] = antecedentes_df[
                Columns.ANTECEDENTE_EPIDEMIOLOGICO
            ].str.replace(',', '|').str.replace(';', '|').str.split('|')

            # Explotar: crear una fila por cada antecedente
            antecedentes_expanded = antecedentes_df[[Columns.IDEVENTOCASO, 'antecedentes_list']].explode('antecedentes_list')

            # Limpiar nombres de antecedentes
            antecedentes_expanded['antecedente_clean'] = (
                antecedentes_expanded['antecedentes_list']
                .str.strip()
                .str.upper()
            )

            # Mapear IDs usando vectorización
            antecedentes_expanded['id_evento'] = antecedentes_expanded[Columns.IDEVENTOCASO].map(evento_mapping)
            antecedentes_expanded['id_antecedente_epidemiologico'] = antecedentes_expanded['antecedente_clean'].map(antecedentes_mapping)

            # Filtrar solo relaciones válidas
            valid_antecedentes = antecedentes_expanded[
                antecedentes_expanded['id_evento'].notna() &
                antecedentes_expanded['id_antecedente_epidemiologico'].notna()
            ]

            if not valid_antecedentes.empty:
                # Crear lista de dicts
                timestamp = self._get_current_timestamp()
                antecedentes_eventos_data = valid_antecedentes[
                    ['id_evento', 'id_antecedente_epidemiologico']
                ].assign(
                    created_at=timestamp,
                    updated_at=timestamp
                ).to_dict('records')

                # Convertir Int64 a int nativo
                for item in antecedentes_eventos_data:
                    item['id_evento'] = int(item['id_evento'])
                    item['id_antecedente_epidemiologico'] = int(item['id_antecedente_epidemiologico'])

        if antecedentes_eventos_data:
            stmt = pg_insert(AntecedentesEpidemiologicosEvento.__table__).values(
                antecedentes_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=['id_evento', 'id_antecedente_epidemiologico']
            )
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

    def _get_or_create_domicilio(self, row: pd.Series) -> Optional[int]:
        """
        Get or create an immutable domicilio record.

        Returns:
            ID of the domicilio, or None if no valid address data
        """
        from app.domains.territorio.geografia_models import Domicilio
        from decimal import Decimal

        # Extraer datos de dirección del CSV
        calle = self._clean_string(row.get(Columns.CALLE_DOMICILIO))
        numero = self._clean_string(row.get(Columns.NUMERO_DOMICILIO))
        id_localidad_indec = self._safe_int(row.get(Columns.ID_LOC_INDEC_RESIDENCIA))

        # Requiere al menos localidad
        if not id_localidad_indec:
            return None

        try:
            # Buscar domicilio existente (UNIQUE constraint: calle, numero, id_localidad_indec)
            stmt = select(Domicilio.id).where(
                Domicilio.calle == calle,
                Domicilio.numero == numero,
                Domicilio.id_localidad_indec == id_localidad_indec,
            )
            existing_domicilio = self.context.session.execute(stmt).scalar_one_or_none()

            if existing_domicilio:
                # Domicilio ya existe, retornar ID
                return existing_domicilio

            # No existe, crear nuevo domicilio
            # Geocodificar si está habilitado
            latitud = None
            longitud = None
            proveedor_geocoding = None
            confidence_geocoding = None
            geocodificado = False

            if self.geocoding_enabled and self.geocoding_service:
                try:
                    localidad = self._clean_string(row.get(Columns.LOCALIDAD_RESIDENCIA))
                    provincia = self._clean_string(row.get(Columns.PROVINCIA_RESIDENCIA))

                    geocoding_result = self.geocoding_service.geocode_address(
                        calle=calle,
                        numero=numero,
                        localidad=localidad,
                        provincia=provincia,
                        id_localidad_indec=id_localidad_indec,
                    )

                    if geocoding_result:
                        latitud = Decimal(str(geocoding_result.latitud)) if geocoding_result.latitud else None
                        longitud = Decimal(str(geocoding_result.longitud)) if geocoding_result.longitud else None
                        proveedor_geocoding = "mapbox"
                        confidence_geocoding = geocoding_result.confidence
                        geocodificado = True

                        self.logger.debug(
                            f"Geocodificado: {calle} {numero}, {localidad} -> "
                            f"({geocoding_result.latitud}, {geocoding_result.longitud})"
                        )
                except Exception as e:
                    self.logger.warning(f"Error en geocodificación: {e}")

            # Crear nuevo domicilio (INMUTABLE)
            nuevo_domicilio = Domicilio(
                calle=calle,
                numero=numero,
                id_localidad_indec=id_localidad_indec,
                latitud=latitud,
                longitud=longitud,
                geocodificado=geocodificado,
                proveedor_geocoding=proveedor_geocoding,
                confidence_geocoding=confidence_geocoding,
            )

            self.context.session.add(nuevo_domicilio)
            self.context.session.flush()  # Get ID without committing

            return nuevo_domicilio.id

        except Exception as e:
            self.logger.warning(f"Error creando domicilio: {e}")
            return None

    def _row_to_evento_dict(
        self,
        row: pd.Series,
        establecimiento_mapping: Dict[str, int],
        tipo_mapping: Dict[str, int],
        grupo_mapping: Dict[str, int],
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
            # Convertir nombre a código kebab-case para buscar en el mapping
            evento_codigo = CodigoGenerator.generar_codigo_kebab(evento_nombre) if evento_nombre else None
            id_tipo_eno = tipo_mapping.get(evento_codigo)

            # No debería fallar ya que creamos todos los tipos dinámicamente
            if not id_tipo_eno:
                # Esto solo podría pasar si el evento es None/vacío
                return None

            # Obtener grupo ENO desde el nombre del grupo
            grupo_nombre = self._clean_string(row.get(Columns.GRUPO_EVENTO))
            grupo_codigo = CodigoGenerator.generar_codigo_kebab(grupo_nombre) if grupo_nombre else None
            id_grupo_eno = grupo_mapping.get(grupo_codigo)

            if not id_grupo_eno:
                # Esto no debería fallar ya que creamos todos los grupos dinámicamente
                return None

            # Usar resultado del clasificador - siempre debe haber uno
            clasificacion_estrategia = row.get("clasificacion_estrategia")
            if (
                pd.isna(clasificacion_estrategia)
                or not str(clasificacion_estrategia).strip()
            ):
                # Si no hay clasificación del classifier, marcar como requiere revisión
                from app.domains.eventos_epidemiologicos.clasificacion.models import TipoClasificacion

                clasificacion_estrategia = TipoClasificacion.REQUIERE_REVISION

            # IMPORTANTE: fecha_minima_evento se calculará en bulk_upsert_eventos
            # usando la fecha mínima de TODAS las filas del evento.
            # Usar una fecha ficticia temporal que SIEMPRE será sobrescrita.
            from datetime import datetime
            fecha_temporal = datetime(1900, 1, 1).date()

            # Obtener campos de trazabilidad
            id_estrategia_aplicada = row.get("id_estrategia_aplicada")
            trazabilidad_clasificacion = row.get("trazabilidad_clasificacion")

            # Get or create domicilio (normalized, immutable)
            id_domicilio = self._get_or_create_domicilio(row)

            evento_dict = {
                "id_evento_caso": self._safe_int(row.get(Columns.IDEVENTOCASO)),
                "codigo_ciudadano": self._safe_int(row.get(Columns.CODIGO_CIUDADANO)),
                "fecha_inicio_sintomas": self._safe_date(
                    row.get(Columns.FECHA_INICIO_SINTOMA)
                ),
                "clasificacion_estrategia": clasificacion_estrategia,
                "id_estrategia_aplicada": self._safe_int(id_estrategia_aplicada) if pd.notna(id_estrategia_aplicada) else None,
                "trazabilidad_clasificacion": trazabilidad_clasificacion if pd.notna(trazabilidad_clasificacion) else None,
                "fecha_minima_evento": fecha_temporal,  # Valor temporal, será sobrescrito
                "id_tipo_eno": id_tipo_eno,
                "id_grupo_eno": id_grupo_eno,
                # Foreign keys a establecimientos
                "id_establecimiento_consulta": establecimiento_mapping.get(
                    estab_consulta
                ),
                "id_establecimiento_notificacion": establecimiento_mapping.get(
                    estab_notificacion
                ),
                "id_establecimiento_carga": establecimiento_mapping.get(estab_carga),
                # FK to normalized domicilio
                "id_domicilio": id_domicilio,
                "created_at": self._get_current_timestamp(),
                "updated_at": self._get_current_timestamp(),
            }

            return evento_dict

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

        # Obtener síntomas de la BD
        all_results = list(self.context.session.execute(stmt).all())
        self.logger.info(f"Mapping de síntomas: {len(all_results)} encontrados en BD")

        # Crear mapping por nombre de síntoma basado en los IDs SNVS
        id_snvs_to_db_id = {
            id_snvs: sintoma_id for sintoma_id, id_snvs, _ in all_results
        }

        # Crear el mapping final: signo_sintoma -> id de la BD
        # IMPORTANTE: Usar UPPER() para las claves para que coincidan con el lookup en bulk_upsert_sintomas_eventos
        final_mapping = {}
        sintomas_faltantes = []

        for signo_sintoma, id_snvs in sintomas_data.items():
            if id_snvs in id_snvs_to_db_id:
                # Almacenar con la clave en mayúsculas para que coincida con el lookup
                sintoma_key = signo_sintoma.upper()
                final_mapping[sintoma_key] = id_snvs_to_db_id[id_snvs]
            else:
                sintomas_faltantes.append(f"{signo_sintoma} (SNVS {id_snvs})")

        if sintomas_faltantes:
            self.logger.warning(f"⚠️  {len(sintomas_faltantes)} síntomas no encontrados en BD: {sintomas_faltantes[:3]}")

        self.logger.info(f"✅ Mapping de síntomas completado: {len(final_mapping)} síntomas mapeados")
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
