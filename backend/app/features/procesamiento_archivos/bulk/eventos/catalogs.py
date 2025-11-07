"""
Catalog processors: Grupos ENO, Tipos ENO, and other taxonomies.

Handles get-or-create operations for catalog/taxonomy tables.
"""

import logging
from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.utils.codigo_generator import CodigoGenerator
from app.domains.eventos_epidemiologicos.eventos.models import GrupoEno, TipoEno

from ...config.columns import Columns
from ..shared import get_or_create_catalog, get_current_timestamp


logger = logging.getLogger(__name__)


class CatalogsProcessor:
    """Handles catalog/taxonomy operations for eventos."""

    def __init__(self, context, logger_instance):
        self.context = context
        self.logger = logger_instance

    def get_or_create_grupos_eno(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get or create grupo ENO entries using generic catalog pattern."""

        def transform_grupo(valor: str) -> Dict:
            """Transform CSV value to GrupoEno record."""
            codigo = CodigoGenerator.generar_codigo_kebab(valor)
            grupo_data = CodigoGenerator.generar_par_grupo(
                valor,
                f"Grupo {CodigoGenerator.capitalizar_nombre(valor)} (importado del CSV)",
            )
            return {
                "nombre": grupo_data["nombre"],
                "codigo": grupo_data["codigo"],
                "descripcion": grupo_data["descripcion"],
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp(),
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
        self, df: pd.DataFrame, grupo_mapping: Dict[str, int]
    ) -> tuple[Dict[str, int], Dict[int, set]]:
        """Get or create tipo ENO entries with grupo associations."""

        # OPTIMIZACIÓN: Vectorizado con pandas (10-50x más rápido que iterrows)
        tipos_set = set()
        tipo_to_grupos = {}

        # Filtrar y preparar datos válidos
        df_valid = (
            df[[Columns.GRUPO_EVENTO.name, Columns.TIPO_EVENTO.name]].dropna().copy()
        )

        if df_valid.empty:
            return {}, {}

        # Vectorizado: generar códigos para todos de una vez
        df_valid["grupo_str"] = (
            df_valid[Columns.GRUPO_EVENTO.name].astype(str).str.strip()
        )
        df_valid["tipo_str"] = (
            df_valid[Columns.TIPO_EVENTO.name].astype(str).str.strip()
        )
        df_valid["codigo_grupo"] = df_valid["grupo_str"].apply(
            CodigoGenerator.generar_codigo_kebab
        )
        df_valid["codigo_tipo"] = df_valid["tipo_str"].apply(
            CodigoGenerator.generar_codigo_kebab
        )

        # Filtrar solo los que tienen grupo_id válido
        df_valid["grupo_id"] = df_valid["codigo_grupo"].map(grupo_mapping)
        df_valid = df_valid[df_valid["grupo_id"].notna()]

        # Agrupar por tipo para construir el diccionario
        for codigo_tipo, group_df in df_valid.groupby("codigo_tipo"):
            tipos_set.add(codigo_tipo)
            tipo_to_grupos[codigo_tipo] = {
                "original": group_df["tipo_str"].iloc[0],
                "grupos": set(group_df["grupo_id"].astype(int).unique()),
            }

        if not tipos_set:
            return {}, {}

        # Check existing tipos
        stmt = select(TipoEno.id, TipoEno.codigo).where(
            TipoEno.codigo.in_(list(tipos_set))
        )
        existing_mapping = {
            codigo: tipo_id
            for tipo_id, codigo in self.context.session.execute(stmt).all()
        }

        # Create missing tipos
        nuevos_tipos = []
        for tipo_codigo in tipos_set:
            if tipo_codigo not in existing_mapping:
                nombre_original = tipo_to_grupos[tipo_codigo]["original"]
                tipo_data = CodigoGenerator.generar_par_tipo(nombre_original)
                nuevos_tipos.append(
                    {
                        "nombre": tipo_data["nombre"],
                        "codigo": tipo_data["codigo"],
                        "created_at": get_current_timestamp(),
                        "updated_at": get_current_timestamp(),
                    }
                )

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

        # Build tipo_id → grupo_ids mapping
        tipo_grupos_mapping = {}
        for tipo_codigo, data in tipo_to_grupos.items():
            tipo_id = existing_mapping.get(tipo_codigo)
            if tipo_id:
                tipo_grupos_mapping[tipo_id] = data["grupos"]

        return existing_mapping, tipo_grupos_mapping
