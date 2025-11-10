"""
Bulk processor para establecimientos de salud - POLARS PURO OPTIMIZADO.

RESPONSABILIDAD: Crear/actualizar establecimientos desde CSV.
Soporta 5 tipos: CLINICA, DIAGNOSTICO, MUESTRA, EPIDEMIOLOGIA, CARGA.

ESTRATEGIA DE MATCHING:
1. Busca por codigo_snvs (mapping oficial SNVS → IGN cargado por seed)
2. Si no encuentra, busca por nombre (case-insensitive)
3. Si no encuentra match: crea nuevo establecimiento con source='SNVS'

El mapping SNVS → IGN se carga en la BD mediante el seed script, que lee
el archivo establecimientos_mapping_final.json y actualiza el campo codigo_snvs
de los establecimientos IGN con los códigos correspondientes del SNVS.

OPTIMIZACIONES:
- Lazy evaluation con Polars para todas las transformaciones
- Sin loops Python con .apply() o .iterrows()
- Expresiones Polars vectorizadas para limpiar datos
- Conversión única a set al final
"""

import polars as pl
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.services.geografia_bootstrap_service import (
    GeografiaBootstrapService,
)

from ...config.columns import Columns
from ..shared import BulkProcessorBase, pl_safe_int, pl_clean_string


# Configuración: Mapeo de columnas de establecimientos
# Formato: (columna_id_snvs, columna_nombre, columna_localidad)
ESTABLECIMIENTO_COLUMN_GROUPS = [
    (Columns.ID_ESTAB_CLINICA, Columns.ESTAB_CLINICA, Columns.ID_LOC_INDEC_CLINICA),
    (Columns.ID_ESTABLECIMIENTO_DIAG, Columns.ESTABLECIMIENTO_DIAG, Columns.ID_LOC_INDEC_DIAG),
    (Columns.ID_ESTABLECIMIENTO_MUESTRA, Columns.ESTABLECIMIENTO_MUESTRA, Columns.ID_LOC_INDEC_MUESTRA),
    (Columns.ID_ORIGEN, Columns.ESTABLECIMIENTO_EPI, Columns.ID_LOC_INDEC_EPI),
    (None, Columns.ESTABLECIMIENTO_CARGA, Columns.ID_LOC_INDEC_CARGA),  # CARGA no tiene columna ID
]


class EstablecimientosProcessor(BulkProcessorBase):
    """
    Procesador de establecimientos de salud.

    Flujo:
    1. Asegurar jerarquía geográfica existe (delega a GeografiaBootstrapService)
    2. Extraer establecimientos únicos del CSV
    3. Buscar en BD establecimientos IGN por nombre (case-insensitive)
    4. Si match: usar establecimiento IGN existente
    5. Si no match: crear nuevo con source='SNVS'
    6. Retornar mapeo nombre → id
    """

    def upsert_establecimientos(self, df: pl.DataFrame) -> dict[str, int]:
        """
        Procesa establecimientos de todos los tipos - POLARS PURO.

        Returns:
            Dict mapping nombre_establecimiento → id
        """
        # Paso 1: Asegurar jerarquía geográfica existe
        geo_service = GeografiaBootstrapService(self.context.session)
        geo_service.ensure_geografia_exists(df)

        # Paso 2: Extraer establecimientos únicos (nombre, localidad)
        establecimientos_set = self._extract_establecimientos_from_df(df)

        self.logger.info(f"🏥 Establecimientos únicos extraídos del CSV: {len(establecimientos_set)}")
        if establecimientos_set:
            # Log algunos ejemplos
            ejemplos = list(establecimientos_set)[:5]
            self.logger.info(f"📋 Ejemplos: {ejemplos}")

        if not establecimientos_set:
            self.logger.warning("⚠️  No se encontraron establecimientos en el CSV")
            return {}

        # Paso 3: Upsert establecimientos
        mapping = self._upsert_establecimientos(establecimientos_set)
        self.logger.info(f"✅ Mapping de establecimientos creado: {len(mapping)} establecimientos mapeados")
        return mapping

    # ===== EXTRACCIÓN =====

    def _extract_establecimientos_from_df(self, df: pl.DataFrame) -> set:
        """
        Extrae establecimientos únicos de TODAS las columnas - POLARS PURO.

        OPTIMIZACIONES:
        - Lazy evaluation para cada grupo de columnas
        - Expresiones Polars para limpieza (sin .apply())
        - Conversión única a set al final (sin .iterrows())
        - 10-100x más rápido que pandas

        Returns:
            Set de tuplas (id_snvs, nombre, id_localidad)
            - id_snvs puede ser None si no hay columna ID para ese tipo
            - nombre puede ser None si no hay nombre en el CSV
        """
        # Lista para acumular DataFrames de cada grupo
        establecimientos_dfs = []

        for id_col, nombre_col, localidad_col in ESTABLECIMIENTO_COLUMN_GROUPS:
            # Obtener nombres de columnas (son objetos Column, necesitamos .name)
            nombre_col_name = nombre_col.name if hasattr(nombre_col, 'name') else nombre_col
            localidad_col_name = localidad_col.name if hasattr(localidad_col, 'name') else localidad_col
            id_col_name = id_col.name if (id_col and hasattr(id_col, 'name')) else id_col

            # Verificar que columnas necesarias existen
            if nombre_col_name not in df.columns or localidad_col_name not in df.columns:
                continue

            has_id_col = id_col_name is not None and id_col_name in df.columns

            # LAZY EVALUATION - Procesar con expresiones Polars
            if has_id_col:
                pares_df = (
                    df.lazy()
                    .filter(
                        # Al menos ID o nombre debe estar presente
                        pl.col(id_col_name).is_not_null() | pl.col(nombre_col_name).is_not_null()
                    )
                    .select([
                        # Limpiar ID de SNVS: convertir a int, luego a string
                        (
                            pl.when(pl_safe_int(id_col_name).is_not_null())
                            .then(pl_safe_int(id_col_name).cast(pl.Utf8))
                            .otherwise(None)
                        ).alias("id_snvs_limpio"),
                        # Limpiar nombre: strip + uppercase
                        (
                            pl_clean_string(nombre_col_name).str.to_uppercase()
                        ).alias("nombre_limpio"),
                        # Convertir localidad a int
                        pl_safe_int(localidad_col_name).alias("id_loc_int"),
                    ])
                    .filter(
                        # Filtrar registros que tienen al menos ID o nombre válidos
                        pl.col("id_snvs_limpio").is_not_null() | pl.col("nombre_limpio").is_not_null()
                    )
                    .collect()
                )
            else:
                # Sin columna ID
                pares_df = (
                    df.lazy()
                    .filter(pl.col(nombre_col_name).is_not_null())
                    .select([
                        pl.lit(None, dtype=pl.Utf8).alias("id_snvs_limpio"),
                        pl_clean_string(nombre_col_name).str.to_uppercase().alias("nombre_limpio"),
                        pl_safe_int(localidad_col_name).alias("id_loc_int"),
                    ])
                    .filter(pl.col("nombre_limpio").is_not_null())
                    .collect()
                )

            if pares_df.height > 0:
                establecimientos_dfs.append(pares_df)

        # Concatenar todos los DataFrames y convertir a set
        if not establecimientos_dfs:
            return set()

        # Concatenar y obtener únicos
        establecimientos_df = pl.concat(establecimientos_dfs).unique()

        # Convertir a set de tuplas - UNA SOLA conversión
        establecimientos_set = set(
            (row["id_snvs_limpio"], row["nombre_limpio"], row["id_loc_int"])
            for row in establecimientos_df.iter_rows(named=True)
        )

        return establecimientos_set

    # ===== UPSERT =====

    def _upsert_establecimientos(self, establecimientos_set: set) -> dict[str, int]:
        """
        Crea/actualiza establecimientos y retorna mapeo.

        ESTRATEGIA:
        1. Buscar por codigo_snvs (ID de SNVS del CSV)
        2. Si no existe por codigo_snvs, buscar por nombre (case-insensitive)
        3. Si no existe: crear nuevo con source='SNVS'

        Args:
            establecimientos_set: Set de (id_snvs, nombre, id_localidad)

        Returns:
            {clave_busqueda: id} donde clave_busqueda es id_snvs o nombre según lo que se usó
        """
        # Extraer IDs y nombres
        ids_snvs = [id_snvs for id_snvs, nombre, _ in establecimientos_set if id_snvs]
        nombres = [nombre for id_snvs, nombre, _ in establecimientos_set if nombre]

        self.logger.info(f"📋 Procesando {len(establecimientos_set)} establecimientos únicos:")
        self.logger.info(f"   - {len(ids_snvs)} con ID de SNVS")
        self.logger.info(f"   - {len(nombres)} con nombre")

        # PASO 1: Buscar por codigo_snvs (IDs del CSV)
        existing_by_codigo = self._get_establecimientos_by_codigo_snvs(ids_snvs)
        self.logger.info(f"🔍 Paso 1 - Búsqueda por codigo_snvs: {len(existing_by_codigo)} matches")

        # PASO 2: Para los que NO se encontraron por codigo_snvs, buscar por nombre
        # Construir lista de establecimientos sin match por código
        ids_con_match = set(existing_by_codigo.keys())
        establecimientos_sin_match = [
            (id_snvs, nombre) for id_snvs, nombre, _ in establecimientos_set
            if id_snvs not in ids_con_match
        ]
        nombres_sin_match = [nombre for _, nombre in establecimientos_sin_match if nombre]

        self.logger.info(f"🔍 Paso 2 - Establecimientos sin match por código: {len(establecimientos_sin_match)}")
        existing_by_nombre = self._get_existing_establecimientos(nombres_sin_match)
        self.logger.info(f"✓ Encontrados por nombre: {len(existing_by_nombre)}")

        # Combinar ambos mappings
        existing_mapping = {**existing_by_nombre, **existing_by_codigo}
        self.logger.info(f"📊 Total matches encontrados: {len(existing_mapping)}")

        # PASO 3: Crear nuevos establecimientos SNVS (los que NO existen en BD)
        timestamp = self._get_current_timestamp()
        nuevos = []
        for id_snvs, nombre, id_localidad in establecimientos_set:
            # Usar ID o nombre como clave de búsqueda
            clave = id_snvs if id_snvs else nombre

            # Si no está en existing_mapping, crear nuevo
            if clave not in existing_mapping:
                nuevo = {
                    "nombre": nombre or f"Establecimiento SNVS {id_snvs}",  # Usar ID si no hay nombre
                    "id_localidad_indec": id_localidad,
                    "source": "SNVS",
                    "codigo_snvs": id_snvs,  # Solo guardar el ID numérico de SNVS, no el nombre
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                nuevos.append(nuevo)

        if nuevos:
            self.logger.info(f"➕ Creando {len(nuevos)} nuevos establecimientos con source='SNVS'")
            if len(nuevos) <= 5:
                self.logger.info(f"   Ejemplos: {[(e['codigo_snvs'], e['nombre']) for e in nuevos]}")
            stmt = pg_insert(Establecimiento.__table__).values(nuevos)
            self.context.session.execute(stmt.on_conflict_do_nothing())

            # Re-obtener mapeo completo
            existing_mapping = {
                **self._get_establecimientos_by_codigo_snvs(ids_snvs),
                **self._get_existing_establecimientos(nombres),
            }
            self.logger.info(f"✅ Mapping actualizado: {len(existing_mapping)} establecimientos")
        else:
            self.logger.info(f"ℹ️  Todos los establecimientos ya existen en BD")

        return existing_mapping

    def _get_establecimientos_by_codigo_snvs(self, ids_snvs: list) -> dict[str, int]:
        """
        Busca establecimientos por codigo_snvs (IDs numéricos de SNVS).

        Prioriza este método sobre búsqueda por nombre ya que usa el
        mapping oficial cargado desde establecimientos_mapping_final.json.

        Args:
            ids_snvs: Lista de IDs de SNVS (strings numéricos, ej: "503", "215")

        Returns:
            {id_snvs: id_establecimiento}
        """
        if not ids_snvs:
            return {}

        # Query buscando por codigo_snvs (ahora son IDs numéricos)
        stmt = select(Establecimiento.id, Establecimiento.codigo_snvs).where(
            Establecimiento.codigo_snvs.in_(ids_snvs)
        )

        # Retornar mapeo id_snvs → id_establecimiento
        return {
            codigo_snvs: estab_id
            for estab_id, codigo_snvs in self.context.session.execute(stmt).all()
            if codigo_snvs  # Filtrar NULLs
        }

    def _get_existing_establecimientos(self, nombres: list) -> dict[str, int]:
        """
        Obtiene mapeo de establecimientos existentes por nombre.

        Usa matching case-insensitive para encontrar establecimientos
        cuyos nombres coincidan ignorando mayúsculas/minúsculas.

        NOTA: Este método es fallback. Se prefiere _get_establecimientos_by_codigo_snvs
        que usa el mapping oficial IGN.
        """
        if not nombres:
            return {}

        # Convertir nombres a uppercase para matching case-insensitive
        nombres_upper = [n.upper() for n in nombres]

        # Query con UPPER() para matching case-insensitive
        stmt = select(Establecimiento.id, Establecimiento.nombre).where(
            func.upper(Establecimiento.nombre).in_(nombres_upper)
        )

        # Retornar mapeo usando el nombre en uppercase como key
        return {
            nombre.upper(): estab_id
            for estab_id, nombre in self.context.session.execute(stmt).all()
        }
