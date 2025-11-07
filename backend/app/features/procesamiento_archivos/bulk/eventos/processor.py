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
from ..shared import is_valid_street_name


class EventosProcessor(BulkProcessorBase):
    """Handles event-related bulk operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializar servicio de geocodificación si está habilitado
        self.geocoding_enabled = (
            os.getenv("ENABLE_GEOCODING", "false").lower() == "true"
        )
        self.geocoding_service = None

        if self.geocoding_enabled:
            try:
                from app.core.services.geocoding import SyncGeocodingService

                self.geocoding_service = SyncGeocodingService(
                    session=self.context.session, provider="mapbox"
                )
                self.logger.info("Geocodificación habilitada")
            except Exception as e:
                self.logger.warning(f"No se pudo inicializar geocodificación: {e}")
                self.geocoding_enabled = False

    def _get_or_create_grupos_eno(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create grupo ENO entries using generic pattern with CodigoGenerator."""

        # DEBUG: Ver qué grupos tenemos en el CSV
        grupos_unicos = df[Columns.GRUPO_EVENTO.name].dropna().unique()
        self.logger.info(
            f"🔍 DEBUG: Grupos únicos en CSV ({len(grupos_unicos)}): {list(grupos_unicos)[:10]}"
        )

        def transform_grupo(valor: str) -> Dict:
            """Transform CSV value to GrupoEno record."""
            grupo_data = CodigoGenerator.generar_par_grupo(
                valor,
                f"Grupo {CodigoGenerator.capitalizar_nombre(valor)} (importado del CSV)",
            )
            return {
                "nombre": grupo_data["nombre"],
                "codigo": grupo_data["codigo"],
                "descripcion": grupo_data["descripcion"],
            }

        # Use existing catalog function from catalogs.py pattern
        result = get_or_create_catalog(
            session=self.context.session,
            model=GrupoEno,
            df=df,
            column=Columns.GRUPO_EVENTO.name,
            key_field="codigo",
            transform_fn=transform_grupo,
        )

        self.logger.info(
            f"🔍 DEBUG: Grupos creados/encontrados ({len(result)}): {list(result.keys())[:10]}"
        )
        return result

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
        for tipo in df[Columns.EVENTO.name].dropna().unique():
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
        for tipo in df[Columns.EVENTO.name].dropna().unique():
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
                    f"Tipo {CodigoGenerator.capitalizar_nombre(nombre_original)}",
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

        # OPTIMIZACIÓN: Construir mapping vectorizado (10-50x más rápido que iterrows)
        tipo_grupos_mapping: Dict[int, set] = {}

        # Vectorizado: preparar datos
        df_mapping = (
            df[[Columns.EVENTO.name, Columns.GRUPO_EVENTO.name]].dropna().copy()
        )

        if not df_mapping.empty:
            df_mapping["tipo_limpio"] = df_mapping[Columns.EVENTO.name].apply(
                self._clean_string
            )
            df_mapping["grupo_limpio"] = df_mapping[Columns.GRUPO_EVENTO.name].apply(
                self._clean_string
            )
            df_mapping = df_mapping[
                df_mapping["tipo_limpio"].notna() & df_mapping["grupo_limpio"].notna()
            ]

            df_mapping["tipo_codigo"] = df_mapping["tipo_limpio"].apply(
                CodigoGenerator.generar_codigo_kebab
            )
            df_mapping["grupo_codigo"] = df_mapping["grupo_limpio"].apply(
                CodigoGenerator.generar_codigo_kebab
            )

            df_mapping["tipo_id"] = df_mapping["tipo_codigo"].map(existing_mapping)
            df_mapping["grupo_id"] = df_mapping["grupo_codigo"].map(grupo_mapping)

            # Filtrar solo los que tienen ambos IDs válidos
            df_valido = df_mapping[
                df_mapping["tipo_id"].notna() & df_mapping["grupo_id"].notna()
            ]

            # Agrupar para construir sets
            for tipo_id, group_df in df_valido.groupby("tipo_id"):
                tipo_grupos_mapping[int(tipo_id)] = set(
                    group_df["grupo_id"].astype(int).unique()
                )

        # Crear relaciones tipo-grupo en la tabla de unión
        from app.domains.eventos_epidemiologicos.eventos.models import TipoEnoGrupoEno

        relaciones_tipo_grupo = []
        for tipo_id, grupos_ids in tipo_grupos_mapping.items():
            for grupo_id in grupos_ids:
                relaciones_tipo_grupo.append(
                    {
                        "id_tipo_eno": int(tipo_id),  # Convertir numpy.int64 → int
                        "id_grupo_eno": int(grupo_id),  # Convertir numpy.int64 → int
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if relaciones_tipo_grupo:
            stmt = pg_insert(TipoEnoGrupoEno.__table__).values(relaciones_tipo_grupo)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=["id_tipo_eno", "id_grupo_eno"]
            )
            self.context.session.execute(upsert_stmt)
            self.logger.info(
                f"{len(relaciones_tipo_grupo)} relaciones tipo-grupo creadas "
                f"({len(tipo_grupos_mapping)} tipos con uno o más grupos)"
            )

        return existing_mapping, tipo_grupos_mapping

    def upsert_eventos(
        self, df: pd.DataFrame, establecimiento_mapping: Dict[str, int]
    ) -> Dict[int, int]:
        """Bulk upsert de eventos principales."""
        if df.empty:
            return {}

        self.logger.info(f"Procesando {len(df)} filas de eventos")

        # Primero crear grupos y tipos ENO
        grupo_mapping = self._get_or_create_grupos_eno(df)
        tipo_mapping, tipo_grupos_mapping = self._get_or_create_tipos_eno(
            df, grupo_mapping
        )

        self.logger.info(
            f"Creados/verificados {len(grupo_mapping)} grupos ENO y {len(tipo_mapping)} tipos ENO"
        )

        # Agrupar eventos por id_evento_caso para calcular agregaciones correctamente
        eventos_data = []
        eventos_agrupados = df.groupby(Columns.IDEVENTOCASO.name)

        self.logger.info(
            f"Procesando {len(eventos_agrupados)} eventos únicos de {len(df)} filas totales"
        )

        # OPTIMIZACIÓN: Vectorizado - agregación de eventos usando groupby (50-100x más rápido)
        # Preparar datos para agregación
        df_for_agg = df.copy()

        # Limpiar columnas de establecimientos y grupos de una vez
        df_for_agg["estab_consulta_clean"] = df_for_agg[
            Columns.ESTAB_CLINICA.name
        ].apply(lambda x: self._clean_string(x) if pd.notna(x) else None)
        df_for_agg["estab_notif_clean"] = df_for_agg[
            Columns.ESTABLECIMIENTO_EPI.name
        ].apply(lambda x: self._clean_string(x) if pd.notna(x) else None)
        df_for_agg["estab_carga_clean"] = df_for_agg[
            Columns.ESTABLECIMIENTO_CARGA.name
        ].apply(lambda x: self._clean_string(x) if pd.notna(x) else None)

        # Mapear grupos ENO de una vez
        df_for_agg["grupo_nombre_clean"] = df_for_agg[Columns.GRUPO_EVENTO.name].apply(
            lambda x: self._clean_string(x) if pd.notna(x) else None
        )
        df_for_agg["grupo_id"] = df_for_agg["grupo_nombre_clean"].apply(
            lambda x: (
                grupo_mapping.get(CodigoGenerator.generar_codigo_kebab(x))
                if x
                else None
            )
        )

        # Agregar por IDEVENTOCASO
        agg_results = df_for_agg.groupby(Columns.IDEVENTOCASO.name).agg(
            {
                # Fechas: tomar la mínima de cada columna (pd.NaT es ignorado por min())
                Columns.FECHA_APERTURA.name: "min",
                Columns.FECHA_INICIO_SINTOMA.name: "min",
                Columns.FECHA_CONSULTA.name: "min",
                Columns.FTM.name: "min",
                # Establecimientos: tomar el primer valor no nulo
                "estab_consulta_clean": lambda x: (
                    x.dropna().iloc[0] if len(x.dropna()) > 0 else None
                ),
                "estab_notif_clean": lambda x: (
                    x.dropna().iloc[0] if len(x.dropna()) > 0 else None
                ),
                "estab_carga_clean": lambda x: (
                    x.dropna().iloc[0] if len(x.dropna()) > 0 else None
                ),
                # Grupos ENO: recolectar TODOS los IDs únicos
                "grupo_id": lambda x: set(x.dropna().unique()),
            }
        )

        for id_evento_caso, grupo_df in eventos_agrupados:
            if not id_evento_caso or id_evento_caso not in agg_results.index:
                continue

            # Obtener datos agregados
            agg_data = agg_results.loc[id_evento_caso]

            # Calcular fecha_minima_evento: la mínima de las 4 columnas
            fechas_candidatas = [
                agg_data[Columns.FECHA_APERTURA.name],
                agg_data[Columns.FECHA_INICIO_SINTOMA.name],
                agg_data[Columns.FECHA_CONSULTA.name],
                agg_data[Columns.FTM.name],
            ]
            # Filtrar NaT/None
            fechas_validas = [f for f in fechas_candidatas if pd.notna(f)]

            if not fechas_validas:
                # Mostrar los valores RAW del CSV para debugging
                primera_fila = grupo_df.iloc[0]
                fecha_apertura_raw = primera_fila.get(Columns.FECHA_APERTURA.name)
                fecha_sintoma_raw = primera_fila.get(Columns.FECHA_INICIO_SINTOMA.name)
                fecha_consulta_raw = primera_fila.get(Columns.FECHA_CONSULTA.name)
                fecha_muestra_raw = primera_fila.get(Columns.FTM.name)

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
                fecha_minima_evento = min(fechas_validas)

            # Fecha de inicio de síntomas más temprana (ya calculada por min())
            fecha_inicio_sintomas_mas_temprana = agg_data[
                Columns.FECHA_INICIO_SINTOMA.name
            ]
            if pd.isna(fecha_inicio_sintomas_mas_temprana):
                fecha_inicio_sintomas_mas_temprana = None

            # Usar la primera fila para datos básicos
            primera_fila = grupo_df.iloc[0]

            # Obtener establecimientos agregados
            estab_consulta_final = agg_data["estab_consulta_clean"]
            estab_notif_final = agg_data["estab_notif_clean"]
            estab_carga_final = agg_data["estab_carga_clean"]

            # Obtener grupos ENO agregados
            todos_grupos_eno = agg_data["grupo_id"]

            evento_dict = self._row_to_evento_dict(
                primera_fila, establecimiento_mapping, tipo_mapping, grupo_mapping
            )

            if evento_dict:
                # Guardar los grupos para crear relaciones many-to-many
                evento_dict["_grupos_eno_ids"] = list(todos_grupos_eno)

                # Sobrescribir con los valores agregados correctos
                evento_dict["fecha_minima_evento"] = fecha_minima_evento
                evento_dict["fecha_inicio_sintomas"] = (
                    fecha_inicio_sintomas_mas_temprana
                )

                # Calcular campos epidemiológicos solo si hay fecha válida
                if fecha_minima_evento:
                    # Convertir pd.Timestamp a datetime.date para calcular_semana_epidemiologica
                    fecha_minima_date = (
                        fecha_minima_evento.date()
                        if hasattr(fecha_minima_evento, "date")
                        else fecha_minima_evento
                    )

                    # Semana epidemiológica basada en fecha_minima_evento
                    semana_epi, anio_epi = calcular_semana_epidemiologica(
                        fecha_minima_date
                    )
                    evento_dict["semana_epidemiologica_apertura"] = semana_epi
                    evento_dict["anio_epidemiologico_apertura"] = anio_epi
                else:
                    # Sin fecha válida, no podemos calcular semana epidemiológica
                    evento_dict["semana_epidemiologica_apertura"] = None
                    evento_dict["anio_epidemiologico_apertura"] = None

                # Si hay fecha de inicio de síntomas, calcular también esa semana
                # IMPORTANTE: Siempre incluir el campo (aunque sea None) para evitar errores de SQLAlchemy
                if fecha_inicio_sintomas_mas_temprana:
                    # Convertir pd.Timestamp a datetime.date
                    fecha_sintomas_date = (
                        fecha_inicio_sintomas_mas_temprana.date()
                        if hasattr(fecha_inicio_sintomas_mas_temprana, "date")
                        else fecha_inicio_sintomas_mas_temprana
                    )

                    semana_sintomas, _ = calcular_semana_epidemiologica(
                        fecha_sintomas_date
                    )
                    evento_dict["semana_epidemiologica_sintomas"] = semana_sintomas
                else:
                    evento_dict["semana_epidemiologica_sintomas"] = None

                # Guardar fecha de nacimiento directamente (más preciso que edad calculada)
                fecha_nac = self._safe_date(
                    primera_fila.get(Columns.FECHA_NACIMIENTO.name)
                )
                evento_dict["fecha_nacimiento"] = fecha_nac

                # Actualizar establecimientos con los valores priorizados
                if estab_consulta_final:
                    evento_dict["id_establecimiento_consulta"] = (
                        establecimiento_mapping.get(estab_consulta_final)
                    )
                if estab_notif_final:
                    evento_dict["id_establecimiento_notificacion"] = (
                        establecimiento_mapping.get(estab_notif_final)
                    )
                if estab_carga_final:
                    evento_dict["id_establecimiento_carga"] = (
                        establecimiento_mapping.get(estab_carga_final)
                    )

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
                eventos_grupos_data.append(
                    {"id_evento_caso": id_evento_caso, "id_grupo_eno": id_grupo}
                )

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
                relaciones_eventos_grupos.append(
                    {
                        "id_evento": int(id_evento),  # Convertir numpy.int64 → int
                        "id_grupo_eno": int(
                            id_grupo_eno
                        ),  # Convertir numpy.int64 → int
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if relaciones_eventos_grupos:
            stmt = pg_insert(EventoGrupoEno.__table__).values(relaciones_eventos_grupos)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=["id_evento", "id_grupo_eno"]
            )
            self.context.session.execute(upsert_stmt)
            eventos_unicos = len(set(r["id_evento"] for r in relaciones_eventos_grupos))
            self.logger.info(
                f"{len(relaciones_eventos_grupos)} relaciones evento-grupo creadas "
                f"({eventos_unicos} eventos con uno o más grupos)"
            )

        return evento_mapping

    def _get_or_create_domicilio(self, row: pd.Series) -> Optional[int]:
        """
        Get or create an immutable domicilio record.

        Returns:
            ID of the domicilio, or None if no valid address data
        """
        from app.domains.territorio.geografia_models import Domicilio
        from decimal import Decimal

        # Extraer datos de dirección del CSV
        calle = self._clean_string(row.get(Columns.CALLE_DOMICILIO.name))
        numero = self._clean_string(row.get(Columns.NUMERO_DOMICILIO.name))
        id_localidad_indec = self._safe_int(
            row.get(Columns.ID_LOC_INDEC_RESIDENCIA.name)
        )

        # VALIDACIÓN CRÍTICA: Verificar que la calle sea válida
        if not is_valid_street_name(calle):
            self.logger.debug(
                f"🚫 Domicilio rechazado: calle inválida '{calle}' "
                f"(numero={numero}, id_localidad={id_localidad_indec})"
            )
            return None

        # Requiere al menos localidad
        if not id_localidad_indec:
            return None

        try:
            # Buscar domicilio existente (UNIQUE constraint: calle, numero, id_localidad_indec)
            # NOTA: Usar .first() en lugar de .scalar_one_or_none() para manejar duplicados
            # (pueden existir duplicados legacy antes del UNIQUE constraint)
            stmt = select(Domicilio.id).where(
                Domicilio.calle == calle,
                Domicilio.numero == numero,
                Domicilio.id_localidad_indec == id_localidad_indec,
            )
            existing_domicilio = self.context.session.execute(stmt).scalars().first()

            if existing_domicilio:
                # Domicilio ya existe, retornar ID del primero encontrado
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
                    localidad = self._clean_string(
                        row.get(Columns.LOCALIDAD_RESIDENCIA.name)
                    )
                    provincia = self._clean_string(
                        row.get(Columns.PROVINCIA_RESIDENCIA.name)
                    )

                    geocoding_result = self.geocoding_service.geocode_address(
                        calle=calle,
                        numero=numero,
                        localidad=localidad,
                        provincia=provincia,
                        id_localidad_indec=id_localidad_indec,
                    )

                    if geocoding_result:
                        latitud = (
                            Decimal(str(geocoding_result.latitud))
                            if geocoding_result.latitud
                            else None
                        )
                        longitud = (
                            Decimal(str(geocoding_result.longitud))
                            if geocoding_result.longitud
                            else None
                        )
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
            estab_consulta = self._clean_string(row.get(Columns.ESTAB_CLINICA.name))
            estab_notificacion = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_EPI.name)
            )
            estab_carga = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_CARGA.name)
            )

            # Obtener tipo ENO desde el nombre del evento
            evento_nombre = self._clean_string(row.get(Columns.EVENTO.name))
            # Convertir nombre a código kebab-case para buscar en el mapping
            evento_codigo = (
                CodigoGenerator.generar_codigo_kebab(evento_nombre)
                if evento_nombre
                else None
            )
            id_tipo_eno = tipo_mapping.get(evento_codigo)

            # No debería fallar ya que creamos todos los tipos dinámicamente
            if not id_tipo_eno:
                # Esto solo podría pasar si el evento es None/vacío
                return None

            # Obtener grupo ENO desde el nombre del grupo
            grupo_nombre = self._clean_string(row.get(Columns.GRUPO_EVENTO.name))
            grupo_codigo = (
                CodigoGenerator.generar_codigo_kebab(grupo_nombre)
                if grupo_nombre
                else None
            )
            id_grupo_eno = grupo_mapping.get(grupo_codigo)

            if not id_grupo_eno:
                # Log para debugging - esto no debería ocurrir pero hay que investigar
                self.logger.warning(
                    f"⚠️  No se encontró grupo ENO para código '{grupo_codigo}' (nombre: '{grupo_nombre}'). "
                    f"Grupos disponibles: {list(grupo_mapping.keys())[:5]}... "
                    f"Este evento NO se insertará."
                )
                return None

            # Usar resultado del clasificador - siempre debe haber uno
            clasificacion_estrategia = row.get("clasificacion_estrategia")
            if (
                pd.isna(clasificacion_estrategia)
                or not str(clasificacion_estrategia).strip()
            ):
                # Si no hay clasificación del classifier, marcar como requiere revisión
                from app.domains.eventos_epidemiologicos.clasificacion.models import (
                    TipoClasificacion,
                )

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
                "id_evento_caso": self._safe_int(row.get(Columns.IDEVENTOCASO.name)),
                "codigo_ciudadano": self._safe_int(
                    row.get(Columns.CODIGO_CIUDADANO.name)
                ),
                "fecha_inicio_sintomas": self._safe_date(
                    row.get(Columns.FECHA_INICIO_SINTOMA.name)
                ),
                "clasificacion_estrategia": clasificacion_estrategia,
                "id_estrategia_aplicada": (
                    self._safe_int(id_estrategia_aplicada)
                    if pd.notna(id_estrategia_aplicada)
                    else None
                ),
                "trazabilidad_clasificacion": (
                    trazabilidad_clasificacion
                    if pd.notna(trazabilidad_clasificacion)
                    else None
                ),
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
