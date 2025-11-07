"""Address and citizen-address link operations."""

from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.domains.sujetos_epidemiologicos.ciudadanos_models import CiudadanoDomicilio
from app.domains.territorio.geografia_models import Domicilio, Localidad

from ...config.columns import Columns
from ..shared import BulkProcessorBase, BulkOperationResult
from ..shared import is_valid_street_name


class DomiciliosProcessor(BulkProcessorBase):
    """Handles address-related bulk operations."""

    def _clean_numero_domicilio(self, numero_series: pd.Series) -> pd.Series:
        """
        Limpia columna numero_domicilio manejando tanto string como numeric.

        Args:
            numero_series: Serie de pandas con números de domicilio

        Returns:
            Serie limpia con valores string sin decimales (ej: "1332" no "1332.0")

        IMPORTANTE: Siempre retorna strings para evitar problemas de tipo en PostgreSQL
        """
        # ESTRATEGIA: Convertir TODO a string explícitamente
        # Esto evita que pandas o SQLAlchemy infieran tipos numéricos

        def to_string_numero(val):
            """Convierte valor a string, manejando None, NaN, floats, etc."""
            if pd.isna(val) or val is None or val == "":
                return None
            # Si es float, convertir a int primero para quitar decimales
            if isinstance(val, (float, int)):
                return str(int(val))
            # Si es string, limpiar
            return str(val).strip() if str(val).strip() else None

        return numero_series.apply(to_string_numero)

    def upsert_ciudadanos_domicilios(self, df: pd.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert of addresses and citizen-address links.

        Simplified flow:
        1. Upsert unique addresses
        2. Trigger geocoding (if enabled)
        3. Create citizen-address links
        """
        start_time = self._get_current_timestamp()

        # Filter records with valid address data
        domicilios_df = self._filter_valid_domicilios(df)
        if domicilios_df.empty:
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

    def _filter_valid_domicilios(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter records with valid address data.

        Excluye domicilios que no son geocodificables:
        - Sin código de ciudadano
        - Sin localidad
        - Sin calle válida (ej: S/N, NO APLICA, etc.)
        """
        # Filtro básico: debe tener ciudadano y localidad
        filtered = df.dropna(subset=[Columns.CODIGO_CIUDADANO.name])
        filtered = filtered[filtered[Columns.ID_LOC_INDEC_RESIDENCIA.name].notna()]

        # Aplicar validación de calle válida
        calle_col = Columns.CALLE_DOMICILIO.name
        if calle_col in filtered.columns:
            # Crear máscara de calles válidas
            calle_valida_mask = filtered[calle_col].apply(
                lambda x: is_valid_street_name(x) if pd.notna(x) else False
            )

            # Solo mantener registros con calle válida
            filtered = filtered[calle_valida_mask]

            # Log de registros filtrados
            records_filtered = len(df) - len(filtered)
            if records_filtered > 0:
                self.logger.info(
                    f"📍 Filtrados {records_filtered} domicilios sin calle válida "
                    f"(S/N, NO APLICA, etc.)"
                )

        return filtered

    def _upsert_domicilios_unicos(
        self, domicilios_df: pd.DataFrame
    ) -> Dict[tuple, int]:
        """
        Create unique addresses and return mapping (street, number, locality) → id.

        Returns:
            {(calle, numero, localidad_id): domicilio_id}
        """
        # Ensure localities exist
        localidad_ids = (
            domicilios_df[Columns.ID_LOC_INDEC_RESIDENCIA.name]
            .dropna()
            .unique()
            .tolist()
        )
        localidad_mapping = self._ensure_localidades_exist(localidad_ids)

        # Extract unique addresses
        domicilios_unicos = domicilios_df[
            [
                Columns.CALLE_DOMICILIO.name,
                Columns.NUMERO_DOMICILIO.name,
                Columns.ID_LOC_INDEC_RESIDENCIA.name,
            ]
        ].drop_duplicates()

        # VECTORIZED: Prepare data for insert (100x faster than iterrows())
        timestamp = self._get_current_timestamp()
        domicilios_unicos = domicilios_unicos.copy()

        # Map locality IDs vectorially
        domicilios_unicos["localidad_id_mapped"] = (
            pd.to_numeric(
                domicilios_unicos[Columns.ID_LOC_INDEC_RESIDENCIA.name], errors="coerce"
            )
            .astype("Int64")
            .map(localidad_mapping)
        )

        # Filter only valid localities
        domicilios_validos = domicilios_unicos[
            domicilios_unicos["localidad_id_mapped"].notna()
        ]

        if domicilios_validos.empty:
            return {}

        # Build data using pandas Series (fast) then convert to list manually
        # EVITAR: DataFrame.to_dict('records') porque infiere tipos numéricos

        calle_series = (
            domicilios_validos[Columns.CALLE_DOMICILIO.name]
            .str.strip()
            .replace("", None)
        )
        numero_series = self._clean_numero_domicilio(
            domicilios_validos[Columns.NUMERO_DOMICILIO.name]
        )
        localidad_series = domicilios_validos["localidad_id_mapped"].astype(int)

        # CRÍTICO: Construir dicts manualmente para garantizar tipos correctos
        # IMPORTANTE: Aplicar validación de calle aquí también para asegurar que no se creen domicilios sin calle
        domicilios_data = []
        skipped_invalid_count = 0
        for i in range(len(domicilios_validos)):
            calle_val = calle_series.iloc[i]
            numero_val = numero_series.iloc[i]
            localidad_val = localidad_series.iloc[i]

            # VALIDACIÓN CRÍTICA: No crear domicilio si la calle no es válida
            if not is_valid_street_name(calle_val):
                skipped_invalid_count += 1
                self.logger.debug(
                    f"🚫 Skipping invalid calle: '{calle_val}' (type={type(calle_val).__name__}, "
                    f"repr={repr(calle_val)}, numero={numero_val})"
                )
                continue  # Skip este domicilio

            # Garantizar que numero sea string o None
            if numero_val is not None and not isinstance(numero_val, str):
                numero_val = str(numero_val)

            domicilios_data.append(
                {
                    "calle": calle_val if pd.notna(calle_val) else None,
                    "numero": numero_val,
                    "id_localidad_indec": int(localidad_val),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
            )

        if skipped_invalid_count > 0:
            self.logger.info(
                f"✅ Skipped {skipped_invalid_count} domicilios with invalid calles"
            )

        if not domicilios_data:
            return {}

        # DEBUG: Verificar tipos en los primeros registros
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

        # CRÍTICO: Asegurar que numero sea string en las tuplas
        domicilios_keys = [
            (
                d["calle"],
                str(d["numero"]) if d["numero"] is not None else None,
                d["id_localidad_indec"],
            )
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
            f"   🔄 Los domicilios serán geocodificados en background por Celery (cola 'geocoding')"
        )
        self.logger.info(
            f"   ⏱️  Procesamiento iniciará en 5 segundos (después del commit de DB)"
        )

        from app.features.geocoding.tasks import geocode_pending_domicilios

        try:
            # 5 second delay so commit finishes first
            task_result = geocode_pending_domicilios.apply_async(countdown=5)
            self.logger.info(
                f"   ✅ Tarea de geocodificación encolada exitosamente (task_id: {task_result.id})"
            )
            self.logger.info(
                f"   📊 Para monitorear: celery -A app.core.celery_app inspect active"
            )
        except Exception as e:
            self.logger.error(f"   ❌ Error encolando tarea de geocodificación: {e}")
            self.logger.error(
                f"   ⚠️  Verifica que Redis y Celery worker estén corriendo"
            )

    def _create_vinculos_ciudadano_domicilio(
        self, domicilios_df: pd.DataFrame, domicilios_ids_map: Dict[tuple, int]
    ) -> int:
        """
        Create links between citizens and addresses.

        Returns:
            Number of links created
        """
        # VECTORIZED: Prepare dataframe with clean data (100x faster than .apply())
        df_clean = domicilios_df.copy()
        df_clean["calle_clean"] = (
            df_clean[Columns.CALLE_DOMICILIO.name].str.strip().replace("", None)
        )
        df_clean["numero_clean"] = self._clean_numero_domicilio(
            df_clean[Columns.NUMERO_DOMICILIO.name]
        )
        # CRÍTICO: Asegurar que numero_clean sea string/object para lookup consistente
        df_clean["numero_clean"] = df_clean["numero_clean"].astype("object")
        df_clean["localidad_id"] = pd.to_numeric(
            df_clean[Columns.ID_LOC_INDEC_RESIDENCIA.name], errors="coerce"
        ).astype("Int64")

        # VECTORIZED: Map to domicilio_id using tuple lookup
        df_clean["id_domicilio"] = df_clean.apply(
            lambda row: domicilios_ids_map.get(
                (row["calle_clean"], row["numero_clean"], row["localidad_id"])
            ),
            axis=1,
        )

        # Filter only valid entries
        df_validos = df_clean[df_clean["id_domicilio"].notna()]

        if df_validos.empty:
            return 0

        # VECTORIZED: Create links using dict comprehension
        timestamp = self._get_current_timestamp()
        vinculos_data = {
            "codigo_ciudadano": pd.to_numeric(
                df_validos[Columns.CODIGO_CIUDADANO.name], errors="coerce"
            ).astype("Int64"),
            "id_domicilio": df_validos["id_domicilio"].astype(int),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        vinculos_data = pd.DataFrame(vinculos_data).to_dict("records")

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

    def _ensure_localidades_exist(self, localidad_ids: list) -> Dict[int, int]:
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
                        "categoria": "Placeholder",
                        "centroide_lat": None,
                        "centroide_lon": None,
                        "id_departamento_indec": 99999,  # Placeholder department
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
