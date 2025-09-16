"""Bulk processor for establishments (used by multiple domains)."""

from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia

from ..core.columns import Columns
from .base import BulkProcessorBase


class EstablecimientosBulkProcessor(BulkProcessorBase):
    """Handles establishment creation and management for all event types."""

    def bulk_upsert_establecimientos(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Procesa establecimientos de CLINICA, DIAGNOSTICO, MUESTRA, EPIDEMIOLOGIA y CARGA.
        
        Returns:
            Dict mapping establishment names to their IDs
        """
        # 0. Crear localidades necesarias primero
        self._create_localidades_from_df(df)
        
        # Extraer establecimientos únicos de todos los tipos
        establecimientos_set = set()

        for _, row in df.iterrows():
            # Establecimientos de CLINICA
            nombre_estab_clinica = self._clean_string(row.get(Columns.ESTAB_CLINICA))
            id_loc_clinica = self._safe_int(row.get(Columns.ID_LOC_INDEC_CLINICA))

            if nombre_estab_clinica:
                establecimientos_set.add((nombre_estab_clinica, id_loc_clinica))

            # Establecimientos de DIAGNOSTICO
            nombre_estab_diag = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_DIAG)
            )
            id_loc_diag = self._safe_int(row.get(Columns.ID_LOC_INDEC_DIAG))

            if nombre_estab_diag:
                establecimientos_set.add((nombre_estab_diag, id_loc_diag))

            # Establecimientos de MUESTRA
            nombre_estab_muestra = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_MUESTRA)
            )
            id_loc_muestra = self._safe_int(row.get(Columns.ID_LOC_INDEC_MUESTRA))

            if nombre_estab_muestra:
                establecimientos_set.add((nombre_estab_muestra, id_loc_muestra))

            # Establecimientos de EPIDEMIOLOGIA (quien reporta)
            nombre_estab_epi = self._clean_string(row.get(Columns.ESTABLECIMIENTO_EPI))
            id_loc_epi = self._safe_int(row.get(Columns.ID_LOC_INDEC_EPI))

            if nombre_estab_epi:
                establecimientos_set.add((nombre_estab_epi, id_loc_epi))

            # Establecimientos de CARGA (donde se carga en el sistema)
            nombre_estab_carga = self._clean_string(
                row.get(Columns.ESTABLECIMIENTO_CARGA)
            )
            id_loc_carga = self._safe_int(row.get(Columns.ID_LOC_INDEC_CARGA))

            if nombre_estab_carga:
                establecimientos_set.add((nombre_estab_carga, id_loc_carga))

        if not establecimientos_set:
            return {}

        # Verificar existentes
        nombres_estab = [e[0] for e in establecimientos_set]
        stmt = select(Establecimiento.id, Establecimiento.nombre).where(
            Establecimiento.nombre.in_(nombres_estab)
        )
        existing_mapping = {
            nombre: estab_id
            for estab_id, nombre in self.context.session.execute(stmt).all()
        }

        # Crear nuevos establecimientos
        nuevos_establecimientos = []
        for nombre, id_localidad in establecimientos_set:
            if nombre not in existing_mapping:
                nuevos_establecimientos.append(
                    {
                        "nombre": nombre,
                        "id_localidad_establecimiento": id_localidad,
                        "created_at": self._get_current_timestamp(),
                        "updated_at": self._get_current_timestamp(),
                    }
                )

        if nuevos_establecimientos:
            stmt = pg_insert(Establecimiento.__table__).values(nuevos_establecimientos)
            upsert_stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(upsert_stmt)

            # Re-obtener el mapping completo
            stmt = select(Establecimiento.id, Establecimiento.nombre).where(
                Establecimiento.nombre.in_(nombres_estab)
            )
            existing_mapping = {
                nombre: estab_id
                for estab_id, nombre in self.context.session.execute(stmt).all()
            }

        return existing_mapping

    def _create_localidades_from_df(self, df: pd.DataFrame) -> None:
        """
        Crea las localidades necesarias extrayendo IDs INDEC únicos del DataFrame.
        """
        self.logger.info("Creando localidades desde DataFrame")
        
        # 1. Primero crear departamentos necesarios
        self._create_departamentos_from_df(df)
        
        # 2. Extraer IDs de localidad únicos de todas las columnas junto con departamentos
        localidad_data = {}  # {localidad_id: departamento_id}
        viaje_localidades = set()  # Solo los IDs de localidades de viaje, sin provincia
        
        for _, row in df.iterrows():
            # Mapear localidad -> departamento para cada tipo (excepto viaje)
            mappings = [
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_CLINICA)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_CLINICA))),
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_DIAG)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_DIAG))),
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_MUESTRA)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_MUESTRA))),
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_EPI)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_EPI))),
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_CARGA)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_CARGA))),
                (self._safe_int(row.get(Columns.ID_LOC_INDEC_RESIDENCIA)), self._safe_int(row.get(Columns.ID_DEPTO_INDEC_RESIDENCIA))),
            ]
            
            for loc_id, dep_id in mappings:
                if loc_id is not None and dep_id is not None:
                    localidad_data[loc_id] = dep_id
            
            # Recopilar localidades de viaje (verificaremos si ya tienen depto después)
            loc_viaje = self._safe_int(row.get(Columns.ID_LOC_INDEC_VIAJE))
            if loc_viaje is not None:
                viaje_localidades.add(loc_viaje)
        
        if not localidad_data and not viaje_localidades:
            self.logger.info("No se encontraron IDs de localidad válidos")
            return
            
        # Combinar todas las localidades para verificar existencia
        todas_localidades = set(localidad_data.keys()) | viaje_localidades
        
        # Verificar cuáles localidades ya existen y obtener sus departamentos
        stmt = select(
            Localidad.id_localidad_indec, 
            Localidad.id_departamento_indec
        ).where(
            Localidad.id_localidad_indec.in_(list(todas_localidades))
        )
        existing_localidades = {
            loc_id: dep_id 
            for loc_id, dep_id in self.context.session.execute(stmt).all()
        }
        
        # Para localidades de viaje, verificar si ya tienen departamento asociado en BD
        viaje_con_departamento = {}
        for loc_viaje in viaje_localidades:
            if loc_viaje in existing_localidades and existing_localidades[loc_viaje] is not None:
                # La localidad ya existe y tiene departamento
                viaje_con_departamento[loc_viaje] = existing_localidades[loc_viaje]
        
        # Crear localidades faltantes
        nuevas_localidades = []
        
        # Localidades regulares con departamento
        for loc_id, dep_id in localidad_data.items():
            if loc_id not in existing_localidades:
                nuevas_localidades.append({
                    "id_localidad_indec": loc_id,
                    "nombre": f"Localidad INDEC {loc_id}",  # Nombre temporal
                    "id_departamento_indec": dep_id,  # Usar departamento real del CSV
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
        
        # Localidades de viaje que no existen - crear sin departamento (NULL)
        for loc_viaje in viaje_localidades:
            if loc_viaje not in existing_localidades:
                nuevas_localidades.append({
                    "id_localidad_indec": loc_viaje,
                    "nombre": f"Localidad Viaje INDEC {loc_viaje}",  # Nombre temporal específico
                    "id_departamento_indec": None,  # NULL - sin departamento conocido
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
        
        if nuevas_localidades:
            # Bulk insert de localidades
            stmt = pg_insert(Localidad.__table__).values(nuevas_localidades)
            stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(stmt)
            
            self.logger.info(f"Creadas {len(nuevas_localidades)} localidades temporales")
        else:
            self.logger.info("Todas las localidades ya existían")

    def _create_departamentos_from_df(self, df: pd.DataFrame) -> None:
        """
        Crea los departamentos necesarios extrayendo IDs INDEC únicos del DataFrame.
        """
        self.logger.info("Creando departamentos desde DataFrame")
        
        # 1. Primero crear provincias necesarias
        self._create_provincias_from_df(df)
        
        # 2. Extraer departamento -> provincia mappings
        departamento_data = {}  # {departamento_id: provincia_id}
        
        for _, row in df.iterrows():
            mappings = [
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_CLINICA)), self._safe_int(row.get(Columns.ID_PROV_INDEC_CLINICA))),
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_DIAG)), self._safe_int(row.get(Columns.ID_PROV_INDEC_DIAG))),
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_MUESTRA)), self._safe_int(row.get(Columns.ID_PROV_INDEC_MUESTRA))),
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_EPI)), self._safe_int(row.get(Columns.ID_PROV_INDEC_EPI))),
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_CARGA)), self._safe_int(row.get(Columns.ID_PROV_INDEC_CARGA))),
                (self._safe_int(row.get(Columns.ID_DEPTO_INDEC_RESIDENCIA)), self._safe_int(row.get(Columns.ID_PROV_INDEC_RESIDENCIA))),
            ]
            
            for dep_id, prov_id in mappings:
                if dep_id is not None and prov_id is not None:
                    departamento_data[dep_id] = prov_id
        
        if not departamento_data:
            return
            
        # Verificar cuáles departamentos ya existen
        stmt = select(Departamento.id_departamento_indec).where(
            Departamento.id_departamento_indec.in_(list(departamento_data.keys()))
        )
        existing_ids = {
            id_indec for id_indec, in self.context.session.execute(stmt).all()
        }
        
        # Crear departamentos faltantes
        nuevos_departamentos = []
        for dep_id, prov_id in departamento_data.items():
            if dep_id not in existing_ids:
                nuevos_departamentos.append({
                    "id_departamento_indec": dep_id,
                    "nombre": f"Departamento INDEC {dep_id}",  # Nombre temporal
                    "id_provincia_indec": prov_id,  # Usar provincia real del CSV
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
        
        if nuevos_departamentos:
            # Bulk insert de departamentos
            stmt = pg_insert(Departamento.__table__).values(nuevos_departamentos)
            stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(stmt)
            
            self.logger.info(f"Creados {len(nuevos_departamentos)} departamentos temporales")

    def _create_provincias_from_df(self, df: pd.DataFrame) -> None:
        """
        Crea las provincias necesarias extrayendo IDs INDEC únicos del DataFrame.
        """
        self.logger.info("Creando provincias desde DataFrame")
        
        # Extraer IDs de provincia únicos
        provincia_ids = set()
        
        for _, row in df.iterrows():
            prov_ids = [
                self._safe_int(row.get(Columns.ID_PROV_INDEC_CLINICA)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_DIAG)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_MUESTRA)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_EPI)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_CARGA)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_RESIDENCIA)),
                self._safe_int(row.get(Columns.ID_PROV_INDEC_VIAJE)),
            ]
            
            for prov_id in prov_ids:
                if prov_id is not None:
                    provincia_ids.add(prov_id)
        
        if not provincia_ids:
            return
            
        # Verificar cuáles provincias ya existen
        stmt = select(Provincia.id_provincia_indec).where(
            Provincia.id_provincia_indec.in_(list(provincia_ids))
        )
        existing_ids = {
            id_indec for id_indec, in self.context.session.execute(stmt).all()
        }
        
        # Crear provincias faltantes
        nuevas_provincias = []
        for prov_id in provincia_ids:
            if prov_id not in existing_ids:
                nuevas_provincias.append({
                    "id_provincia_indec": prov_id,
                    "nombre": f"Provincia INDEC {prov_id}",  # Nombre temporal
                    "created_at": self._get_current_timestamp(),
                    "updated_at": self._get_current_timestamp(),
                })
        
        if nuevas_provincias:
            # Bulk insert de provincias
            stmt = pg_insert(Provincia.__table__).values(nuevas_provincias)
            stmt = stmt.on_conflict_do_nothing()
            self.context.session.execute(stmt)
            
            self.logger.info(f"Creadas {len(nuevas_provincias)} provincias temporales")