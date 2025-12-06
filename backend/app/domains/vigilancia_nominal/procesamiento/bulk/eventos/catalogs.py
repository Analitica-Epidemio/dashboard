"""
Catalog processors: Grupos de Enfermedades, Enfermedades, and other taxonomies.

Handles get-or-create operations for catalog/taxonomy tables.
OPTIMIZADO CON POLARS PURO - lazy evaluation, joins, sin loops Python.
"""

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.slug import capitalizar_nombre, generar_slug
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    GrupoDeEnfermedades,
)
from ..config.columns import Columns
from ..shared import get_current_timestamp, get_or_create_catalog


class CatalogsProcessor:
    """Handles catalog/taxonomy operations for eventos - POLARS PURO."""

    def __init__(self, context, logger_instance):
        self.context = context
        self.logger = logger_instance

    def get_or_create_grupos(self, df: pl.DataFrame) -> dict[str, int]:
        """
        Get or create GrupoDeEnfermedades entries using generic catalog pattern.

        POLARS PURO: usa helper get_or_create_catalog de shared.py.
        """

        def transform_grupo(valor: str) -> dict:
            """Transform CSV value to GrupoDeEnfermedades record."""
            nombre = capitalizar_nombre(valor)
            timestamp = get_current_timestamp()
            return {
                "nombre": nombre,
                "slug": generar_slug(valor),
                "descripcion": f"Grupo {nombre} (importado del CSV)",
                "created_at": timestamp,
                "updated_at": timestamp,
            }

        try:
            return get_or_create_catalog(
                session=self.context.session,
                model=GrupoDeEnfermedades,
                df=df,
                column=Columns.GRUPO_EVENTO.name,
                key_field="slug",
                transform_fn=transform_grupo,
            )
        except Exception as e:
            self.logger.error(f"Error creating grupos: {e}")
            return {}

    def get_or_create_enfermedades(
        self, df: pl.DataFrame, grupo_mapping: dict[str, int]
    ) -> tuple[dict[str, int], dict[int, set]]:
        """
        Get or create Enfermedad entries with grupo associations.

        OPTIMIZADO CON POLARS PURO:
        - Lazy evaluation con .lazy()
        - Join para mapear grupo_id desde grupo_mapping
        - Agregación con group_by para enfermedad -> grupos
        - Sin loops Python
        """

        # === PASO 1: Preparar datos con Polars lazy ===
        df_lazy = (
            df.lazy()
            .filter(
                pl.col(Columns.GRUPO_EVENTO.name).is_not_null()
                & pl.col(Columns.TIPO_EVENTO.name).is_not_null()
            )
            .select([
                pl.col(Columns.GRUPO_EVENTO.name)
                    .cast(pl.Utf8)
                    .str.strip_chars()
                    .alias("grupo_str"),
                pl.col(Columns.TIPO_EVENTO.name)
                    .cast(pl.Utf8)
                    .str.strip_chars()
                    .alias("tipo_str"),
            ])
            .filter(
                (pl.col("grupo_str") != "")
                & (pl.col("tipo_str") != "")
            )
        )

        df_prepared = df_lazy.collect()

        if df_prepared.height == 0:
            return {}, {}

        # === PASO 2: Generar slugs con Polars apply (batch processing) ===
        df_with_slugs = df_prepared.with_columns([
            pl.col("grupo_str")
                .map_elements(generar_slug, return_dtype=pl.Utf8)
                .alias("slug_grupo"),
            pl.col("tipo_str")
                .map_elements(generar_slug, return_dtype=pl.Utf8)
                .alias("slug_tipo"),
        ])

        # === PASO 3: JOIN con grupo_mapping para obtener grupo_id ===
        if not grupo_mapping:
            return {}, {}

        grupo_df = pl.DataFrame({
            "slug_grupo": list(grupo_mapping.keys()),
            "grupo_id": list(grupo_mapping.values()),
        })

        df_with_grupo_id = df_with_slugs.join(
            grupo_df,
            on="slug_grupo",
            how="inner"
        )

        if df_with_grupo_id.height == 0:
            return {}, {}

        # === PASO 4: Agregar por enfermedad para obtener enfermedad -> grupos mapping ===
        enfermedad_grupos_agg = (
            df_with_grupo_id
            .group_by("slug_tipo")
            .agg([
                pl.col("tipo_str").first().alias("nombre_original"),
                pl.col("grupo_id").unique().alias("grupo_ids"),
            ])
        )

        # Extraer slugs únicos para check/create
        slugs_set = set(enfermedad_grupos_agg["slug_tipo"].to_list())

        if not slugs_set:
            return {}, {}

        # === PASO 5: Check existing enfermedades ===
        stmt = select(Enfermedad.id, Enfermedad.slug).where(
            Enfermedad.slug.in_(list(slugs_set))
        )
        existing_mapping = {
            slug: enfermedad_id
            for enfermedad_id, slug in self.context.session.execute(stmt).all()
        }

        # === PASO 6: Create missing enfermedades ===
        existing_slugs = set(existing_mapping.keys())
        faltantes = slugs_set - existing_slugs

        if faltantes:
            faltantes_df = enfermedad_grupos_agg.filter(
                pl.col("slug_tipo").is_in(list(faltantes))
            )

            timestamp = get_current_timestamp()
            nuevas_enfermedades = []
            for row in faltantes_df.iter_rows(named=True):
                nombre_original = row["nombre_original"]
                nuevas_enfermedades.append({
                    "nombre": capitalizar_nombre(nombre_original),
                    "slug": generar_slug(nombre_original),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

            if nuevas_enfermedades:
                stmt = pg_insert(Enfermedad.__table__).values(nuevas_enfermedades)
                upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["slug"])
                self.context.session.execute(upsert_stmt)

                # Re-fetch complete mapping
                stmt = select(Enfermedad.id, Enfermedad.slug).where(
                    Enfermedad.slug.in_(list(slugs_set))
                )
                existing_mapping = {
                    slug: enfermedad_id
                    for enfermedad_id, slug in self.context.session.execute(stmt).all()
                }

        # === PASO 7: Build enfermedad_id → grupo_ids mapping ===
        enfermedad_id_df = pl.DataFrame({
            "slug_tipo": list(existing_mapping.keys()),
            "enfermedad_id": list(existing_mapping.values()),
        })

        enfermedad_grupos_final = enfermedad_grupos_agg.join(
            enfermedad_id_df,
            on="slug_tipo",
            how="inner"
        )

        # Convertir a dict: enfermedad_id -> set(grupo_ids)
        enfermedad_grupos_mapping: dict[int, set] = {}
        for row in enfermedad_grupos_final.iter_rows(named=True):
            enfermedad_id = row["enfermedad_id"]
            grupo_ids = row["grupo_ids"]
            enfermedad_grupos_mapping[enfermedad_id] = set(grupo_ids)

        return existing_mapping, enfermedad_grupos_mapping
