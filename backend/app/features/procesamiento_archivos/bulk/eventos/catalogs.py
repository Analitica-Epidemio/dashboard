"""
Catalog processors: Grupos ENO, Tipos ENO, and other taxonomies.

Handles get-or-create operations for catalog/taxonomy tables.
OPTIMIZADO CON POLARS PURO - lazy evaluation, joins, sin loops Python.
"""

import logging

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.utils.codigo_generator import CodigoGenerator
from app.domains.eventos_epidemiologicos.eventos.models import GrupoEno, TipoEno

from ...config.columns import Columns
from ..shared import get_or_create_catalog, get_current_timestamp


logger = logging.getLogger(__name__)


class CatalogsProcessor:
    """Handles catalog/taxonomy operations for eventos - POLARS PURO."""

    def __init__(self, context, logger_instance):
        self.context = context
        self.logger = logger_instance

    def get_or_create_grupos_eno(self, df: pl.DataFrame) -> dict[str, int]:
        """
        Get or create grupo ENO entries using generic catalog pattern.

        POLARS PURO: usa helper get_or_create_catalog de shared.py.
        """

        def transform_grupo(valor: str) -> dict:
            """Transform CSV value to GrupoEno record."""
            grupo_data = CodigoGenerator.generar_par_grupo(
                valor,
                f"Grupo {CodigoGenerator.capitalizar_nombre(valor)} (importado del CSV)",
            )
            timestamp = get_current_timestamp()
            return {
                "nombre": grupo_data["nombre"],
                "codigo": grupo_data["codigo"],
                "descripcion": grupo_data["descripcion"],
                "created_at": timestamp,
                "updated_at": timestamp,
            }

        try:
            return get_or_create_catalog(
                session=self.context.session,
                model=GrupoEno,
                df=df,
                column=Columns.GRUPO_EVENTO.name,
                key_field="codigo",
                transform_fn=transform_grupo,
            )
        except Exception as e:
            self.logger.error(f"Error creating grupos ENO: {e}")
            return {}

    def get_or_create_tipos_eno(
        self, df: pl.DataFrame, grupo_mapping: dict[str, int]
    ) -> tuple[dict[str, int], dict[int, set]]:
        """
        Get or create tipo ENO entries with grupo associations.

        OPTIMIZADO CON POLARS PURO:
        - Lazy evaluation con .lazy()
        - Join para mapear grupo_id desde grupo_mapping
        - Agregación con group_by para tipo -> grupos
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

        # === PASO 2: Generar códigos con Polars apply (batch processing) ===
        # Nota: apply es más eficiente que iterar row-by-row en Python
        df_with_codes = df_prepared.with_columns([
            pl.col("grupo_str")
                .map_elements(
                    lambda x: CodigoGenerator.generar_codigo_kebab(x),
                    return_dtype=pl.Utf8
                )
                .alias("codigo_grupo"),
            pl.col("tipo_str")
                .map_elements(
                    lambda x: CodigoGenerator.generar_codigo_kebab(x),
                    return_dtype=pl.Utf8
                )
                .alias("codigo_tipo"),
        ])

        # === PASO 3: JOIN con grupo_mapping para obtener grupo_id ===
        # Convertir grupo_mapping a DataFrame para hacer join
        if not grupo_mapping:
            return {}, {}

        grupo_df = pl.DataFrame({
            "codigo_grupo": list(grupo_mapping.keys()),
            "grupo_id": list(grupo_mapping.values()),
        })

        df_with_grupo_id = df_with_codes.join(
            grupo_df,
            on="codigo_grupo",
            how="inner"  # Solo mantener registros con grupo_id válido
        )

        if df_with_grupo_id.height == 0:
            return {}, {}

        # === PASO 4: Agregar por tipo para obtener tipo -> grupos mapping ===
        # Para cada tipo_codigo, obtener:
        # - El nombre original (primer valor, para crear el tipo)
        # - Set de grupo_ids asociados
        tipo_grupos_agg = (
            df_with_grupo_id
            .group_by("codigo_tipo")
            .agg([
                pl.col("tipo_str").first().alias("tipo_nombre_original"),
                pl.col("grupo_id").unique().alias("grupo_ids"),
            ])
        )

        # Extraer tipos únicos para check/create
        tipos_set = set(tipo_grupos_agg["codigo_tipo"].to_list())

        if not tipos_set:
            return {}, {}

        # === PASO 5: Check existing tipos ===
        stmt = select(TipoEno.id, TipoEno.codigo).where(
            TipoEno.codigo.in_(list(tipos_set))
        )
        existing_mapping = {
            codigo: tipo_id
            for tipo_id, codigo in self.context.session.execute(stmt).all()
        }

        # === PASO 6: Create missing tipos ===
        existing_keys = set(existing_mapping.keys())
        faltantes = tipos_set - existing_keys

        if faltantes:
            # Filtrar agregación para solo faltantes y crear registros
            tipo_faltantes_df = tipo_grupos_agg.filter(
                pl.col("codigo_tipo").is_in(list(faltantes))
            )

            timestamp = get_current_timestamp()
            nuevos_tipos = []
            for row in tipo_faltantes_df.iter_rows(named=True):
                tipo_codigo = row["codigo_tipo"]
                nombre_original = row["tipo_nombre_original"]

                tipo_data = CodigoGenerator.generar_par_tipo(nombre_original)
                nuevos_tipos.append({
                    "nombre": tipo_data["nombre"],
                    "codigo": tipo_data["codigo"],
                    "created_at": timestamp,
                    "updated_at": timestamp,
                })

            if nuevos_tipos:
                stmt = pg_insert(TipoEno.__table__).values(nuevos_tipos)
                upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["codigo"])
                self.context.session.execute(upsert_stmt)

                # Re-fetch complete mapping
                stmt = select(TipoEno.id, TipoEno.codigo).where(
                    TipoEno.codigo.in_(list(tipos_set))
                )
                existing_mapping = {
                    codigo: tipo_id
                    for tipo_id, codigo in self.context.session.execute(stmt).all()
                }

        # === PASO 7: Build tipo_id → grupo_ids mapping usando Polars ===
        # Join tipo_grupos_agg con existing_mapping para obtener tipo_id
        tipo_id_df = pl.DataFrame({
            "codigo_tipo": list(existing_mapping.keys()),
            "tipo_id": list(existing_mapping.values()),
        })

        tipo_grupos_final = tipo_grupos_agg.join(
            tipo_id_df,
            on="codigo_tipo",
            how="inner"
        )

        # Convertir a dict: tipo_id -> set(grupo_ids)
        tipo_grupos_mapping: dict[int, set] = {}
        for row in tipo_grupos_final.iter_rows(named=True):
            tipo_id = row["tipo_id"]
            grupo_ids = row["grupo_ids"]
            tipo_grupos_mapping[tipo_id] = set(grupo_ids)

        return existing_mapping, tipo_grupos_mapping
