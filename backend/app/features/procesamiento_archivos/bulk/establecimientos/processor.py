"""
Bulk processor para establecimientos de salud.

RESPONSABILIDAD: Crear/actualizar establecimientos desde CSV.
Soporta 5 tipos: CLINICA, DIAGNOSTICO, MUESTRA, EPIDEMIOLOGIA, CARGA.
"""

from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.services.geografia_bootstrap_service import (
    GeografiaBootstrapService,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase


# Configuración: Mapeo de columnas de establecimientos
# Formato: (columna_nombre, columna_localidad)
ESTABLECIMIENTO_COLUMN_GROUPS = [
    (Columns.ESTAB_CLINICA, Columns.ID_LOC_INDEC_CLINICA),
    (Columns.ESTABLECIMIENTO_DIAG, Columns.ID_LOC_INDEC_DIAG),
    (Columns.ESTABLECIMIENTO_MUESTRA, Columns.ID_LOC_INDEC_MUESTRA),
    (Columns.ESTABLECIMIENTO_EPI, Columns.ID_LOC_INDEC_EPI),
    (Columns.ESTABLECIMIENTO_CARGA, Columns.ID_LOC_INDEC_CARGA),
]


class EstablecimientosProcessor(BulkProcessorBase):
    """
    Procesador de establecimientos de salud.

    Flujo:
    1. Asegurar jerarquía geográfica existe (delega a GeografiaBootstrapService)
    2. Extraer establecimientos únicos del CSV
    3. Crear/actualizar en BD
    4. Retornar mapeo nombre → id
    """

    def upsert_establecimientos(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Procesa establecimientos de todos los tipos.

        Returns:
            Dict mapping nombre_establecimiento → id
        """
        # Paso 1: Asegurar jerarquía geográfica existe
        geo_service = GeografiaBootstrapService(self.context.session)
        geo_service.ensure_geografia_exists(df)

        # Paso 2: Extraer establecimientos únicos (nombre, localidad)
        establecimientos_set = self._extract_establecimientos_from_df(df)

        if not establecimientos_set:
            return {}

        # Paso 3: Upsert establecimientos
        return self._upsert_establecimientos(establecimientos_set)

    # ===== EXTRACCIÓN =====

    def _extract_establecimientos_from_df(self, df: pd.DataFrame) -> set:
        """
        Extrae establecimientos únicos de TODAS las columnas.

        Returns:
            Set de tuplas (nombre, id_localidad)
        """
        establecimientos = set()

        # OPTIMIZACIÓN: Vectorizado para evitar iterrows() (10-50x más rápido)
        for nombre_col, localidad_col in ESTABLECIMIENTO_COLUMN_GROUPS:
            if nombre_col not in df.columns or localidad_col not in df.columns:
                continue

            # Extraer pares válidos (nombre, localidad)
            pares = df[[nombre_col, localidad_col]].dropna(subset=[nombre_col]).copy()

            if pares.empty:
                continue

            # Vectorizado: limpiar todos los nombres y convertir IDs de una vez
            pares['nombre_limpio'] = pares[nombre_col].apply(lambda x: self._clean_string(x))
            pares['id_loc_int'] = pares[localidad_col].apply(lambda x: self._safe_int(x))

            # Filtrar solo los que tienen nombre limpio
            pares_validos = pares[pares['nombre_limpio'].notna()]

            # Agregar al set usando vectorización
            for nombre, id_loc in zip(pares_validos['nombre_limpio'], pares_validos['id_loc_int']):
                establecimientos.add((nombre, id_loc))

        return establecimientos

    # ===== UPSERT =====

    def _upsert_establecimientos(self, establecimientos_set: set) -> Dict[str, int]:
        """
        Crea/actualiza establecimientos y retorna mapeo.

        Args:
            establecimientos_set: Set de (nombre, id_localidad)

        Returns:
            {nombre: id}
        """
        nombres = [nombre for nombre, _ in establecimientos_set]

        # Verificar existentes
        existing_mapping = self._get_existing_establecimientos(nombres)

        # Crear nuevos
        nuevos = [
            {
                "nombre": nombre,
                "id_localidad_indec": id_localidad,
                "created_at": self._get_current_timestamp(),
                "updated_at": self._get_current_timestamp(),
            }
            for nombre, id_localidad in establecimientos_set
            if nombre not in existing_mapping
        ]

        if nuevos:
            stmt = pg_insert(Establecimiento.__table__).values(nuevos)
            self.context.session.execute(stmt.on_conflict_do_nothing())

            # Re-obtener mapeo completo
            existing_mapping = self._get_existing_establecimientos(nombres)

        return existing_mapping

    def _get_existing_establecimientos(self, nombres: list) -> Dict[str, int]:
        """Obtiene mapeo de establecimientos existentes."""
        if not nombres:
            return {}

        stmt = select(Establecimiento.id, Establecimiento.nombre).where(
            Establecimiento.nombre.in_(nombres)
        )

        return {
            nombre: estab_id
            for estab_id, nombre in self.context.session.execute(stmt).all()
        }
