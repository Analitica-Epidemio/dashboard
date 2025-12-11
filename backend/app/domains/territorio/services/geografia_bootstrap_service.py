"""
Servicio para bootstrapping de jerarquía geográfica desde CSVs epidemiológicos.

RESPONSABILIDAD: Crear provincias/departamentos/localidades placeholder
cuando no existen en la BD para evitar perder datos del CSV.

IMPORTANTE: Este servicio crea datos TEMPORALES con nombres genéricos.
La data real debe importarse desde fuentes oficiales (INDEC, IGN).

OPTIMIZACIONES:
- Cache sin expiración usando functools.cache
- Bulk operations optimizadas
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Set

import polars as pl
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, col

from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia

logger = logging.getLogger(__name__)


# Configuración: Mapeo de columnas geográficas
# Formato: (localidad_col, departamento_col, provincia_col)
GRUPOS_COLUMNAS_GEO = [
    ("ID_LOC_INDEC_CLINICA", "ID_DEPTO_INDEC_CLINICA", "ID_PROV_INDEC_CLINICA"),
    ("ID_LOC_INDEC_DIAG", "ID_DEPTO_INDEC_DIAG", "ID_PROV_INDEC_DIAG"),
    ("ID_LOC_INDEC_MUESTRA", "ID_DEPTO_INDEC_MUESTRA", "ID_PROV_INDEC_MUESTRA"),
    ("ID_LOC_INDEC_EPI", "ID_DEPTO_INDEC_EPI", "ID_PROV_INDEC_EPI"),
    ("ID_LOC_INDEC_CARGA", "ID_DEPTO_INDEC_CARGA", "ID_PROV_INDEC_CARGA"),
    (
        "ID_LOC_INDEC_RESIDENCIA",
        "ID_DEPTO_INDEC_RESIDENCIA",
        "ID_PROV_INDEC_RESIDENCIA",
    ),
]


class GeografiaBootstrapService:
    """
    Servicio para crear jerarquía geográfica placeholder desde CSVs.

    Flujo: Provincias → Departamentos → Localidades
    """

    def __init__(self, session: Session):
        self.session = session

    def asegurar_geografia_existe(self, df: pl.DataFrame) -> None:
        """
        Asegura que toda la jerarquía geográfica del CSV existe en BD.

        Crea placeholders para IDs que no existen.
        Orden: 1) Provincias, 2) Departamentos, 3) Localidades
        """
        logger.info("Verificando jerarquía geográfica")

        # 1. Provincias (nivel superior)
        ids_provincia = self._extraer_ids_provincia(df)
        self._asegurar_provincias_existen(ids_provincia)

        # 2. Departamentos (requiere provincias)
        depto_a_prov = self._extraer_mapeos_departamento(df)
        self._asegurar_departamentos_existen(depto_a_prov)

        # 3. Localidades (requiere departamentos)
        loc_a_depto = self._extraer_mapeos_localidad(df)
        ids_loc_viaje = self._extraer_ids_localidad_viaje(df)
        self._asegurar_localidades_existen(loc_a_depto, ids_loc_viaje)

        logger.info("Jerarquía geográfica verificada")

    # ===== EXTRACCIÓN DE IDs DESDE CSV =====

    def _extraer_ids_provincia(self, df: pl.DataFrame) -> Set[int]:
        """Extrae todos los IDs de provincia únicos del CSV."""
        ids_provincia = set()

        # Todas las columnas de provincia
        cols_prov = [grupo[2] for grupo in GRUPOS_COLUMNAS_GEO]
        cols_prov.append("ID_PROV_INDEC_VIAJE")  # También viajes

        for col_name in cols_prov:
            if col_name in df.columns:
                ids = df[col_name].drop_nulls().cast(pl.Int64).unique()
                ids_provincia.update(int(x) for x in ids.to_list() if x is not None)

        return ids_provincia

    def _extraer_mapeos_departamento(self, df: pl.DataFrame) -> Dict[int, int]:
        """
        Extrae mapeo: departamento_id → provincia_id

        Returns:
            {depto_indec_id: provincia_indec_id}
        """
        mapeos = {}

        for col_loc, col_dep, col_prov in GRUPOS_COLUMNAS_GEO:
            if col_dep in df.columns and col_prov in df.columns:
                # Obtener pares únicos (departamento, provincia)
                pares = df.select([col_dep, col_prov]).drop_nulls().unique()

                for fila in pares.iter_rows(named=True):
                    id_dep = self._int_seguro(fila[col_dep])
                    id_prov = self._int_seguro(fila[col_prov])

                    if id_dep and id_prov:
                        mapeos[id_dep] = id_prov

        return mapeos

    def _extraer_mapeos_localidad(self, df: pl.DataFrame) -> Dict[int, int]:
        """
        Extrae mapeo: localidad_id → departamento_id

        Returns:
            {localidad_indec_id: departamento_indec_id}
        """
        mapeos = {}

        for col_loc, col_dep, _ in GRUPOS_COLUMNAS_GEO:
            if col_loc in df.columns and col_dep in df.columns:
                # Obtener pares únicos (localidad, departamento)
                pares = df.select([col_loc, col_dep]).drop_nulls().unique()

                for fila in pares.iter_rows(named=True):
                    id_loc = self._int_seguro(fila[col_loc])
                    id_dep = self._int_seguro(fila[col_dep])

                    if id_loc and id_dep:
                        mapeos[id_loc] = id_dep

        return mapeos

    def _extraer_ids_localidad_viaje(self, df: pl.DataFrame) -> Set[int]:
        """
        Extrae IDs de localidades de viaje (sin departamento conocido).

        Las localidades de viaje pueden no tener departamento asociado.
        """
        if "ID_LOC_INDEC_VIAJE" not in df.columns:
            return set()

        ids = df["ID_LOC_INDEC_VIAJE"].drop_nulls().cast(pl.Int64).unique()
        return set(int(x) for x in ids.to_list() if x is not None)

    # ===== CREACIÓN DE ENTIDADES =====

    def _asegurar_provincias_existen(self, ids_provincia: Set[int]) -> None:
        """Crea provincias placeholder para IDs que no existen."""
        if not ids_provincia:
            return

        # Verificar existentes
        stmt = select(col(Provincia.id_provincia_indec)).where(
            col(Provincia.id_provincia_indec).in_(list(ids_provincia))
        )
        existentes = {id_indec for (id_indec,) in self.session.execute(stmt).all()}

        # Crear faltantes
        nuevas = [
            {
                "id_provincia_indec": id_prov,
                "nombre": f"Provincia INDEC {id_prov}",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            for id_prov in ids_provincia
            if id_prov not in existentes
        ]

        if nuevas:
            provincia_table = sa_inspect(Provincia).local_table
            stmt = pg_insert(provincia_table).values(nuevas)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creadas {len(nuevas)} provincias placeholder")

    def _asegurar_departamentos_existen(self, depto_a_prov: Dict[int, int]) -> None:
        """Crea departamentos placeholder con sus provincias asociadas."""
        if not depto_a_prov:
            return

        # Verificar existentes
        stmt = select(col(Departamento.id_departamento_indec)).where(
            col(Departamento.id_departamento_indec).in_(list(depto_a_prov.keys()))
        )
        existentes = {id_indec for (id_indec,) in self.session.execute(stmt).all()}

        # Crear faltantes
        nuevos = [
            {
                "id_departamento_indec": id_dep,
                "nombre": f"Departamento INDEC {id_dep}",
                "id_provincia_indec": id_prov,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            for id_dep, id_prov in depto_a_prov.items()
            if id_dep not in existentes
        ]

        if nuevos:
            departamento_table = sa_inspect(Departamento).local_table
            stmt = pg_insert(departamento_table).values(nuevos)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creados {len(nuevos)} departamentos placeholder")

    def _asegurar_localidades_existen(
        self, loc_a_depto: Dict[int, int], ids_loc_viaje: Set[int]
    ) -> None:
        """
        Crea localidades placeholder.

        Args:
            loc_a_depto: Localidades normales con departamento
            ids_loc_viaje: Localidades de viaje (sin departamento)
        """
        todas_localidades = set(loc_a_depto.keys()) | ids_loc_viaje

        if not todas_localidades:
            return

        # Verificar existentes
        stmt = select(
            col(Localidad.id_localidad_indec), col(Localidad.id_departamento_indec)
        ).where(col(Localidad.id_localidad_indec).in_(list(todas_localidades)))
        existentes = {
            id_loc: id_dep for id_loc, id_dep in self.session.execute(stmt).all()
        }

        # Crear localidades faltantes
        nuevas = []

        # 1. Localidades normales con departamento
        for id_loc, dep_indec in loc_a_depto.items():
            if id_loc not in existentes:
                nuevas.append(
                    {
                        "id_localidad_indec": id_loc,
                        "nombre": f"Localidad INDEC {id_loc}",
                        "id_departamento_indec": dep_indec,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    }
                )

        # 2. Localidades de viaje sin departamento
        for id_loc in ids_loc_viaje:
            if id_loc not in existentes:
                nuevas.append(
                    {
                        "id_localidad_indec": id_loc,
                        "nombre": f"Localidad Viaje INDEC {id_loc}",
                        "id_departamento_indec": None,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    }
                )

        if nuevas:
            localidad_table = sa_inspect(Localidad).local_table
            stmt = pg_insert(localidad_table).values(nuevas)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creadas {len(nuevas)} localidades placeholder")

    # ===== HELPERS =====

    @staticmethod
    def _int_seguro(valor: Any) -> int | None:
        """Conversión segura a int."""
        if valor is None:
            return None
        try:
            return int(float(valor))
        except (ValueError, TypeError):
            return None
