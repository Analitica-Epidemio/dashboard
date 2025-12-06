"""Bulk processor for epidemiological antecedents - POLARS PURO."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.vigilancia_nominal.models.caso import (
    AntecedenteEpidemiologico,
    AntecedentesCasoEpidemiologico,
)

from ...config.columns import Columns
from ..shared import (
    BulkOperationResult,
    BulkProcessorBase,
    get_or_create_catalog,
)


class AntecedentesProcessor(BulkProcessorBase):
    """Handles epidemiological background operations - POLARS PURO."""

    def upsert_antecedentes_epidemiologicos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """
        Bulk upsert de antecedentes epidemiológicos usando POLARS PURO.

        Elimina loops Python para split/proceso de antecedentes.
        Usa .str.split() de Polars y join para evento_mapping.
        """
        start_time = self._get_current_timestamp()

        # 1. Filtrar filas con antecedentes válidos (lazy evaluation)
        antecedentes_df = df.filter(
            pl.col(Columns.ANTECEDENTE_EPIDEMIOLOGICO.name).is_not_null()
        )

        if antecedentes_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 2. Obtener mapeo de antecedentes (expandiendo delimitadores con Polars)
        antecedentes_mapping = self._get_or_create_antecedentes(df)

        if not antecedentes_mapping:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 3. Procesar antecedentes con POLARS PURO - id_evento ya existe en df
        # Normalizar delimitadores a "|" y hacer split
        processed_df = (
            antecedentes_df
            .select([
                pl.col("id_caso"),  # Ya existe del JOIN en main.py
                pl.col(Columns.ANTECEDENTE_EPIDEMIOLOGICO.name)
                .str.replace_all(",", "|")  # Normalizar comas
                .str.replace_all(";", "|")  # Normalizar punto y coma
                .alias("antecedentes_raw"),
            ])
            # Explotar antecedentes separados por "|" en filas individuales
            .with_columns([
                pl.col("antecedentes_raw").str.split("|").alias("antecedentes_list")
            ])
            .explode("antecedentes_list")
            # Limpiar cada antecedente individual
            .with_columns([
                pl.col("antecedentes_list").str.strip_chars().alias("antecedente_clean")
            ])
            # Filtrar antecedentes vacíos
            .filter(
                pl.col("antecedente_clean").is_not_null()
                & (pl.col("antecedente_clean") != "")
            )
        )

        if processed_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 4. Convertir antecedentes_mapping a DataFrame y hacer join
        antecedentes_mapping_df = pl.DataFrame({
            "antecedente_clean": list(antecedentes_mapping.keys()),
            "id_antecedente_epidemiologico": list(antecedentes_mapping.values()),
        })

        # 5. Join con antecedentes_mapping y preparar datos finales
        timestamp = self._get_current_timestamp()
        final_df = (
            processed_df
            .join(antecedentes_mapping_df, on="antecedente_clean", how="inner")
            .select([
                "id_caso",
                "id_antecedente_epidemiologico",
            ])
            # Eliminar duplicados (mismo evento + mismo antecedente)
            .unique()
            # Agregar timestamps
            .with_columns([
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
        )

        if final_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # 7. Insertar en base de datos
        antecedentes_eventos_data = final_df.to_dicts()

        stmt = pg_insert(AntecedentesCasoEpidemiologico.__table__).values(
            antecedentes_eventos_data
        )
        upsert_stmt = stmt.on_conflict_do_nothing(
            index_elements=["id_caso", "id_antecedente_epidemiologico"]
        )
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(antecedentes_eventos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    # === PRIVATE HELPER METHODS ===

    def _get_or_create_antecedentes(self, df: pl.DataFrame) -> dict[str, int]:
        """
        Get or create antecedent catalog entries - POLARS PURO.

        Usa .str.split() de Polars para expandir valores delimitados.
        """
        # 1. Extraer y normalizar antecedentes con POLARS PURO
        antecedentes_expanded = (
            df
            .filter(pl.col(Columns.ANTECEDENTE_EPIDEMIOLOGICO.name).is_not_null())
            .select([
                pl.col(Columns.ANTECEDENTE_EPIDEMIOLOGICO.name)
                .str.replace_all(",", "|")  # Normalizar comas
                .str.replace_all(";", "|")  # Normalizar punto y coma
                .alias("antecedentes_raw")
            ])
            # Split por "|" y explotar en filas individuales
            .with_columns([
                pl.col("antecedentes_raw").str.split("|").alias("antecedentes_list")
            ])
            .explode("antecedentes_list")
            # Limpiar cada antecedente
            .with_columns([
                pl.col("antecedentes_list").str.strip_chars().alias("antecedente_clean")
            ])
            # Filtrar vacíos
            .filter(
                pl.col("antecedente_clean").is_not_null()
                & (pl.col("antecedente_clean") != "")
            )
            # Obtener valores únicos
            .select("antecedente_clean")
            .unique()
        )

        if antecedentes_expanded.height == 0:
            return {}

        # 2. Renombrar columna para compatibilidad con get_or_create_catalog
        temp_df = antecedentes_expanded.rename({"antecedente_clean": "ANTECEDENTE"})

        # 3. Usar patrón genérico get_or_create_catalog
        return get_or_create_catalog(
            session=self.context.session,
            model=AntecedenteEpidemiologico,
            df=temp_df,
            column="ANTECEDENTE",
            key_field="descripcion",
            name_field="descripcion",
            # La tabla no tiene unique constraint en descripcion
            has_unique_constraint=False,
        )
