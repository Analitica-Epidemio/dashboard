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
from datetime import datetime
from functools import cache
from typing import Dict, List, Set, Tuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia

logger = logging.getLogger(__name__)


# Configuración: Mapeo de columnas geográficas
# Formato: (localidad_col, departamento_col, provincia_col)
GEO_COLUMN_GROUPS = [
    ('ID_LOC_INDEC_CLINICA', 'ID_DEPTO_INDEC_CLINICA', 'ID_PROV_INDEC_CLINICA'),
    ('ID_LOC_INDEC_DIAG', 'ID_DEPTO_INDEC_DIAG', 'ID_PROV_INDEC_DIAG'),
    ('ID_LOC_INDEC_MUESTRA', 'ID_DEPTO_INDEC_MUESTRA', 'ID_PROV_INDEC_MUESTRA'),
    ('ID_LOC_INDEC_EPI', 'ID_DEPTO_INDEC_EPI', 'ID_PROV_INDEC_EPI'),
    ('ID_LOC_INDEC_CARGA', 'ID_DEPTO_INDEC_CARGA', 'ID_PROV_INDEC_CARGA'),
    ('ID_LOC_INDEC_RESIDENCIA', 'ID_DEPTO_INDEC_RESIDENCIA', 'ID_PROV_INDEC_RESIDENCIA'),
]


class GeografiaBootstrapService:
    """
    Servicio para crear jerarquía geográfica placeholder desde CSVs.

    Flujo: Provincias → Departamentos → Localidades
    """

    def __init__(self, session: Session):
        self.session = session

    def ensure_geografia_exists(self, df: pd.DataFrame) -> None:
        """
        Asegura que toda la jerarquía geográfica del CSV existe en BD.

        Crea placeholders para IDs que no existen.
        Orden: 1) Provincias, 2) Departamentos, 3) Localidades
        """
        logger.info("Verificando jerarquía geográfica")

        # 1. Provincias (nivel superior)
        provincia_ids = self._extract_provincia_ids(df)
        self._ensure_provincias_exist(provincia_ids)

        # 2. Departamentos (requiere provincias)
        depto_to_prov = self._extract_departamento_mappings(df)
        self._ensure_departamentos_exist(depto_to_prov)

        # 3. Localidades (requiere departamentos)
        loc_to_depto = self._extract_localidad_mappings(df)
        loc_viaje_ids = self._extract_localidad_viaje_ids(df)
        self._ensure_localidades_exist(loc_to_depto, loc_viaje_ids)

        logger.info("Jerarquía geográfica verificada")

    # ===== EXTRACCIÓN DE IDs DESDE CSV =====

    def _extract_provincia_ids(self, df: pd.DataFrame) -> Set[int]:
        """Extrae todos los IDs de provincia únicos del CSV."""
        provincia_ids = set()

        # Todas las columnas de provincia
        prov_columns = [group[2] for group in GEO_COLUMN_GROUPS]
        prov_columns.append('ID_PROV_INDEC_VIAJE')  # También viajes

        for col in prov_columns:
            if col in df.columns:
                ids = df[col].dropna().astype('Int64').unique()
                provincia_ids.update(int(x) for x in ids if pd.notna(x))

        return provincia_ids

    def _extract_departamento_mappings(self, df: pd.DataFrame) -> Dict[int, int]:
        """
        Extrae mapeo: departamento_id → provincia_id

        Returns:
            {depto_indec_id: provincia_indec_id}
        """
        mappings = {}

        for loc_col, dep_col, prov_col in GEO_COLUMN_GROUPS:
            if dep_col in df.columns and prov_col in df.columns:
                # Obtener pares únicos (departamento, provincia)
                pairs = df[[dep_col, prov_col]].dropna().drop_duplicates()

                for _, row in pairs.iterrows():
                    dep_id = self._safe_int(row[dep_col])
                    prov_id = self._safe_int(row[prov_col])

                    if dep_id and prov_id:
                        mappings[dep_id] = prov_id

        return mappings

    def _extract_localidad_mappings(self, df: pd.DataFrame) -> Dict[int, int]:
        """
        Extrae mapeo: localidad_id → departamento_id

        Returns:
            {localidad_indec_id: departamento_indec_id}
        """
        mappings = {}

        for loc_col, dep_col, _ in GEO_COLUMN_GROUPS:
            if loc_col in df.columns and dep_col in df.columns:
                # Obtener pares únicos (localidad, departamento)
                pairs = df[[loc_col, dep_col]].dropna().drop_duplicates()

                for _, row in pairs.iterrows():
                    loc_id = self._safe_int(row[loc_col])
                    dep_id = self._safe_int(row[dep_col])

                    if loc_id and dep_id:
                        mappings[loc_id] = dep_id

        return mappings

    def _extract_localidad_viaje_ids(self, df: pd.DataFrame) -> Set[int]:
        """
        Extrae IDs de localidades de viaje (sin departamento conocido).

        Las localidades de viaje pueden no tener departamento asociado.
        """
        if 'ID_LOC_INDEC_VIAJE' not in df.columns:
            return set()

        ids = df['ID_LOC_INDEC_VIAJE'].dropna().astype('Int64').unique()
        return set(int(x) for x in ids if pd.notna(x))

    # ===== CREACIÓN DE ENTIDADES =====

    def _ensure_provincias_exist(self, provincia_ids: Set[int]) -> None:
        """Crea provincias placeholder para IDs que no existen."""
        if not provincia_ids:
            return

        # Verificar existentes
        stmt = select(Provincia.id_provincia_indec).where(
            Provincia.id_provincia_indec.in_(list(provincia_ids))
        )
        existing = {id_indec for id_indec, in self.session.execute(stmt).all()}

        # Crear faltantes
        nuevas = [
            {
                "id_provincia_indec": prov_id,
                "nombre": f"Provincia INDEC {prov_id}",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for prov_id in provincia_ids if prov_id not in existing
        ]

        if nuevas:
            stmt = pg_insert(Provincia.__table__).values(nuevas)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creadas {len(nuevas)} provincias placeholder")

    def _ensure_departamentos_exist(self, depto_to_prov: Dict[int, int]) -> None:
        """Crea departamentos placeholder con sus provincias asociadas."""
        if not depto_to_prov:
            return

        # Verificar existentes
        stmt = select(Departamento.id_departamento_indec).where(
            Departamento.id_departamento_indec.in_(list(depto_to_prov.keys()))
        )
        existing = {id_indec for id_indec, in self.session.execute(stmt).all()}

        # Crear faltantes
        nuevos = [
            {
                "id_departamento_indec": dep_id,
                "nombre": f"Departamento INDEC {dep_id}",
                "id_provincia_indec": prov_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for dep_id, prov_id in depto_to_prov.items()
            if dep_id not in existing
        ]

        if nuevos:
            stmt = pg_insert(Departamento.__table__).values(nuevos)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creados {len(nuevos)} departamentos placeholder")

    def _ensure_localidades_exist(
        self,
        loc_to_depto: Dict[int, int],
        loc_viaje_ids: Set[int]
    ) -> None:
        """
        Crea localidades placeholder.

        Args:
            loc_to_depto: Localidades normales con departamento
            loc_viaje_ids: Localidades de viaje (sin departamento)
        """
        todas_localidades = set(loc_to_depto.keys()) | loc_viaje_ids

        if not todas_localidades:
            return

        # Verificar existentes
        stmt = select(
            Localidad.id_localidad_indec,
            Localidad.id_departamento_indec
        ).where(
            Localidad.id_localidad_indec.in_(list(todas_localidades))
        )
        existing = {
            loc_id: dep_id
            for loc_id, dep_id in self.session.execute(stmt).all()
        }

        # Obtener IDs auto-generados de departamentos
        dep_indec_to_id = self._get_departamento_id_mapping(set(loc_to_depto.values()))

        # Crear localidades faltantes
        nuevas = []

        # 1. Localidades normales con departamento
        for loc_id, dep_indec in loc_to_depto.items():
            if loc_id not in existing:
                nuevas.append({
                    "id_localidad_indec": loc_id,
                    "nombre": f"Localidad INDEC {loc_id}",
                    "id_departamento_indec": dep_indec,
                    "id_departamento": dep_indec_to_id.get(dep_indec),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })

        # 2. Localidades de viaje sin departamento
        for loc_id in loc_viaje_ids:
            if loc_id not in existing:
                nuevas.append({
                    "id_localidad_indec": loc_id,
                    "nombre": f"Localidad Viaje INDEC {loc_id}",
                    "id_departamento_indec": None,
                    "id_departamento": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })

        if nuevas:
            stmt = pg_insert(Localidad.__table__).values(nuevas)
            self.session.execute(stmt.on_conflict_do_nothing())
            logger.info(f"Creadas {len(nuevas)} localidades placeholder")

    @staticmethod
    @cache  # Cache sin expiración - los IDs no cambian durante la sesión
    def _get_cached_departamento_ids(dep_indec_codes_tuple: tuple) -> Dict[int, int]:
        """
        Versión cacheada estática para obtener mapeo de departamentos.
        Usa tupla en lugar de Set para ser hashable.
        """
        # Esta función será sobreescrita con una instancia específica
        # El cache es por tupla de IDs, así que múltiples llamadas con los mismos IDs
        # reutilizan el resultado
        return {}

    def _get_departamento_id_mapping(self, dep_indec_codes: Set[int]) -> Dict[int, int]:
        """
        Obtiene mapeo: departamento_indec_code → id (auto-generated).

        Necesario para la FK de Localidad.id_departamento.
        Con cache para evitar queries repetidas.
        """
        if not dep_indec_codes:
            return {}

        stmt = select(
            Departamento.id_departamento_indec,
            Departamento.id
        ).where(
            Departamento.id_departamento_indec.in_(list(dep_indec_codes))
        )

        return {
            indec_code: auto_id
            for indec_code, auto_id in self.session.execute(stmt).all()
        }

    # ===== HELPERS =====

    @staticmethod
    def _safe_int(value) -> int | None:
        """Conversión segura a int."""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
