"""Main processor for citizen operations - Polars puro optimizado."""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano

from ...config.columns import Columns
from ..shared import (
    BulkProcessorBase,
    BulkOperationResult,
    pl_safe_int,
    pl_clean_string,
    pl_safe_date,
    pl_map_sexo,
    pl_map_tipo_documento,
    pl_map_boolean,
)


class CiudadanosProcessor(BulkProcessorBase):
    """Handles core citizen bulk operations."""

    def upsert_ciudadanos(self, df: pl.DataFrame) -> BulkOperationResult:
        """
        Bulk upsert citizens usando Polars puro + lazy evaluation.

        OPTIMIZACIONES:
        - Lazy evaluation para query optimization
        - Sin casts redundantes (Polars infiere tipos)
        - Sin loops Python (todo en expresiones Polars)
        - Conversiones en una sola pasada
        """
        start_time = self._get_current_timestamp()
        timestamp = self._get_current_timestamp()

        # LAZY EVALUATION - Polars optimiza todo el query plan
        ciudadanos_prepared = (
            df.lazy()
            .filter(pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null())
            .unique(subset=[Columns.CODIGO_CIUDADANO.name])
            .select([
                # IDs y campos numéricos - solo cast si es necesario
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                pl_safe_int(Columns.NRO_DOC.name).alias("numero_documento"),

                # Strings - solo strip, sin cast innecesario
                pl_clean_string(Columns.NOMBRE.name).alias("nombre"),
                pl_clean_string(Columns.APELLIDO.name).alias("apellido"),

                # Enums - mapeo directo en Polars (sin loops Python)
                pl_map_tipo_documento(Columns.TIPO_DOC.name).alias("tipo_documento"),
                pl_map_sexo(Columns.SEXO.name).alias("sexo_biologico"),
                pl_map_sexo(Columns.SEXO_AL_NACER.name).alias("sexo_biologico_al_nacer"),

                # Fechas
                pl_safe_date(Columns.FECHA_NACIMIENTO.name).alias("fecha_nacimiento"),

                # Opcionales con coalesce
                (
                    pl_clean_string(Columns.GENERO.name)
                    if Columns.GENERO.name in df.columns
                    else pl.lit(None)
                ).alias("genero_autopercibido"),
                (
                    pl_clean_string(Columns.ETNIA.name)
                    if Columns.ETNIA.name in df.columns
                    else pl.lit(None)
                ).alias("etnia"),

                # Timestamps
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            .with_columns([
                # Coalesce: si sexo_al_nacer es null, usar sexo_biologico
                pl.when(pl.col("sexo_biologico_al_nacer").is_null())
                  .then(pl.col("sexo_biologico"))
                  .otherwise(pl.col("sexo_biologico_al_nacer"))
                  .alias("sexo_biologico_al_nacer")
            ])
            .collect()  # Aquí se ejecuta todo el query plan optimizado
        )

        if ciudadanos_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Convertir a dicts para SQL insert (única conversión necesaria)
        ciudadanos_data = ciudadanos_prepared.to_dicts()

        # PostgreSQL UPSERT
        stmt = pg_insert(Ciudadano.__table__).values(ciudadanos_data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["codigo_ciudadano"],
            set_={
                "nombre": stmt.excluded.nombre,
                "apellido": stmt.excluded.apellido,
                "tipo_documento": stmt.excluded.tipo_documento,
                "numero_documento": stmt.excluded.numero_documento,
                "fecha_nacimiento": stmt.excluded.fecha_nacimiento,
                "sexo_biologico_al_nacer": stmt.excluded.sexo_biologico_al_nacer,
                "sexo_biologico": stmt.excluded.sexo_biologico,
                "genero_autopercibido": stmt.excluded.genero_autopercibido,
                "etnia": stmt.excluded.etnia,
                "updated_at": self._get_current_timestamp(),
            },
        )

        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(ciudadanos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )

    def upsert_ciudadanos_datos(
        self, df: pl.DataFrame
    ) -> BulkOperationResult:
        """
        Bulk upsert of CiudadanoDatos - OPTIMIZADO con Polars puro.

        OPTIMIZACIONES:
        - Lazy evaluation
        - Mapeo de booleans en Polars (no en Python)
        - Usa id_evento directamente desde df (ya viene del JOIN en main.py)
        """
        from app.domains.sujetos_epidemiologicos.ciudadanos_models import CiudadanoDatos

        start_time = self._get_current_timestamp()

        # LAZY EVALUATION - id_evento ya existe en df desde main.py
        datos_prepared = (
            df.lazy()
            .filter(
                pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null()
                & pl.col("id_evento").is_not_null()
            )
            .select([
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano"),
                pl.col("id_evento"),  # Ya existe desde el JOIN en main.py

                # Strings opcionales
                (
                    pl_clean_string(Columns.COBERTURA_SOCIAL.name)
                    if Columns.COBERTURA_SOCIAL.name in df.columns
                    else pl.lit(None)
                ).alias("cobertura_social_obra_social"),
                (
                    pl_clean_string(Columns.OCUPACION.name)
                    if Columns.OCUPACION.name in df.columns
                    else pl.lit(None)
                ).alias("ocupacion_laboral"),
                (
                    pl_clean_string(Columns.INFO_CONTACTO.name)
                    if Columns.INFO_CONTACTO.name in df.columns
                    else pl.lit(None)
                ).alias("informacion_contacto"),

                # Numéricos opcionales
                (
                    pl_safe_int(Columns.EDAD_ACTUAL.name)
                    if Columns.EDAD_ACTUAL.name in df.columns
                    else pl.lit(None)
                ).alias("edad_anos_actual"),

                # Booleans - mapeo en Polars (sin loops)
                (
                    pl_map_boolean(Columns.SE_DECLARA_PUEBLO_INDIGENA.name)
                    if Columns.SE_DECLARA_PUEBLO_INDIGENA.name in df.columns
                    else pl.lit(None)
                ).alias("es_declarado_pueblo_indigena"),
                (
                    pl_map_boolean(Columns.EMBARAZADA.name)
                    if Columns.EMBARAZADA.name in df.columns
                    else pl.lit(None)
                ).alias("es_embarazada"),

                pl.lit(self._get_current_timestamp()).alias("created_at"),
                pl.lit(self._get_current_timestamp()).alias("updated_at"),
            ])
            .collect()
        )

        if datos_prepared.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # Convertir a dicts para SQL
        datos_data = datos_prepared.to_dicts()

        # Bulk insert
        stmt = pg_insert(CiudadanoDatos.__table__).values(datos_data)
        upsert_stmt = stmt.on_conflict_do_nothing()
        self.context.session.execute(upsert_stmt)

        duration = (self._get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(datos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
