"""
Bulk processor para contactos y notificaciones epidemiológicas.

POLARS PURO - OPTIMIZADO.
"""

import polars as pl
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.atencion_medica.investigaciones_models import ContactosNotificacion

from ...config.columns import Columns
from ..shared import (
    BulkProcessorBase,
    BulkOperationResult,
    pl_safe_int,
    pl_clean_string,
    pl_map_boolean,
    get_current_timestamp,
)


class ContactosProcessor(BulkProcessorBase):
    """Procesa contactos y notificaciones de casos epidemiológicos."""

    def upsert_contactos_notificaciones(self, df: pl.DataFrame) -> BulkOperationResult:
        """Bulk upsert de contactos y notificaciones - POLARS PURO."""
        start_time = get_current_timestamp()

        # POLARS: Filtrar registros con al menos un campo de contacto y con id_evento válido
        contactos_df = df.filter(
            (
                (pl.col(Columns.CONTACTO_CON_CONFIR.name).is_not_null() if Columns.CONTACTO_CON_CONFIR.name in df.columns else pl.lit(False))
                | (pl.col(Columns.CONTACTO_CON_SOSPECHOSO.name).is_not_null() if Columns.CONTACTO_CON_SOSPECHOSO.name in df.columns else pl.lit(False))
                | (pl.col(Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name).is_not_null() if Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name in df.columns else pl.lit(False))
                | (pl.col(Columns.CONTACTOS_MENORES_1.name).is_not_null() if Columns.CONTACTOS_MENORES_1.name in df.columns else pl.lit(False))
                | (pl.col(Columns.CONTACTOS_VACUNADOS.name).is_not_null() if Columns.CONTACTOS_VACUNADOS.name in df.columns else pl.lit(False))
                | (pl.col(Columns.CONTACTO_EMBARAZADAS.name).is_not_null() if Columns.CONTACTO_EMBARAZADAS.name in df.columns else pl.lit(False))
            )
            & pl.col("id_evento").is_not_null()  # id_evento ya viene del JOIN en main.py
        )

        if contactos_df.height == 0:
            return BulkOperationResult(0, 0, 0, [], 0.0)

        # POLARS: Preparar timestamp
        timestamp = get_current_timestamp()

        # POLARS: Preparar datos - id_evento ya está disponible en el DataFrame
        contactos_prepared = (
            contactos_df.lazy()
            .select([
                pl.col("id_evento"),  # Usar id_evento directamente del DataFrame
                # Boolean mappings usando pl_map_boolean helper
                (pl_map_boolean(Columns.CONTACTO_CON_CONFIR.name) if Columns.CONTACTO_CON_CONFIR.name in contactos_df.columns else pl.lit(None)).alias("hubo_contacto_con_caso_confirmado"),
                (pl_map_boolean(Columns.CONTACTO_CON_SOSPECHOSO.name) if Columns.CONTACTO_CON_SOSPECHOSO.name in contactos_df.columns else pl.lit(None)).alias("hubo_contacto_con_caso_sospechoso"),
                # String cleaning (cast primero porque puede venir como numérico)
                (pl.col(Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name).cast(pl.Utf8).str.strip_chars() if Columns.CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS.name in contactos_df.columns else pl.lit(None)).alias("contactos_relevados_contactos_detectados"),
                # Integer fields
                (pl_safe_int(Columns.CONTACTOS_MENORES_1.name) if Columns.CONTACTOS_MENORES_1.name in contactos_df.columns else pl.lit(None)).alias("cantidad_contactos_menores_un_anio"),
                (pl_safe_int(Columns.CONTACTOS_VACUNADOS.name) if Columns.CONTACTOS_VACUNADOS.name in contactos_df.columns else pl.lit(None)).alias("cantidad_contactos_vacunados"),
                (pl_safe_int(Columns.CONTACTO_EMBARAZADAS.name) if Columns.CONTACTO_EMBARAZADAS.name in contactos_df.columns else pl.lit(None)).alias("cantidad_contactos_embarazadas"),
                # Timestamps
                pl.lit(timestamp).alias("created_at"),
                pl.lit(timestamp).alias("updated_at"),
            ])
            # Filtrar registros con al menos un campo relevante (POLARS PURO)
            .filter(
                pl.col("hubo_contacto_con_caso_confirmado").is_not_null()
                | pl.col("hubo_contacto_con_caso_sospechoso").is_not_null()
                | pl.col("contactos_relevados_contactos_detectados").is_not_null()
                | pl.col("cantidad_contactos_menores_un_anio").is_not_null()
                | pl.col("cantidad_contactos_vacunados").is_not_null()
                | pl.col("cantidad_contactos_embarazadas").is_not_null()
            )
            .collect()
        )

        # ÚNICA conversión a dicts al final
        contactos_data = contactos_prepared.to_dicts()

        # Bulk insert
        if contactos_data:
            stmt = pg_insert(ContactosNotificacion.__table__).values(contactos_data)
            self.context.session.execute(stmt.on_conflict_do_nothing())

        duration = (get_current_timestamp() - start_time).total_seconds()

        return BulkOperationResult(
            inserted_count=len(contactos_data),
            updated_count=0,
            skipped_count=0,
            errors=[],
            duration_seconds=duration,
        )
