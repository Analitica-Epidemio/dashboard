"""Address and citizen-address link operations - Polars puro optimizado."""

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.domains.sujetos_epidemiologicos.ciudadanos_models import CiudadanoDomicilio
from app.domains.territorio.geografia_models import Domicilio, Localidad

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    is_valid_street_name,
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
        start_time = self._get_current_timestamp()

        # Filter records with valid address data
        domicilios_df = self._filter_valid_domicilios(df)
        if domicilios_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Step 1: Upsert unique addresses
        domicilios_ids_map = self._upsert_domicilios_unicos(domicilios_df)

        # Step 2: Trigger geocoding if enabled
        self._trigger_geocoding_if_enabled(len(domicilios_ids_map))

        # Step 3: Create citizen-address links
        vinculos_count = self._create_vinculos_ciudadano_domicilio(
            domicilios_df, domicilios_ids_map
        )

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(domicilios_ids_map),
            updated_count=vinculos_count,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    def _filter_valid_domicilios(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Filter records with valid address data - POLARS PURO con lazy evaluation.

        Excluye domicilios que no son geocodificables:
        - Sin código de ciudadano
        - Sin localidad
        - Sin calle válida (ej: S/N, NO APLICA, etc.)
        """
        # LAZY EVALUATION - Filtro básico en Polars
        filtered = (
            df.lazy()
            .filter(
                pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null()
                & pl.col(Columns.ID_LOC_INDEC_RESIDENCIA.name).is_not_null()
            )
            .collect()
        )

        # Aplicar validación de calle válida
        calle_col = Columns.CALLE_DOMICILIO.name
        if calle_col in filtered.columns:
            # Convertir a lista para validar (is_valid_street_name necesita valores Python)
            calles = filtered.select(calle_col).to_series().to_list()
            calle_valida_mask = [is_valid_street_name(x) for x in calles]

            # Agregar columna de validación y filtrar - POLARS
            filtered = filtered.with_row_count("_row_idx")
            valid_indices = [i for i, valid in enumerate(calle_valida_mask) if valid]
            filtered = filtered.filter(pl.col("_row_idx").is_in(valid_indices)).drop("_row_idx")

            # Log de registros filtrados
            records_filtered = df.height - filtered.height
            if records_filtered > 0:
                self.logger.info(
                    f"📍 Filtrados {records_filtered} domicilios sin calle válida "
                    f"(S/N, NO APLICA, etc.)"
                )

        return filtered

    def _upsert_domicilios_unicos(
        self, domicilios_df: pl.DataFrame
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
        localidad_ids = (
            domicilios_df.filter(pl.col(Columns.ID_LOC_INDEC_RESIDENCIA.name).is_not_null())
            .select(Columns.ID_LOC_INDEC_RESIDENCIA.name)
            .unique()
            .to_series()
            .to_list()
        )
        localidad_mapping = self._ensure_localidades_exist(localidad_ids)

        # LAZY EVALUATION - Extract unique addresses
        domicilios_unicos = (
            domicilios_df.lazy()
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
        domicilios_prepared = (
            domicilios_unicos.lazy()
            .select([
                pl_clean_string(Columns.CALLE_DOMICILIO.name).alias("calle"),
                pl_clean_numero_domicilio(Columns.NUMERO_DOMICILIO.name).alias("numero"),
                pl_safe_int(Columns.ID_LOC_INDEC_RESIDENCIA.name).alias("id_localidad_raw"),
            ])
            .collect()
        )

        # Convert to dicts para post-processing (validación y mapeo de localidad)
        domicilios_data_raw = domicilios_prepared.to_dicts()

        # Post-process: validate and clean
        domicilios_data = []
        skipped_invalid_count = 0
        for record in domicilios_data_raw:
            calle_val = record["calle"]
            numero_val = record["numero"]
            id_localidad_raw = record["id_localidad_raw"]

            # Map localidad
            id_localidad = localidad_mapping.get(id_localidad_raw) if id_localidad_raw else None
            if not id_localidad:
                continue

            # VALIDACIÓN CRÍTICA: No crear domicilio si la calle no es válida
            if not is_valid_street_name(calle_val):
                skipped_invalid_count += 1
                self.logger.debug(
                    f"🚫 Skipping invalid calle: '{calle_val}' (numero={numero_val})"
                )
                continue

            domicilios_data.append({
                "calle": calle_val,
                "numero": numero_val,
                "id_localidad_indec": int(id_localidad),
                "created_at": timestamp,
                "updated_at": timestamp,
            })

        if skipped_invalid_count > 0:
            self.logger.info(
                f"✅ Skipped {skipped_invalid_count} domicilios with invalid calles"
            )

        if not domicilios_data:
            return {}

        # DEBUG: Verificar tipos
        if domicilios_data:
            sample = domicilios_data[0]
            self.logger.info(
                f"🔍 DEBUG domicilio sample: calle={sample.get('calle')} ({type(sample.get('calle')).__name__}), "
                f"numero={sample.get('numero')} ({type(sample.get('numero')).__name__}), "
                f"id_localidad_indec={sample.get('id_localidad_indec')} ({type(sample.get('id_localidad_indec')).__name__})"
            )

        # UPSERT addresses
        stmt = pg_insert(Domicilio.__table__).values(domicilios_data)
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

        domicilios_keys = [
            (d["calle"], d["numero"], d["id_localidad_indec"])
            for d in domicilios_data
        ]

        stmt = select(
            Domicilio.id,
            Domicilio.calle,
            Domicilio.numero,
            Domicilio.id_localidad_indec,
        ).where(
            tuple_(Domicilio.calle, Domicilio.numero, Domicilio.id_localidad_indec).in_(
                domicilios_keys
            )
        )

        results = self.context.session.execute(stmt).all()

        return {
            (row.calle, row.numero, row.id_localidad_indec): row.id for row in results
        }

    def _trigger_geocoding_if_enabled(self, domicilios_count: int) -> None:
        """Queue geocoding task if enabled."""
        if not settings.ENABLE_GEOCODING:
            self.logger.debug(
                "📍 Geocodificación deshabilitada en settings (ENABLE_GEOCODING=false)"
            )
            return

        if domicilios_count <= 0:
            self.logger.debug("📍 No hay domicilios para geocodificar")
            return

        self.logger.info(
            f"🗺️  GEOCODIFICACIÓN ACTIVADA: Encolando {domicilios_count} domicilios para geocodificar"
        )
        self.logger.info(
            "   🔄 Los domicilios serán geocodificados en background por Celery (cola 'geocoding')"
        )
        self.logger.info(
            "   ⏱️  Procesamiento iniciará en 5 segundos (después del commit de DB)"
        )

        from app.features.geocoding.tasks import geocode_pending_domicilios

        try:
            # 5 second delay so commit finishes first
            task_result = geocode_pending_domicilios.apply_async(countdown=5)
            self.logger.info(
                f"   ✅ Tarea de geocodificación encolada exitosamente (task_id: {task_result.id})"
            )
            self.logger.info(
                "   📊 Para monitorear: celery -A app.core.celery_app inspect active"
            )
        except Exception as e:
            self.logger.error(f"   ❌ Error encolando tarea de geocodificación: {e}")
            self.logger.error(
                "   ⚠️  Verifica que Redis y Celery worker estén corriendo"
            )

    def _create_vinculos_ciudadano_domicilio(
        self, domicilios_df: pl.DataFrame, domicilios_ids_map: dict[tuple, int]
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
        df_prepared = (
            domicilios_df.lazy()
            .select([
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                pl_clean_string(Columns.CALLE_DOMICILIO.name).alias("calle_clean"),
                pl_clean_numero_domicilio(Columns.NUMERO_DOMICILIO.name).alias("numero_clean"),
                pl_safe_int(Columns.ID_LOC_INDEC_RESIDENCIA.name).alias("localidad_id"),
            ])
            .collect()
        )

        # Convert to dicts for lookup
        vinculos_data_raw = df_prepared.to_dicts()

        # Post-process: map to domicilio IDs
        timestamp = self._get_current_timestamp()
        vinculos_data = []
        for record in vinculos_data_raw:
            codigo_ciudadano = record["codigo_ciudadano"]
            calle_clean = record["calle_clean"]
            numero_clean = record["numero_clean"]
            localidad_id = record["localidad_id"]

            # Lookup domicilio ID
            id_domicilio = domicilios_ids_map.get((calle_clean, numero_clean, localidad_id))

            # Only create link if both ciudadano and domicilio are valid
            if codigo_ciudadano and id_domicilio:
                vinculos_data.append({
                    "codigo_ciudadano": codigo_ciudadano,
                    "id_domicilio": id_domicilio,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

        if not vinculos_data:
            return 0

        stmt = pg_insert(CiudadanoDomicilio.__table__).values(vinculos_data)
        upsert_stmt = stmt.on_conflict_do_nothing()

        try:
            self.context.session.execute(upsert_stmt)
        except Exception as e:
            self.logger.error(f"Failed to insert ciudadano_domicilio: {e}")
            raise e

        return len(vinculos_data)

    def _ensure_localidades_exist(self, localidad_ids: list) -> dict[int, int]:
        """
        Ensure that all needed localities exist in the database.
        Creates placeholder localities for missing ones to avoid losing data.

        Returns mapping from original id_localidad_indec -> actual id_localidad_indec in DB
        """
        if not localidad_ids:
            return {}

        # Get existing localities
        stmt = select(Localidad.id_localidad_indec).where(
            Localidad.id_localidad_indec.in_(localidad_ids)
        )
        existentes = set(
            id_loc for (id_loc,) in self.context.session.execute(stmt).all()
        )

        # Mapping: all existing ones map to themselves
        localidad_mapping = {loc_id: loc_id for loc_id in existentes}

        # Create placeholders for missing ones
        faltantes = [loc_id for loc_id in localidad_ids if loc_id not in existentes]

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
                    localidad_mapping[loc_id] = loc_id

        return localidad_mapping
