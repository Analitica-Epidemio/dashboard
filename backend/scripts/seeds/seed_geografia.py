"""
Seeds para datos geográficos del sistema epidemiológico.

Carga localidades y sus departamentos asociados desde archivos Excel del INDEC.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlmodel import select as sqlmodel_select

from app.core.constants.chubut_epidemiologia import (
    MAPEO_LOCALIDAD_A_DEPARTAMENTO_CHUBUT,
    POBLACIONES_DEPARTAMENTOS_CHUBUT_2022,
    POBLACIONES_LOCALIDADES_CHUBUT_2010,
)
from app.domains.localidades.models import Departamento, Localidad, Provincia


class SeedGeografia:
    """Servicio para cargar datos geográficos desde archivos INDEC."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.data_path = Path(__file__).parent.parent.parent / "data"

    async def cargar_provincias(self) -> int:
        """
        Carga las provincias argentinas.

        Returns:
            Número de provincias cargadas
        """
        print("🏛️ Cargando provincias argentinas...")

        # Verificar si ya existen
        stmt: Select = sqlmodel_select(Provincia)
        result = await self.session.execute(stmt)
        if result.first():
            print("   ✅ Provincias ya existen, saltando...")
            return 0

        # Por ahora solo Chubut, pero fácil agregar más
        provincia_chubut = Provincia(
            id_provincia_indec=26,
            nombre="CHUBUT",
            poblacion=POBLACIONES_DEPARTAMENTOS_CHUBUT_2022["TOTAL"]
            if "TOTAL" in POBLACIONES_DEPARTAMENTOS_CHUBUT_2022
            else 592621,
        )
        self.session.add(provincia_chubut)

        await self.session.commit()
        print("   ✅ Provincia Chubut cargada")
        return 1

    async def cargar_departamentos(self) -> int:
        """
        Carga los departamentos de Chubut.

        Returns:
            Número de departamentos cargados
        """
        print("🏞️ Cargando departamentos de Chubut...")

        # Verificar si ya existen
        stmt: Select = sqlmodel_select(Departamento)
        result = await self.session.execute(stmt)
        if result.first():
            print("   ✅ Departamentos ya existen, saltando...")
            return 0

        contador = 0

        # Códigos INDEC reales de departamentos de Chubut
        CODIGOS_DEPARTAMENTOS_CHUBUT = {
            "BIEDMA": 26007,
            "CUSHAMEN": 26014,
            "ESCALANTE": 26021,
            "FLORENTINO AMEGHINO": 26028,
            "FUTALEUFU": 26035,
            "GAIMAN": 26042,
            "GASTRE": 26049,
            "LANGUIÑEO": 26056,
            "MÁRTIRES": 26063,
            "PASO DE INDIOS": 26070,
            "RAWSON": 26077,
            "RÍO SENGUER": 26084,
            "SARMIENTO": 26091,
            "TEHUELCHES": 26098,
            "TELSEN": 26105,
        }

        for nombre_depto, poblacion in POBLACIONES_DEPARTAMENTOS_CHUBUT_2022.items():
            if nombre_depto != "TOTAL":
                codigo = CODIGOS_DEPARTAMENTOS_CHUBUT.get(nombre_depto)
                if codigo:
                    departamento = Departamento(
                        id_departamento_indec=codigo,
                        nombre=nombre_depto,
                        id_provincia_indec=26,  # Chubut
                        poblacion=poblacion,
                        region_sanitaria=self._determinar_region_sanitaria_departamento(
                            nombre_depto
                        ),
                    )
                    self.session.add(departamento)
                    contador += 1

        await self.session.commit()
        print(f"   ✅ Cargados {contador} departamentos")
        return contador

    async def cargar_localidades_desde_excel(self) -> int:
        """
        Carga localidades desde archivos Excel del INDEC.

        Returns:
            Número de localidades cargadas
        """
        print("🏘️ Cargando localidades desde archivos Excel...")

        # Verificar si ya existen localidades
        stmt: Select = sqlmodel_select(Localidad)
        result = await self.session.execute(stmt)
        if result.first():
            print("   ✅ Localidades ya existen, saltando...")
            return 0

        # Primero asegurarse de que existan departamentos
        dept_result = await self.session.execute(sqlmodel_select(Departamento))
        if not dept_result.first():
            print(
                "   ⚠️  No hay departamentos cargados, ejecute primero cargar_departamentos()"
            )
            return 0

        contador = 0

        # Cargar archivo de localidades de Chubut
        archivo_chubut = self.data_path / "localidades" / "localidades_chubut.xlsx"
        if archivo_chubut.exists():
            df = pd.read_excel(archivo_chubut)

            for _, row in df.iterrows():
                # Obtener código de departamento desde el mapeo
                nombre_localidad = row["localidad"].upper()
                nombre_depto = MAPEO_LOCALIDAD_A_DEPARTAMENTO_CHUBUT.get(
                    nombre_localidad
                )

                if nombre_depto:
                    # Buscar el código INDEC del departamento
                    id_depto = self._get_codigo_departamento(nombre_depto)
                    if id_depto:
                        localidad = Localidad(
                            id_localidad_indec=int(row["id_loc_indec"]),
                            nombre=row["localidad"],
                            id_departamento_indec=id_depto,
                            poblacion=POBLACIONES_LOCALIDADES_CHUBUT_2010.get(
                                nombre_localidad
                            ),
                        )
                        self.session.add(localidad)
                        contador += 1
                self.session.add(localidad)
                contador += 1

        # Cargar archivos de otras provincias si existen
        for archivo in self.data_path.glob("localidades/*.xlsx"):
            if archivo.name != "localidades_chubut.xlsx":
                # Procesar otros archivos de localidades
                pass

        await self.session.commit()
        print(f"   ✅ Cargadas {contador} localidades")
        return contador

    def _get_codigo_departamento(self, nombre_depto: str) -> Optional[int]:
        """
        Obtiene el código INDEC de un departamento.

        Args:
            nombre_depto: Nombre del departamento

        Returns:
            Código INDEC o None
        """
        CODIGOS = {
            "BIEDMA": 26007,
            "CUSHAMEN": 26014,
            "ESCALANTE": 26021,
            "FLORENTINO AMEGHINO": 26028,
            "FUTALEUFU": 26035,
            "GAIMAN": 26042,
            "GASTRE": 26049,
            "LANGUIÑEO": 26056,
            "MÁRTIRES": 26063,
            "PASO DE INDIOS": 26070,
            "RAWSON": 26077,
            "RÍO SENGUER": 26084,
            "SARMIENTO": 26091,
            "TEHUELCHES": 26098,
            "TELSEN": 26105,
        }
        return CODIGOS.get(nombre_depto.upper())

    def _determinar_region_sanitaria_departamento(
        self, nombre_departamento: str
    ) -> Optional[str]:
        """
        Determina la región sanitaria basándose en el mapeo de localidades.

        Args:
            nombre_localidad: Nombre de la localidad

        Returns:
            Región sanitaria o None
        """
        # Por ahora usar el mapeo existente
        # En el futuro esto debería venir del archivo Excel
        from app.core.constants.chubut_epidemiologia.areas_programaticas_salud import (
            MAPEO_AREAS_A_DEPARTAMENTOS_CHUBUT,
        )

        for area, deptos in MAPEO_AREAS_A_DEPARTAMENTOS_CHUBUT.items():
            if nombre_departamento.upper() in deptos:
                return area
        return None

    async def cargar_desde_constantes(self) -> int:
        """
        Carga localidades desde las constantes del sistema (fallback).

        Returns:
            Número de localidades cargadas
        """
        print("📍 Cargando localidades desde constantes del sistema...")

        contador = 0

        # Crear localidades desde el mapeo
        for (
            localidad_nombre,
            departamento,
        ) in MAPEO_LOCALIDAD_A_DEPARTAMENTO_CHUBUT.items():
            # Generar ID ficticio basado en el nombre (en producción vendría del INDEC)
            id_loc_indec = 26000000 + contador

            # Obtener código del departamento
            id_depto = self._get_codigo_departamento(departamento)
            if id_depto:
                localidad = Localidad(
                    id_localidad_indec=id_loc_indec,
                    nombre=localidad_nombre,
                    id_departamento_indec=id_depto,
                    poblacion=POBLACIONES_LOCALIDADES_CHUBUT_2010.get(localidad_nombre),
                )
            self.session.add(localidad)
            contador += 1

        await self.session.commit()
        print(f"   ✅ Cargadas {contador} localidades desde constantes")
        return contador


async def seed_geografia(session: AsyncSession) -> None:
    """
    Ejecuta el seed de datos geográficos.

    Args:
        session: Sesión de base de datos
    """
    seeder = SeedGeografia(session)

    # 1. Cargar provincias
    await seeder.cargar_provincias()

    # 2. Cargar departamentos
    await seeder.cargar_departamentos()

    # 3. Cargar localidades
    localidades = await seeder.cargar_localidades_desde_excel()

    # Si no hay archivos Excel, cargar desde constantes
    if localidades == 0:
        await seeder.cargar_desde_constantes()
