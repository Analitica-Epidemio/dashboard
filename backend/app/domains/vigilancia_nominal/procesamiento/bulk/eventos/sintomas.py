"""Bulk processor for symptoms - POLARS PURO optimizado."""

from datetime import date, datetime
from typing import Dict

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.vigilancia_nominal.models.salud import Sintoma
from app.domains.vigilancia_nominal.models.caso import DetalleCasoSintomas
from app.core.epidemiology import (
    calcular_semana_epidemiologica,
)

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    pl_clean_string,
    pl_safe_int,
)


def safe_date(value) -> date | None:
    """
    Safely convert value to date.

    Handles:
    - None -> None
    - date -> date
    - datetime -> date
    - Other -> None
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    return None


class SintomasProcessor(BulkProcessorBase):
    """Handles symptom-related bulk operations - POLARS PURO."""

    def upsert_sintomas_eventos(
        self,
        df: pl.DataFrame,
        sintoma_mapping: Dict[str, int],
    ) -> BulkOperationResult:
        """
        Bulk upsert de síntomas de eventos - POLARS PURO.

        Optimizaciones:
        - Lazy evaluation con .lazy()
        - .explode() para split de síntomas separados por coma
        - Join en Polars para evento_mapping
        - Sin loops Python
        """
        start_time = self._get_current_timestamp()

        # Validar inputs
        if df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 1. POLARS: Filtrar filas con síntomas válidos
        sintomas_df = df.filter(pl.col(Columns.SIGNO_SINTOMA.name).is_not_null())

        if sintomas_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 2. POLARS PURO: Preparar DataFrame de mapeo de síntomas
        # Convertir sintoma_mapping dict a DataFrame para join
        # IMPORTANTE: Las keys ya están en UPPERCASE en el mapping
        sintoma_mapping_df = pl.DataFrame({
            "sintoma_upper": list(sintoma_mapping.keys()),
            "id_sintoma": list(sintoma_mapping.values()),
        })

        # 3. POLARS PURO: Preparar datos con lazy evaluation
        sintomas_prepared = (
            sintomas_df.lazy()
            .select([
                pl.col("id_caso"),  # Cambiado de id_evento a id_caso
                pl_clean_string(Columns.SIGNO_SINTOMA.name).alias("sintoma_raw"),
                (
                    pl.col(Columns.FECHA_INICIO_SINTOMA.name)
                    if Columns.FECHA_INICIO_SINTOMA.name in sintomas_df.columns
                    else pl.lit(None)
                ).alias("fecha_inicio_sintoma"),
            ])
            .filter(
                # Filtrar null después de conversión
                pl.col("id_caso").is_not_null()
                & pl.col("sintoma_raw").is_not_null()
            )
            # 4. EXPLODE: Split de síntomas separados por coma (SIN LOOPS PYTHON!)
            # Si un síntoma tiene "FIEBRE,TOS", se convierte en 2 filas
            .with_columns([
                pl.col("sintoma_raw")
                .str.split(",")
                .alias("sintomas_list")
            ])
            .explode("sintomas_list")
            # Limpiar cada síntoma individual después del split
            .with_columns([
                pl.col("sintomas_list")
                .str.strip_chars()
                .str.to_uppercase()
                .alias("sintoma_upper")
            ])
            .filter(pl.col("sintoma_upper").is_not_null() & (pl.col("sintoma_upper") != ""))
            # 5. JOIN: Mapear sintoma_id (SIN LOOPS PYTHON!)
            .join(sintoma_mapping_df.lazy(), on="sintoma_upper", how="left")
            .collect()
        )

        if sintomas_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 7. Log de síntomas sin mapear
        sintomas_sin_mapear = sintomas_prepared.filter(
            pl.col("id_sintoma").is_null()
        ).height

        if sintomas_sin_mapear > 0:
            # Obtener ejemplos de síntomas sin mapear
            ejemplos = (
                sintomas_prepared
                .filter(pl.col("id_sintoma").is_null())
                .select("sintoma_upper")
                .unique()
                .head(5)
                .to_series()
                .to_list()
            )
            self.logger.warning(
                f"⚠️  {sintomas_sin_mapear} filas con síntomas no mapeados. "
                f"Ejemplos: {ejemplos}"
            )

        # 8. POLARS: Filtrar solo síntomas mapeados
        sintomas_validos = sintomas_prepared.filter(
            pl.col("id_sintoma").is_not_null()
        )

        if sintomas_validos.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 9. POLARS: Deduplicar y agregrar por (id_caso, id_sintoma)
        # Mantener la fecha más temprana para cada combinación
        sintomas_dedup = (
            sintomas_validos
            .group_by(["id_caso", "id_sintoma"])  # Cambiado de id_evento a id_caso
            .agg([
                pl.col("fecha_inicio_sintoma").min().alias("fecha_inicio_sintoma")
            ])
        )

        duplicados_removidos = sintomas_validos.height - sintomas_dedup.height
        if duplicados_removidos > 0:
            self.logger.info(
                f"🔄 Removidos {duplicados_removidos} síntomas duplicados "
                f"(misma combinación evento-síntoma)"
            )

        # 10. Convertir a dicts para procesamiento de fechas epidemiológicas
        # (calcular_semana_epidemiologica requiere Python)
        sintomas_data_raw = sintomas_dedup.to_dicts()

        # 11. Calcular semanas epidemiológicas y preparar para insert
        timestamp = self._get_current_timestamp()
        sintomas_eventos_data = []

        for record in sintomas_data_raw:
            fecha_inicio = safe_date(record.get("fecha_inicio_sintoma"))

            # Calcular semana epidemiológica si hay fecha
            semana_epi = None
            anio_epi = None
            if fecha_inicio:
                semana_epi, anio_epi = calcular_semana_epidemiologica(fecha_inicio)

            sintomas_eventos_data.append({
                "id_caso": int(record["id_caso"]),  # Cambiado de id_evento a id_caso
                "id_sintoma": int(record["id_sintoma"]),
                "fecha_inicio_sintoma": fecha_inicio,
                "semana_epidemiologica_aparicion_sintoma": semana_epi,
                "anio_epidemiologico_sintoma": anio_epi,
                "created_at": timestamp,
                "updated_at": timestamp,
            })

        # 12. Bulk upsert
        if sintomas_eventos_data:
            stmt = pg_insert(DetalleCasoSintomas.__table__).values(
                sintomas_eventos_data
            )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id_caso", "id_sintoma"],  # Cambiado de id_evento a id_caso
                set_={
                    "fecha_inicio_sintoma": stmt.excluded.fecha_inicio_sintoma,
                    "semana_epidemiologica_aparicion_sintoma": stmt.excluded.semana_epidemiologica_aparicion_sintoma,
                    "anio_epidemiologico_sintoma": stmt.excluded.anio_epidemiologico_sintoma,
                    "updated_at": timestamp,
                },
            )

            self.context.session.execute(upsert_stmt)
            self.logger.info(
                f"✅ {len(sintomas_eventos_data)} relaciones síntoma-evento procesadas"
            )

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(sintomas_eventos_data),
            updated_count=0,
            skipped_count=sintomas_sin_mapear,
            errors=[],
            duration_seconds=duration,
        )

    def _get_or_create_sintomas(self, df: pl.DataFrame) -> Dict[str, int]:
        """
        Get or create symptom catalog entries - POLARS PURO.

        Optimizaciones:
        - Lazy evaluation
        - .explode() para split de síntomas separados por coma
        - Sin loops Python para extracción
        """
        # 1. POLARS: Filtrar filas válidas con lazy evaluation
        df_valid = df.lazy().filter(
            pl.col(Columns.SIGNO_SINTOMA.name).is_not_null()
            & pl.col(Columns.ID_SNVS_SIGNO_SINTOMA.name).is_not_null()
        )

        # 2. POLARS PURO: Preparar y explotar síntomas
        sintomas_prepared = (
            df_valid
            .select([
                pl.col(Columns.SIGNO_SINTOMA.name).alias("sintoma_raw"),
                pl_safe_int(Columns.ID_SNVS_SIGNO_SINTOMA.name).alias("id_snvs"),
            ])
            .filter(pl.col("id_snvs").is_not_null())
            # EXPLODE: Split de síntomas separados por coma
            .with_columns([
                pl.col("sintoma_raw")
                .str.split(",")
                .alias("sintomas_list")
            ])
            .explode("sintomas_list")
            # Limpiar cada síntoma individual
            .with_columns([
                pl.col("sintomas_list")
                .str.strip_chars()
                .str.to_uppercase()
                .alias("sintoma_clean")
            ])
            .filter(
                pl.col("sintoma_clean").is_not_null()
                & (pl.col("sintoma_clean") != "")
            )
            # Deduplicar: último valor gana si hay duplicados
            .unique(subset=["sintoma_clean"], keep="last", maintain_order=False)
            .select(["sintoma_clean", "id_snvs"])
            .collect()
        )

        if sintomas_prepared.height == 0:
            self.logger.warning("No síntomas data extracted from DataFrame")
            return {}

        self.logger.debug(f"Extracted {sintomas_prepared.height} unique síntomas")

        # 3. Convertir a dict para trabajar con SQLAlchemy
        # sintoma_clean (UPPER) -> id_snvs
        sintomas_data = dict(
            zip(
                sintomas_prepared["sintoma_clean"].to_list(),
                sintomas_prepared["id_snvs"].to_list()
            )
        )

        # 4. Verificar existentes
        stmt = select(Sintoma.id, Sintoma.signo_sintoma).where(
            Sintoma.signo_sintoma.in_(list(sintomas_data.keys()))
        )
        existing_mapping = {
            signo_sintoma: sintoma_id
            for sintoma_id, signo_sintoma in self.context.session.execute(stmt).all()
        }

        # 5. Crear nuevos con IDs del CSV
        nuevos_sintomas = []
        timestamp = self._get_current_timestamp()

        for signo_sintoma, id_snvs in sintomas_data.items():
            if signo_sintoma not in existing_mapping:
                nuevos_sintomas.append({
                    "id_snvs_signo_sintoma": id_snvs,
                    "signo_sintoma": signo_sintoma,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

        if nuevos_sintomas:
            stmt = pg_insert(Sintoma.__table__).values(nuevos_sintomas)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        # 6. SIEMPRE re-obtener mapping completo después de cualquier inserción
        # Usar id_snvs_signo_sintoma para el mapping ya que es único y consistente
        stmt = select(
            Sintoma.id, Sintoma.id_snvs_signo_sintoma, Sintoma.signo_sintoma
        ).where(Sintoma.id_snvs_signo_sintoma.in_(list(sintomas_data.values())))

        all_results = list(self.context.session.execute(stmt).all())
        self.logger.info(f"Mapping de síntomas: {len(all_results)} encontrados en BD")

        # 7. Crear mapping por nombre de síntoma basado en los IDs SNVS
        id_snvs_to_db_id = {
            id_snvs: sintoma_id for sintoma_id, id_snvs, _ in all_results
        }

        # 8. Crear el mapping final: signo_sintoma (UPPER) -> id de la BD
        final_mapping = {}
        sintomas_faltantes = []

        for signo_sintoma, id_snvs in sintomas_data.items():
            if id_snvs in id_snvs_to_db_id:
                # Almacenar con la clave en mayúsculas (ya está en UPPER)
                final_mapping[signo_sintoma] = id_snvs_to_db_id[id_snvs]
            else:
                sintomas_faltantes.append(f"{signo_sintoma} (SNVS {id_snvs})")

        if sintomas_faltantes:
            self.logger.warning(
                f"⚠️  {len(sintomas_faltantes)} síntomas no encontrados en BD. "
                f"Ejemplos: {sintomas_faltantes[:3]}"
            )

        self.logger.info(
            f"✅ Mapping de síntomas completado: {len(final_mapping)} síntomas mapeados"
        )
        return final_mapping
