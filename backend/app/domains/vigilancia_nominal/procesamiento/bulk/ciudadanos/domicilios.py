"""Address and citizen-address link operations - Polars puro optimizado."""

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.domains.vigilancia_nominal.models.sujetos import CiudadanoDomicilio
from app.domains.territorio.geografia_models import Domicilio, Localidad

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    es_nombre_calle_valido,
    pl_clean_numero_domicilio,
    pl_clean_string,
    pl_safe_int,
)


class DomiciliosProcessor(BulkProcessorBase):
    """Handles address-related bulk operations."""

    def upsert_ciudadanos_domicilios(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert of addresses and citizen-address links - POLARS PURO.

        Simplified flow:
        1. Upsert unique addresses
        2. Trigger geocoding (if enabled)
        3. Create citizen-address links

        OPTIMIZACIONES:
        - Lazy evaluation para todo el filtrado
        - Expresiones Polars para limpieza de datos
        - Sin loops Python para transformaciones
        """
        tiempo_inicio = self._get_current_timestamp()

        # Filter records with valid address data
        df_domicilios = self._filtrar_domicilios_validos(df)
        if df_domicilios.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Step 1: Upsert unique addresses
        mapa_ids_domicilios = self._upsert_domicilios_unicos(df_domicilios)

        # Step 2: Trigger geocoding if enabled
        self._activar_geocodificacion_si_habilitada(len(mapa_ids_domicilios))

        # Step 3: Create citizen-address links
        conteo_vinculos = self._crear_vinculos_ciudadano_domicilio(
            df_domicilios, mapa_ids_domicilios
        )

        duracion = (self._get_current_timestamp() - tiempo_inicio).total_seconds()

        return BulkOperationResult(
            inserted_count=len(mapa_ids_domicilios),
            updated_count=conteo_vinculos,
            skipped_count=0,
            errors=[],
            duration_seconds=duracion,
        )

    def _filtrar_domicilios_validos(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Filter records with valid address data - POLARS PURO con lazy evaluation.

        Excluye domicilios que no son geocodificables:
        - Sin código de ciudadano
        - Sin localidad
        - Sin calle válida (ej: S/N, NO APLICA, etc.)
        """
        # LAZY EVALUATION - Filtro básico en Polars
        filtrado = (
            df.lazy()
            .filter(
                pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null()
                & pl.col(Columns.ID_LOC_INDEC_RESIDENCIA.name).is_not_null()
            )
            .collect()
        )

        # Aplicar validación de calle válida
        col_calle = Columns.CALLE_DOMICILIO.name
        if col_calle in filtrado.columns:
            # Convertir a lista para validar (es_nombre_calle_valido necesita valores Python)
            calles = filtrado.select(col_calle).to_series().to_list()
            mascara_calle_valida = [es_nombre_calle_valido(x) for x in calles]

            # Agregar columna de validación y filtrar - POLARS
            filtrado = filtrado.with_row_count("_row_idx")
            indices_validos = [i for i, valido in enumerate(mascara_calle_valida) if valido]
            filtrado = filtrado.filter(pl.col("_row_idx").is_in(indices_validos)).drop("_row_idx")

            # Log de registros filtrados
            registros_filtrados = df.height - filtrado.height
            if registros_filtrados > 0:
                self.logger.info(
                    f"📍 Filtrados {registros_filtrados} domicilios sin calle válida "
                    f"(S/N, NO APLICA, etc.)"
                )

        return filtrado

    def _upsert_domicilios_unicos(
        self, df_domicilios: pl.DataFrame
    ) -> dict[tuple, int]:
        """
        Create unique addresses and return mapping (street, number, locality) → id - POLARS PURO.

        OPTIMIZACIONES:
        - Lazy evaluation para extraer únicos
        - Expresión Polars para limpiar strings
        - Expresión Polars para limpiar número de domicilio

        Returns:
            {(calle, numero, localidad_id): domicilio_id}
        """
        # Ensure localities exist
        ids_localidad = (
            df_domicilios.filter(pl.col(Columns.ID_LOC_INDEC_RESIDENCIA.name).is_not_null())
            .select(Columns.ID_LOC_INDEC_RESIDENCIA.name)
            .unique()
            .to_series()
            .to_list()
        )
        mapeo_localidad = self._asegurar_localidades_existen(ids_localidad)

        # LAZY EVALUATION - Extract unique addresses
        domicilios_unicos = (
            df_domicilios.lazy()
            .select([
                Columns.CALLE_DOMICILIO.name,
                Columns.NUMERO_DOMICILIO.name,
                Columns.ID_LOC_INDEC_RESIDENCIA.name,
            ])
            .unique()
            .collect()
        )

        # POLARS PURO: Prepare data con expresiones
        timestamp = self._get_current_timestamp()

        # LAZY EVALUATION - Map locality IDs and prepare data
        domicilios_preparados = (
            domicilios_unicos.lazy()
            .select([
                pl_clean_string(Columns.CALLE_DOMICILIO.name).alias("calle"),
                pl_clean_numero_domicilio(Columns.NUMERO_DOMICILIO.name).alias("numero"),
                pl_safe_int(Columns.ID_LOC_INDEC_RESIDENCIA.name).alias("id_localidad_raw"),
            ])
            .collect()
        )

        # Convert to dicts para post-processing (validación y mapeo de localidad)
        datos_domicilios_raw = domicilios_preparados.to_dicts()

        # Post-process: validate and clean
        datos_domicilios = []
        conteo_saltados_invalidos = 0
        for registro in datos_domicilios_raw:
            calle_val = registro["calle"]
            numero_val = registro["numero"]
            id_localidad_raw = registro["id_localidad_raw"]

            # Map localidad
            id_localidad = mapeo_localidad.get(id_localidad_raw) if id_localidad_raw else None
            if not id_localidad:
                continue

            # VALIDACIÓN CRÍTICA: No crear domicilio si la calle no es válida
            if not es_nombre_calle_valido(calle_val):
                conteo_saltados_invalidos += 1
                self.logger.debug(
                    f"🚫 Skipping invalid calle: '{calle_val}' (numero={numero_val})"
                )
                continue

            datos_domicilios.append({
                "calle": calle_val,
                "numero": numero_val,
                "id_localidad_indec": int(id_localidad),
                "created_at": timestamp,
                "updated_at": timestamp,
            })

        if conteo_saltados_invalidos > 0:
            self.logger.info(
                f"✅ Skipped {conteo_saltados_invalidos} domicilios with invalid calles"
            )

        if not datos_domicilios:
            return {}

        # DEBUG: Verificar tipos
        if datos_domicilios:
            muestra = datos_domicilios[0]
            self.logger.info(
                f"🔍 DEBUG domicilio sample: calle={muestra.get('calle')} ({type(muestra.get('calle')).__name__}), "
                f"numero={muestra.get('numero')} ({type(muestra.get('numero')).__name__}), "
                f"id_localidad_indec={muestra.get('id_localidad_indec')} ({type(muestra.get('id_localidad_indec')).__name__})"
            )

        # UPSERT addresses
        stmt = pg_insert(Domicilio.__table__).values(datos_domicilios)
        upsert_stmt = stmt.on_conflict_do_nothing(
            index_elements=["calle", "numero", "id_localidad_indec"]
        )

        try:
            self.context.session.execute(upsert_stmt)
            self.context.session.flush()
        except Exception as e:
            self.logger.error(f"Failed to insert domicilios: {e}")
            raise e

        # Get IDs of created/existing addresses
        from sqlalchemy import tuple_

        llaves_domicilios = [
            (d["calle"], d["numero"], d["id_localidad_indec"])
            for d in datos_domicilios
        ]

        stmt = select(
            Domicilio.id,
            Domicilio.calle,
            Domicilio.numero,
            Domicilio.id_localidad_indec,
        ).where(
            tuple_(Domicilio.calle, Domicilio.numero, Domicilio.id_localidad_indec).in_(
                llaves_domicilios
            )
        )

        resultados = self.context.session.execute(stmt).all()

        return {
            (fila.calle, fila.numero, fila.id_localidad_indec): fila.id for fila in resultados
        }

    def _activar_geocodificacion_si_habilitada(self, conteo_domicilios: int) -> None:
        """Queue geocoding task if enabled."""
        if not settings.ENABLE_GEOCODING:
            self.logger.debug(
                "📍 Geocodificación deshabilitada en settings (ENABLE_GEOCODING=false)"
            )
            return

        if conteo_domicilios <= 0:
            self.logger.debug("📍 No hay domicilios para geocodificar")
            return

        self.logger.info(
            f"🗺️  GEOCODIFICACIÓN ACTIVADA: Encolando {conteo_domicilios} domicilios para geocodificar"
        )
        self.logger.info(
            "   🔄 Los domicilios serán geocodificados en background por Celery (cola 'geocoding')"
        )
        self.logger.info(
            "   ⏱️  Procesamiento iniciará en 5 segundos (después del commit de DB)"
        )

        from app.domains.territorio.geocoding_tasks import geocode_pending_domicilios

        try:
            # 5 second delay so commit finishes first
            resultado_tarea = geocode_pending_domicilios.apply_async(countdown=5)
            self.logger.info(
                f"   ✅ Tarea de geocodificación encolada exitosamente (task_id: {resultado_tarea.id})"
            )
            self.logger.info(
                "   📊 Para monitorear: celery -A app.core.celery_app inspect active"
            )
        except Exception as e:
            self.logger.error(f"   ❌ Error encolando tarea de geocodificación: {e}")
            self.logger.error(
                "   ⚠️  Verifica que Redis y Celery worker estén corriendo"
            )

    def _crear_vinculos_ciudadano_domicilio(
        self, df_domicilios: pl.DataFrame, mapa_ids_domicilios: dict[tuple, int]
    ) -> int:
        """
        Create links between citizens and addresses - POLARS PURO.

        OPTIMIZACIONES:
        - Lazy evaluation para preparar datos
        - Expresiones Polars para limpiar número

        Returns:
            Number of links created
        """
        # LAZY EVALUATION - Prepare clean data con expresiones Polars
        df_preparado = (
            df_domicilios.lazy()
            .select([
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                pl_clean_string(Columns.CALLE_DOMICILIO.name).alias("calle_clean"),
                pl_clean_numero_domicilio(Columns.NUMERO_DOMICILIO.name).alias("numero_clean"),
                pl_safe_int(Columns.ID_LOC_INDEC_RESIDENCIA.name).alias("localidad_id"),
            ])
            .collect()
        )

        # Convert to dicts for lookup
        datos_vinculos_raw = df_preparado.to_dicts()

        # Post-process: map to domicilio IDs
        timestamp = self._get_current_timestamp()
        datos_vinculos = []
        for registro in datos_vinculos_raw:
            codigo_ciudadano = registro["codigo_ciudadano"]
            calle_clean = registro["calle_clean"]
            numero_clean = registro["numero_clean"]
            localidad_id = registro["localidad_id"]

            # Lookup domicilio ID
            id_domicilio = mapa_ids_domicilios.get((calle_clean, numero_clean, localidad_id))

            # Only create link if both ciudadano and domicilio are valid
            if codigo_ciudadano and id_domicilio:
                datos_vinculos.append({
                    "codigo_ciudadano": codigo_ciudadano,
                    "id_domicilio": id_domicilio,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

        if not datos_vinculos:
            return 0

        stmt = pg_insert(CiudadanoDomicilio.__table__).values(datos_vinculos)
        upsert_stmt = stmt.on_conflict_do_nothing()

        try:
            self.context.session.execute(upsert_stmt)
        except Exception as e:
            self.logger.error(f"Failed to insert ciudadano_domicilio: {e}")
            raise e

        return len(datos_vinculos)

    def _asegurar_localidades_existen(self, ids_localidad: list) -> dict[int, int]:
        """
        Ensure that all needed localities exist in the database.
        Creates placeholder localities for missing ones to avoid losing data.

        Returns mapping from original id_localidad_indec -> actual id_localidad_indec in DB
        """
        if not ids_localidad:
            return {}

        # Get existing localities
        stmt = select(Localidad.id_localidad_indec).where(
            Localidad.id_localidad_indec.in_(ids_localidad)
        )
        existentes = set(
            id_loc for (id_loc,) in self.context.session.execute(stmt).all()
        )

        # Mapping: all existing ones map to themselves
        mapeo_localidad = {loc_id: loc_id for loc_id in existentes}

        # Create placeholders for missing ones
        faltantes = [loc_id for loc_id in ids_localidad if loc_id not in existentes]

        if faltantes:
            self.logger.warning(
                f"Creating {len(faltantes)} placeholder localities for missing IDs"
            )

            timestamp = self._get_current_timestamp()
            placeholders = []
            for loc_id in faltantes:
                placeholders.append(
                    {
                        "id_localidad_indec": loc_id,
                        "nombre": f"Localidad INDEC {loc_id}",
                        "latitud": None,
                        "longitud": None,
                        "id_departamento_indec": None,  # Sin departamento conocido
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                )

            # Insert placeholders
            if placeholders:
                stmt = pg_insert(Localidad.__table__).values(placeholders)
                upsert_stmt = stmt.on_conflict_do_nothing(
                    index_elements=["id_localidad_indec"]
                )
                self.context.session.execute(upsert_stmt)

                # All map to themselves
                for loc_id in faltantes:
                    mapeo_localidad[loc_id] = loc_id

        return mapeo_localidad
