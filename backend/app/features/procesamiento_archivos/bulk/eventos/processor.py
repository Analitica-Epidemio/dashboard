"""Bulk processor for events and related entities - Optimizado con Polars puro."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import os

import polars as pl
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
from ..shared import (
    BulkProcessorBase,
    BulkOperationResult,
    get_or_create_catalog,
    is_valid_street_name,
    pl_safe_int,
    pl_safe_date,
    pl_clean_string,
    pl_clean_numero_domicilio,
)


class EventosProcessor(BulkProcessorBase):
    """Handles event-related bulk operations with Polars optimization."""

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

    def _get_or_create_grupos_eno(self, df: pl.DataFrame) -> dict[str, int]:
        """Get or create grupo ENO entries using generic pattern with CodigoGenerator."""

        # DEBUG: Ver qué grupos tenemos en el CSV
        grupos_unicos = df[Columns.GRUPO_EVENTO.name].drop_nulls().unique().to_list()
        self.logger.info(
            f"🔍 DEBUG: Grupos únicos en CSV ({len(grupos_unicos)}): {grupos_unicos[:10]}"
        )

        def transform_grupo(valor: str) -> dict:
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
        self, df: pl.DataFrame, grupo_mapping: dict[str, int]
    ) -> tuple[dict[str, int], dict[int, set]]:
        """
        Get or create tipo ENO entries from DataFrame - OPTIMIZADO con Polars.

        Returns:
            Tuple of:
            - Dict mapping tipo_codigo -> tipo_id
            - Dict mapping tipo_id -> set of grupo_ids
        """
        # OPTIMIZACIÓN: Extraer tipos únicos usando Polars lazy
        tipos_df = (
            df.lazy()
            .select([
                pl_clean_string(Columns.EVENTO.name).alias("evento_clean")
            ])
            .filter(pl.col("evento_clean").is_not_null())
            .unique()
            .collect()
        )

        if tipos_df.height == 0:
            return {}, {}

        tipos_unicos = tipos_df["evento_clean"].to_list()

        # Generar códigos usando vectorización de Polars
        tipo_data_list = []
        for tipo_str in tipos_unicos:
            if tipo_str:
                codigo = CodigoGenerator.generar_codigo_kebab(tipo_str)
                tipo_data_list.append({
                    "tipo_str": tipo_str,
                    "codigo": codigo
                })

        if not tipo_data_list:
            return {}, {}

        # Crear DataFrame de tipos para procesamiento
        tipos_codes_df = pl.DataFrame(tipo_data_list)
        tipos_set = set(tipos_codes_df["codigo"].to_list())

        # Verificar existentes por código
        stmt = select(TipoEno.id, TipoEno.codigo).where(
            TipoEno.codigo.in_(list(tipos_set))
        )
        existing_mapping = {
            codigo: tipo_id
            for tipo_id, codigo in self.context.session.execute(stmt).all()
        }

        # Identificar nuevos tipos
        nuevos_tipos = []
        for row in tipo_data_list:
            tipo_codigo = row["codigo"]
            if tipo_codigo not in existing_mapping:
                nombre_original = row["tipo_str"]
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

        # OPTIMIZACIÓN: Construir mapping tipo-grupo usando Polars puro
        tipo_grupos_mapping: dict[int, set] = {}

        # Preparar DataFrame con tipos y grupos limpios
        tipo_grupo_df = (
            df.lazy()
            .select([
                pl_clean_string(Columns.EVENTO.name).alias("evento_clean"),
                pl_clean_string(Columns.GRUPO_EVENTO.name).alias("grupo_clean")
            ])
            .filter(
                pl.col("evento_clean").is_not_null() &
                pl.col("grupo_clean").is_not_null()
            )
            .unique()
            .collect()
        )

        if tipo_grupo_df.height > 0:
            # Convertir a lista de dicts para procesamiento
            from collections import defaultdict
            tipo_grupos_temp = defaultdict(set)

            for row_dict in tipo_grupo_df.to_dicts():
                evento_clean = row_dict["evento_clean"]
                grupo_clean = row_dict["grupo_clean"]

                tipo_codigo = CodigoGenerator.generar_codigo_kebab(evento_clean)
                grupo_codigo = CodigoGenerator.generar_codigo_kebab(grupo_clean)

                tipo_id = existing_mapping.get(tipo_codigo)
                grupo_id = grupo_mapping.get(grupo_codigo)

                if tipo_id and grupo_id:
                    tipo_grupos_temp[tipo_id].add(grupo_id)

            tipo_grupos_mapping = dict(tipo_grupos_temp)

            # Crear relaciones tipo-grupo en la tabla de unión
            from app.domains.eventos_epidemiologicos.eventos.models import TipoEnoGrupoEno

            timestamp = self._get_current_timestamp()
            relaciones_tipo_grupo = []
            for tipo_id, grupos_ids in tipo_grupos_mapping.items():
                for grupo_id in grupos_ids:
                    relaciones_tipo_grupo.append(
                        {
                            "id_tipo_eno": int(tipo_id),
                            "id_grupo_eno": int(grupo_id),
                            "created_at": timestamp,
                            "updated_at": timestamp,
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

    def _bulk_load_domicilios(self, agg_results: pl.DataFrame) -> dict[int, Optional[int]]:
        """
        Bulk load de domicilios - elimina N+1 queries.

        OPTIMIZACIÓN: En lugar de hacer 1 SELECT por evento (N+1 problem),
        hace 1 SELECT para todos los domicilios necesarios.

        Args:
            agg_results: DataFrame agregado con datos de eventos

        Returns:
            Dict mapping id_evento_caso -> id_domicilio
        """
        from app.domains.territorio.geografia_models import Domicilio

        # 1. Extraer domicilios únicos del DataFrame agregado
        domicilios_df = (
            agg_results.lazy()
            .select([
                pl.col(Columns.IDEVENTOCASO.name),
                pl.col("calle_domicilio"),
                pl.col("numero_domicilio"),
                pl.col("id_localidad_indec"),
                pl.col("localidad_residencia"),
                pl.col("provincia_residencia"),
            ])
            # Limpiar y normalizar claves para matchear con tabla domicilio
            .with_columns([
                pl_clean_string("calle_domicilio").alias("calle_domicilio_clean"),
                pl_clean_numero_domicilio("numero_domicilio").alias("numero_domicilio_clean"),
                pl.col("id_localidad_indec").cast(pl.Int64, strict=False).alias("id_localidad_indec_int"),
            ])
            .collect()
        )

        # 2. Validar calles y filtrar inválidas
        domicilios_validos = []
        evento_to_domicilio = {}  # id_evento_caso -> (calle, numero, id_localidad)

        for row_dict in domicilios_df.to_dicts():
            id_evento_caso = row_dict[Columns.IDEVENTOCASO.name]
            calle = row_dict.get("calle_domicilio_clean")
            numero = row_dict.get("numero_domicilio_clean")
            id_localidad = row_dict.get("id_localidad_indec_int")

            # Validar
            if not is_valid_street_name(calle) or not id_localidad:
                evento_to_domicilio[id_evento_caso] = None
                continue

            domicilio_key = (calle, numero, id_localidad)
            evento_to_domicilio[id_evento_caso] = domicilio_key
            domicilios_validos.append(domicilio_key)

        if not domicilios_validos:
            return evento_to_domicilio

        # 3. Bulk SELECT de domicilios existentes (1 query para todos)
        domicilios_unicos = list(set(domicilios_validos))
        localidades_ids = list(set(d[2] for d in domicilios_unicos))

        # Query todos los domicilios de estas localidades
        stmt = select(
            Domicilio.id,
            Domicilio.calle,
            Domicilio.numero,
            Domicilio.id_localidad_indec
        ).where(
            Domicilio.id_localidad_indec.in_(localidades_ids)
        )

        existing_domicilios = {}
        for dom_id, calle, numero, id_loc in self.context.session.execute(stmt).all():
            key = (
                (calle.strip() if isinstance(calle, str) else calle),
                (numero.strip() if isinstance(numero, str) else numero),
                int(id_loc) if id_loc is not None else None,
            )
            existing_domicilios[key] = dom_id

        # 4. Identificar nuevos domicilios a crear
        nuevos_domicilios = []
        timestamp = self._get_current_timestamp()

        for domicilio_key in domicilios_unicos:
            if domicilio_key not in existing_domicilios:
                calle, numero, id_localidad = domicilio_key
                nuevos_domicilios.append({
                    "calle": calle,
                    "numero": numero,
                    "id_localidad_indec": id_localidad,
                    # estado_geocodificacion usa el default (PENDIENTE) del modelo
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

        # 5. Batch insert de nuevos domicilios
        if nuevos_domicilios:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            stmt = pg_insert(Domicilio.__table__).values(nuevos_domicilios)
            upsert_stmt = stmt.on_conflict_do_nothing(
                index_elements=["calle", "numero", "id_localidad_indec"]
            )
            self.context.session.execute(upsert_stmt)
            self.context.session.flush()

            # Re-query para obtener los IDs de los recién insertados
            stmt = select(
                Domicilio.id,
                Domicilio.calle,
                Domicilio.numero,
                Domicilio.id_localidad_indec
            ).where(
                Domicilio.id_localidad_indec.in_(localidades_ids)
            )

            existing_domicilios = {}
            for dom_id, calle, numero, id_loc in self.context.session.execute(stmt).all():
                key = (
                    (calle.strip() if isinstance(calle, str) else calle),
                    (numero.strip() if isinstance(numero, str) else numero),
                    int(id_loc) if id_loc is not None else None,
                )
                existing_domicilios[key] = dom_id

        # 6. Mapear id_evento_caso -> id_domicilio
        result = {}
        for id_evento_caso, domicilio_key in evento_to_domicilio.items():
            if domicilio_key is None:
                result[id_evento_caso] = None
            else:
                result[id_evento_caso] = existing_domicilios.get(domicilio_key)

        if result:
            matches = sum(1 for dom_id in result.values() if dom_id is not None)
            self.logger.debug(
                f"📍 Domicilios mapeados para eventos: {matches}/{len(result)} "
                f"({len(domicilios_unicos)} domicilios únicos preprocesados)"
            )
            if matches == 0:
                self.logger.warning(
                    "⚠️  No se pudo mapear ningún domicilio a eventos. "
                    "Verificar normalización de columnas CALLE/NUMERO/ID_LOCALIDAD en el CSV."
                )

        return result

    def _build_establecimiento_mapping_expr(
        self, establecimiento_mapping: dict[str, int], col_name: str
    ) -> pl.Expr:
        """
        Build Polars expression to map establecimiento names to IDs.

        Args:
            establecimiento_mapping: Dict of establecimiento_clean -> id
            col_name: Column name to map

        Returns:
            Polars expression that maps the column to establecimiento IDs
        """
        # Create when/then chain for mapping
        expr = pl.lit(None, dtype=pl.Int64)
        for estab_name, estab_id in establecimiento_mapping.items():
            expr = pl.when(pl.col(col_name) == estab_name).then(pl.lit(estab_id)).otherwise(expr)
        return expr

    def upsert_eventos(
        self, df: pl.DataFrame, establecimiento_mapping: dict[str, int]
    ) -> dict[int, int]:
        """
        Bulk upsert de eventos principales - OPTIMIZADO con Polars lazy evaluation.

        OPTIMIZACIONES PRINCIPALES:
        - Lazy evaluation para todo el procesamiento
        - Agregaciones vectorizadas con group_by
        - JOINs en lugar de loops para mapeo de IDs
        - Expresiones Polars para transformaciones
        """
        self.logger.info(f"🏥 Recibido mapping de establecimientos: {len(establecimiento_mapping)} establecimientos")
        if establecimiento_mapping and len(establecimiento_mapping) <= 5:
            self.logger.info(f"   Ejemplos: {list(establecimiento_mapping.keys())[:5]}")

        if df.height == 0:
            return {}

        self.logger.info(f"Procesando {df.height} filas de eventos")

        # Primero crear grupos y tipos ENO
        grupo_mapping = self._get_or_create_grupos_eno(df)
        tipo_mapping, tipo_grupos_mapping = self._get_or_create_tipos_eno(
            df, grupo_mapping
        )

        self.logger.info(
            f"Creados/verificados {len(grupo_mapping)} grupos ENO y {len(tipo_mapping)} tipos ENO"
        )

        # Contar eventos únicos
        grupos_unicos = df[Columns.IDEVENTOCASO.name].drop_nulls().n_unique()
        self.logger.info(
            f"Procesando {grupos_unicos} eventos únicos de {df.height} filas totales"
        )

        # OPTIMIZACIÓN CLAVE: Usar lazy evaluation para todas las transformaciones
        # Crear mappings como DataFrames para hacer JOINs

        # 1. Crear DataFrame de mapping de grupos
        grupo_mapping_df = pl.DataFrame({
            "grupo_nombre_clean": list(grupo_mapping.keys()),
            "grupo_id": list(grupo_mapping.values())
        })

        # 2. Crear DataFrame de mapping de tipos
        tipo_mapping_df = pl.DataFrame({
            "tipo_codigo": list(tipo_mapping.keys()),
            "tipo_id": list(tipo_mapping.values())
        })

        # 3. OPTIMIZACIÓN: Pre-calcular códigos kebab UNA SOLA VEZ (elimina map_elements)
        # Crear DataFrame con valores limpios
        df_cleaned = (
            df.lazy()
            .with_columns([
                # Limpiar strings de establecimientos
                pl_clean_string(Columns.ESTAB_CLINICA.name).alias("estab_consulta_clean"),
                pl_clean_string(Columns.ESTABLECIMIENTO_EPI.name).alias("estab_notif_clean"),
                pl_clean_string(Columns.ESTABLECIMIENTO_CARGA.name).alias("estab_carga_clean"),

                # Limpiar grupo y evento
                pl_clean_string(Columns.GRUPO_EVENTO.name).alias("grupo_nombre_clean"),
                pl_clean_string(Columns.EVENTO.name).alias("evento_nombre_clean"),
            ])
            .collect()
        )

        # Extraer valores únicos LIMPIOS y generar códigos (solo para valores únicos)
        grupos_unicos = df_cleaned["grupo_nombre_clean"].drop_nulls().unique().to_list()
        eventos_unicos = df_cleaned["evento_nombre_clean"].drop_nulls().unique().to_list()

        # Generar códigos solo para valores únicos (no para cada fila)
        # Ahora el mapping usa los valores limpios como keys
        grupo_kebab_map = {g: CodigoGenerator.generar_codigo_kebab(g)
                           for g in grupos_unicos if g}
        evento_kebab_map = {e: CodigoGenerator.generar_codigo_kebab(e)
                            for e in eventos_unicos if e}

        # Aplicar mapping vectorizado
        df_prepared = (
            df_cleaned.lazy()
            .with_columns([
                # Mapear a códigos usando replace (VECTORIZADO en Rust, no Python loop)
                pl.col("grupo_nombre_clean").replace(grupo_kebab_map, default=None).alias("grupo_codigo"),
                pl.col("evento_nombre_clean").replace(evento_kebab_map, default=None).alias("tipo_codigo"),
            ])
            .collect()
        )

        # 4. JOIN con mappings para obtener IDs
        df_with_ids = (
            df_prepared.lazy()
            # Join grupo
            .join(
                grupo_mapping_df.lazy(),
                left_on="grupo_codigo",
                right_on="grupo_nombre_clean",
                how="left"
            )
            # Join tipo
            .join(
                tipo_mapping_df.lazy(),
                on="tipo_codigo",
                how="left"
            )
            .collect()
        )

        # 5. AGREGACIÓN VECTORIZADA: Calcular valores por id_evento_caso
        # OPTIMIZACIÓN: Incluir datos de domicilio en agregación para evitar filtros posteriores
        agg_results = (
            df_with_ids.lazy()
            .group_by(Columns.IDEVENTOCASO.name)
            .agg([
                # Fechas: tomar la mínima de cada columna
                pl.col(Columns.FECHA_APERTURA.name).min().alias("fecha_apertura_min"),
                pl.col(Columns.FECHA_INICIO_SINTOMA.name).min().alias("fecha_inicio_sintoma_min"),
                pl.col(Columns.FECHA_CONSULTA.name).min().alias("fecha_consulta_min"),
                pl.col(Columns.FTM.name).min().alias("ftm_min"),

                # Establecimientos: tomar el primer valor no nulo
                pl.col("estab_consulta_clean").drop_nulls().first().alias("estab_consulta_final"),
                pl.col("estab_notif_clean").drop_nulls().first().alias("estab_notif_final"),
                pl.col("estab_carga_clean").drop_nulls().first().alias("estab_carga_final"),

                # Grupos ENO: recolectar TODOS los IDs únicos
                pl.col("grupo_id").drop_nulls().unique().alias("grupos_ids"),

                # Tipo ENO: tomar el primero (debería ser único por evento)
                pl.col("tipo_id").drop_nulls().first().alias("tipo_id"),

                # Tomar primera fila de datos base para campos que no se agregan
                pl.col(Columns.CODIGO_CIUDADANO.name).first().alias("codigo_ciudadano_first"),
                pl.col(Columns.FECHA_NACIMIENTO.name).first().alias("fecha_nacimiento_first"),

                # Campos de clasificación
                pl.col("clasificacion_estrategia").first().alias("clasificacion_estrategia_first"),
                pl.col("id_estrategia_aplicada").first().alias("id_estrategia_aplicada_first"),
                pl.col("trazabilidad_clasificacion").first().alias("trazabilidad_clasificacion_first"),

                # OPTIMIZACIÓN: Incluir datos de domicilio en la agregación
                pl.col(Columns.CALLE_DOMICILIO.name).first().alias("calle_domicilio"),
                pl.col(Columns.NUMERO_DOMICILIO.name).first().alias("numero_domicilio"),
                pl.col(Columns.ID_LOC_INDEC_RESIDENCIA.name).first().alias("id_localidad_indec"),
                pl.col(Columns.LOCALIDAD_RESIDENCIA.name).first().alias("localidad_residencia"),
                pl.col(Columns.PROVINCIA_RESIDENCIA.name).first().alias("provincia_residencia"),

                # Contar filas para debug
                pl.count().alias("num_filas"),
            ])
            .collect()
        )

        # 6. OPTIMIZACIÓN: Bulk load de domicilios (elimina N+1 queries)
        # Pre-cargar todos los domicilios existentes que necesitamos
        domicilios_map = self._bulk_load_domicilios(agg_results)

        # 7. Procesar eventos y construir eventos_data
        timestamp = self._get_current_timestamp()
        eventos_data = []
        eventos_grupos_data = []

        for agg_row in agg_results.to_dicts():
            id_evento_caso = agg_row[Columns.IDEVENTOCASO.name]
            if not id_evento_caso:
                continue

            # Calcular fecha_minima_evento: la mínima de las 4 columnas
            fechas_candidatas = [
                agg_row.get("fecha_apertura_min"),
                agg_row.get("fecha_inicio_sintoma_min"),
                agg_row.get("fecha_consulta_min"),
                agg_row.get("ftm_min"),
            ]
            fechas_validas = [f for f in fechas_candidatas if f is not None]

            if not fechas_validas:
                # Log warning para eventos sin fecha
                self.logger.warning(
                    f"⚠️  Evento {id_evento_caso}: no tiene ninguna fecha válida. "
                    f"Se insertará con fecha_minima_evento = NULL (requiere revisión manual)."
                )
                fecha_minima_evento = None
            else:
                fecha_minima_evento = min(fechas_validas)

            # Fecha de inicio de síntomas más temprana
            fecha_inicio_sintomas_mas_temprana = agg_row.get("fecha_inicio_sintoma_min")

            # Obtener tipo_id
            id_tipo_eno = agg_row.get("tipo_id")
            if not id_tipo_eno:
                # Sin tipo, skip este evento
                continue

            # Obtener grupos
            grupos_ids = agg_row.get("grupos_ids", [])
            if not grupos_ids:
                self.logger.warning(f"⚠️  Evento {id_evento_caso}: sin grupo ENO. Se omitirá.")
                continue

            # OPTIMIZACIÓN: Lookup de domicilio en dict (O(1) en lugar de query)
            id_domicilio = domicilios_map.get(id_evento_caso)

            # Mapear establecimientos usando el mapping
            id_estab_consulta = None
            id_estab_notif = None
            id_estab_carga = None

            estab_consulta_final = agg_row.get("estab_consulta_final")
            estab_notif_final = agg_row.get("estab_notif_final")
            estab_carga_final = agg_row.get("estab_carga_final")

            if estab_consulta_final:
                id_estab_consulta = establecimiento_mapping.get(estab_consulta_final)
            if estab_notif_final:
                id_estab_notif = establecimiento_mapping.get(estab_notif_final)
            if estab_carga_final:
                id_estab_carga = establecimiento_mapping.get(estab_carga_final)

            # Procesar clasificación
            clasificacion_estrategia = agg_row.get("clasificacion_estrategia_first")
            if clasificacion_estrategia is None or not str(clasificacion_estrategia).strip():
                from app.domains.eventos_epidemiologicos.clasificacion.models import TipoClasificacion
                clasificacion_estrategia = TipoClasificacion.REQUIERE_REVISION

            # Calcular semanas epidemiológicas
            semana_epidemiologica_apertura = None
            anio_epidemiologico_apertura = None
            semana_epidemiologica_sintomas = None

            if fecha_minima_evento:
                # Convertir a date si es datetime
                if hasattr(fecha_minima_evento, "date"):
                    fecha_minima_date = fecha_minima_evento.date()
                elif isinstance(fecha_minima_evento, date):
                    fecha_minima_date = fecha_minima_evento
                else:
                    fecha_minima_date = fecha_minima_evento

                semana_epi, anio_epi = calcular_semana_epidemiologica(fecha_minima_date)
                semana_epidemiologica_apertura = semana_epi
                anio_epidemiologico_apertura = anio_epi

            if fecha_inicio_sintomas_mas_temprana:
                if hasattr(fecha_inicio_sintomas_mas_temprana, "date"):
                    fecha_sintomas_date = fecha_inicio_sintomas_mas_temprana.date()
                elif isinstance(fecha_inicio_sintomas_mas_temprana, date):
                    fecha_sintomas_date = fecha_inicio_sintomas_mas_temprana
                else:
                    fecha_sintomas_date = fecha_inicio_sintomas_mas_temprana

                semana_sintomas, _ = calcular_semana_epidemiologica(fecha_sintomas_date)
                semana_epidemiologica_sintomas = semana_sintomas

            # Construir evento dict
            evento_dict = {
                "id_evento_caso": id_evento_caso,
                "codigo_ciudadano": agg_row.get("codigo_ciudadano_first"),
                "fecha_inicio_sintomas": fecha_inicio_sintomas_mas_temprana,
                "clasificacion_estrategia": clasificacion_estrategia,
                "id_estrategia_aplicada": agg_row.get("id_estrategia_aplicada_first"),
                "trazabilidad_clasificacion": agg_row.get("trazabilidad_clasificacion_first"),
                "fecha_minima_evento": fecha_minima_evento,
                "semana_epidemiologica_apertura": semana_epidemiologica_apertura,
                "anio_epidemiologico_apertura": anio_epidemiologico_apertura,
                "semana_epidemiologica_sintomas": semana_epidemiologica_sintomas,
                "fecha_nacimiento": agg_row.get("fecha_nacimiento_first"),
                "id_tipo_eno": id_tipo_eno,
                "id_establecimiento_consulta": id_estab_consulta,
                "id_establecimiento_notificacion": id_estab_notif,
                "id_establecimiento_carga": id_estab_carga,
                "id_domicilio": id_domicilio,
                "created_at": timestamp,
                "updated_at": timestamp,
            }

            eventos_data.append(evento_dict)

            # Preparar relaciones evento-grupo
            for id_grupo in grupos_ids:
                eventos_grupos_data.append({
                    "id_evento_caso": id_evento_caso,
                    "id_grupo_eno": id_grupo
                })

            # Log para casos con muchas filas
            num_filas = agg_row.get("num_filas", 1)
            if num_filas > 10:
                self.logger.info(
                    f"Evento {id_evento_caso}: {num_filas} filas agregadas "
                    f"(fecha_minima: {fecha_minima_evento})"
                )

        if not eventos_data:
            return {}

        # Estadísticas de establecimientos asignados
        eventos_con_consulta = sum(1 for e in eventos_data if e.get("id_establecimiento_consulta") is not None)
        eventos_con_notif = sum(1 for e in eventos_data if e.get("id_establecimiento_notificacion") is not None)
        eventos_con_carga = sum(1 for e in eventos_data if e.get("id_establecimiento_carga") is not None)

        self.logger.info(
            f"Bulk upserting {len(eventos_data)} eventos únicos (de {df.height} filas totales)"
        )
        self.logger.info(
            f"📊 Establecimientos asignados: consulta={eventos_con_consulta}, "
            f"notificación={eventos_con_notif}, carga={eventos_con_carga}"
        )

        # PostgreSQL UPSERT
        stmt = pg_insert(Evento.__table__).values(eventos_data)

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
            "id_domicilio": stmt.excluded.id_domicilio,
            "updated_at": self._get_current_timestamp(),
        }

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

        timestamp_relaciones = self._get_current_timestamp()
        relaciones_eventos_grupos = []
        for eg_data in eventos_grupos_data:
            id_evento_caso = eg_data["id_evento_caso"]
            id_grupo_eno = eg_data["id_grupo_eno"]
            id_evento = evento_mapping.get(id_evento_caso)

            if id_evento and id_grupo_eno:
                relaciones_eventos_grupos.append(
                    {
                        "id_evento": int(id_evento),
                        "id_grupo_eno": int(id_grupo_eno),
                        "created_at": timestamp_relaciones,
                        "updated_at": timestamp_relaciones,
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

    def _get_or_create_domicilio(self, row: dict) -> Optional[int]:
        """
        Get or create an immutable domicilio record.

        Returns:
            ID of the domicilio, or None if no valid address data
        """
        from app.domains.territorio.geografia_models import Domicilio

        # Extraer datos de dirección del CSV usando helpers Polars si es posible
        # Nota: row es un dict de primera_fila_df, ya procesado
        calle = row.get(Columns.CALLE_DOMICILIO.name)
        numero = row.get(Columns.NUMERO_DOMICILIO.name)
        id_localidad_indec = row.get(Columns.ID_LOC_INDEC_RESIDENCIA.name)

        # Limpiar strings
        if calle is not None:
            calle = str(calle).strip() if str(calle).strip() else None
        if numero is not None:
            numero = str(numero).strip() if str(numero).strip() else None

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
            stmt = select(Domicilio.id).where(
                Domicilio.calle == calle,
                Domicilio.numero == numero,
                Domicilio.id_localidad_indec == id_localidad_indec,
            )
            existing_domicilio = self.context.session.execute(stmt).scalars().first()

            if existing_domicilio:
                return existing_domicilio

            # No existe, crear nuevo domicilio
            latitud = None
            longitud = None
            proveedor_geocoding = None
            confidence_geocoding = None
            geocodificado = False

            if self.geocoding_enabled and self.geocoding_service:
                try:
                    localidad = row.get(Columns.LOCALIDAD_RESIDENCIA.name)
                    provincia = row.get(Columns.PROVINCIA_RESIDENCIA.name)

                    if localidad is not None:
                        localidad = str(localidad).strip() if str(localidad).strip() else None
                    if provincia is not None:
                        provincia = str(provincia).strip() if str(provincia).strip() else None

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
