#!/usr/bin/env python3
"""
🌎 SEED MAESTRO - Sistema de Epidemiología

Este script carga todos los datos iniciales necesarios para la aplicación.

FUENTES DE DATOS:
-----------------
1. **Geografía**: API Georef (datos.gob.ar) - Oficial del gobierno argentino
   - 24 Provincias
   - ~530 Departamentos con coordenadas (lat/lon)
   - ~5,000 Localidades con coordenadas (lat/lon)
   - Fuente: https://apis.datos.gob.ar/georef/api/

2. **Población**: Censo Nacional 2022 (INDEC)
   - Archivo: seeds/data/censo2022_poblacion.xlsx
   - Fuente: https://www.indec.gob.ar/ftp/cuadros/poblacion/cnphv2022_resultados_provisionales.xlsx

3. **Establecimientos de Salud**: Instituto Geográfico Nacional (IGN)
   - ~8,300 establecimientos de salud de Argentina
   - Fuente: https://wms.ign.gob.ar/geoserver/ign/ows (Capa: ign:salud_020801)

4. **Capas GIS** (OPCIONAL): Instituto Geográfico Nacional
   - Hidrografía (cursos de agua)
   - Áreas urbanas
   - Requiere: Archivos GeoJSON descargados manualmente
   - Ver: seeds/data/GIS_README.md para instrucciones

5. **Estrategias**: Definiciones de estrategias epidemiológicas
   - Cargadas desde seeds/strategies.py

6. **Charts**: Configuración de gráficos del dashboard
   - Cargados desde seeds/charts.py

7. **Boletines**: Template de configuración de boletines epidemiológicos
   - Cargado desde domains/boletines/seeds.py

REQUISITOS:
-----------
- Base de datos vacía (las tablas deben existir pero estar vacías)
- Conexión a internet (para API Georef y REFES)
- Archivo censo2022_poblacion.xlsx en seeds/data/

USO:
----
  python app/scripts/seed.py

O desde Make:
  make seed

TIEMPO ESTIMADO: 5-8 minutos
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Cargar variables de entorno desde .env
load_dotenv()


def truncate_tables():
    """Limpia las tablas geográficas, establecimientos y agentes"""
    print("\n" + "=" * 70)
    print("🗑️  LIMPIANDO BASE DE DATOS")
    print("=" * 70)

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
    )
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Tablas geográficas y establecimientos
        conn.execute(
            text(
                "TRUNCATE establecimiento, localidad, departamento, provincia RESTART IDENTITY CASCADE"
            )
        )

        conn.commit()
        print("✅ Tablas truncadas (geografía, establecimientos, agentes)")


def preguntar_superadmin_dev() -> bool:
    """
    Pregunta al usuario si quiere crear el superadmin de desarrollo.
    Retorna True si el usuario confirma, False en caso contrario.
    """
    print("\n" + "=" * 70)
    print("🔐 SUPERADMIN DE DESARROLLO")
    print("=" * 70)
    print("\n⚠️  ADVERTENCIA: Esto creará un superadmin con credenciales inseguras:")
    print("   Email: admin@admin.com")
    print("   Password: admin")
    print("\n   Solo usar en desarrollo local. En producción usar: make superadmin")

    try:
        respuesta = input("\n¿Crear superadmin de desarrollo? [y/N]: ").strip().lower()
        return respuesta in ["y", "yes", "si", "sí"]
    except EOFError:
        # No hay stdin (ej: pipe), omitir
        print("  ⏭️  Omitido (no hay terminal interactiva)")
        return False


def main():
    """Ejecuta todos los seeds en orden"""
    print("\n" + "=" * 70)
    print("🌎 SEED COMPLETO - SISTEMA DE EPIDEMIOLOGÍA")
    print("=" * 70)
    print("\nEste proceso cargará:")
    print("  📍 Geografía completa de Argentina (API Georef)")
    print("  📊 Población del Censo 2022 (INDEC)")
    print("  🏥 Establecimientos de Salud (~8,300 desde IGN WFS)")
    print("  🦠 Grupos/Tipos ENO y Agentes Etiológicos")
    print("  🎯 Estrategias epidemiológicas")
    print("  📈 Configuración de gráficos y boletines")
    print("\n⏱️  Tiempo estimado: 8-12 minutos (incluye descargas WFS)")
    print("=" * 70)

    # Preguntar al inicio si crear superadmin de desarrollo
    crear_superadmin = preguntar_superadmin_dev()

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
    )
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    try:
        # Paso 0: Limpiar
        truncate_tables()

        # Paso 1: Geografía desde API Georef
        print("\n" + "=" * 70)
        print("PASO 1/7: GEOGRAFÍA (API Georef)")
        print("=" * 70)
        from app.scripts.seeds.seed_from_georef_api import (
            seed_departamentos_desde_georef,
            seed_localidades_desde_georef,
            seed_provincias_desde_georef,
        )

        with engine.begin() as conn:
            prov_count = seed_provincias_desde_georef(conn)
            dept_count = seed_departamentos_desde_georef(conn)
            loc_count = seed_localidades_desde_georef(conn, max_localidades=5000)

        # Paso 1.5: Geometrías de provincias y departamentos
        print("\n" + "=" * 70)
        print("PASO 1.5/8: GEOMETRÍAS (GeoJSON desde Georef)")
        print("=" * 70)
        try:
            from app.scripts.seeds.seed_geometrias_georef import (
                seed_geometrias_departamentos,
                seed_geometrias_provincias,
            )

            with engine.begin() as conn:
                seed_geometrias_provincias(conn)
                seed_geometrias_departamentos(conn)
        except Exception as e:
            print(f"⚠️  Error cargando geometrías: {e}")
            import traceback

            traceback.print_exc()

        # Paso 2: Población del Censo 2022
        print("\n" + "=" * 70)
        print("PASO 2/8: POBLACIÓN (Censo 2022)")
        print("=" * 70)
        from app.scripts.seeds.seed_poblacion_censo2022 import (
            descargar_censo_si_no_existe,
            seed_poblacion_departamentos,
            seed_poblacion_provincias,
        )

        data_dir = Path(__file__).parent / "seeds" / "data"
        archivo_censo = data_dir / "censo2022_poblacion.xlsx"

        # Descargar automáticamente si no existe
        if descargar_censo_si_no_existe(archivo_censo):
            with Session(engine) as session:
                seed_poblacion_provincias(session, archivo_censo)
                seed_poblacion_departamentos(session, archivo_censo)
        else:
            print("⚠️  No se pudo obtener archivo del censo, omitiendo...")

        # Paso 3: Establecimientos REFES
        print("\n" + "=" * 70)
        print("PASO 3/7: ESTABLECIMIENTOS DE SALUD (REFES)")
        print("=" * 70)
        estab_count = 0
        try:
            from app.scripts.seeds.seed_establecimientos_refes import seed_refes

            with engine.begin() as conn:
                estab_count = seed_refes(conn)
        except Exception as e:
            print(f"⚠️  Error descargando REFES (omitiendo): {e}")
            print("   La URL del dataset puede haber cambiado.")

            # Paso 4: Capas GIS (descarga automática desde WFS)
            # print("\n" + "="*70)
            # print("PASO 4/6: CAPAS GIS (Descarga desde IGN)")
            # print("="*70)
            # gis_hidro_count = 0
            # gis_areas_count = 0
            # try:
            #     from app.scripts.seeds.seed_capas_gis_ign import seed_hidrografia, seed_areas_urbanas

            #     with engine.connect() as conn:
            #         # Descarga automática desde WFS (sin fallback a archivos locales)
            #         gis_hidro_count = seed_hidrografia(conn)
            #         gis_areas_count = seed_areas_urbanas(conn)

            #         if gis_hidro_count > 0 or gis_areas_count > 0:
            #             print("✅ Capas GIS cargadas desde WFS")
            #         else:
            #             print("❌ No se pudieron descargar capas GIS (verificar conexión a internet)")
            # except Exception as e:
            print(f"❌ Error cargando GIS: {e}")
            import traceback

            traceback.print_exc()

        # Paso 4.5: Grupos ENO y Tipos ENO
        print("\n" + "=" * 70)
        print("PASO 4.5/10: GRUPOS Y TIPOS ENO")
        print("=" * 70)
        try:
            from app.scripts.seeds.seed_grupos_eno import seed_grupos_eno
            from app.scripts.seeds.seed_tipos_eno import seed_tipos_eno

            with Session(engine) as session:
                seed_grupos_eno(session)
                seed_tipos_eno(session)
                session.commit()
                print("✅ Grupos y Tipos ENO cargados")
        except Exception as e:
            print(f"⚠️  Error cargando Grupos/Tipos ENO: {e}")
            import traceback

            traceback.print_exc()

        # Paso 4.6: Agentes Etiológicos
        print("\n" + "=" * 70)
        print("PASO 4.6/10: AGENTES ETIOLÓGICOS")
        print("=" * 70)
        try:
            import asyncio

            from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

            from app.scripts.seeds.seed_agentes_etiologicos import (
                seed_agentes_etiologicos,
            )

            # Crear engine dedicado para este seed (evita problemas de event loop)
            async_db_url = DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
            temp_engine = create_async_engine(async_db_url)

            async def seed_agentes_async():
                async with AsyncSession(temp_engine) as session:
                    await seed_agentes_etiologicos(session)
                await temp_engine.dispose()

            asyncio.run(seed_agentes_async())
            print("✅ Agentes etiológicos cargados")
        except Exception as e:
            print(f"⚠️  Error cargando agentes etiológicos: {e}")
            import traceback

            traceback.print_exc()

        # Paso 4.7: Agrupaciones de Agentes (para charts agrupados)
        print("\n" + "=" * 70)
        print("PASO 4.7/10: AGRUPACIONES DE AGENTES")
        print("=" * 70)
        try:
            from app.domains.catalogos.agentes.seed_agrupaciones import (
                seed_agrupaciones,
            )

            with Session(engine) as session:
                stats = seed_agrupaciones(session)  # type: ignore[arg-type]
                print(f"✅ Agrupaciones creadas: {stats['agrupaciones_creadas']}")
                print(f"   Actualizadas: {stats['agrupaciones_actualizadas']}")
                print(f"   Agentes vinculados: {stats['agentes_vinculados']}")
                if stats["agentes_no_encontrados"]:
                    print(
                        f"   ⚠️ Agentes no encontrados: {len(stats['agentes_no_encontrados'])}"
                    )
        except Exception as e:
            print(f"⚠️  Error cargando agrupaciones: {e}")
            import traceback

            traceback.print_exc()

        # Paso 5: Estrategias
        print("\n" + "=" * 70)
        print("PASO 5/10: ESTRATEGIAS")
        print("=" * 70)
        try:
            from app.scripts.seeds.strategies import seed_all_strategies

            with Session(engine) as session:
                seed_all_strategies(session)
                print("✅ Estrategias cargadas")
        except Exception as e:
            print(f"⚠️  Error cargando estrategias: {e}")
            import traceback

            traceback.print_exc()

        # Paso 6: Charts
        print("\n" + "=" * 70)
        print("PASO 6/10: GRÁFICOS")
        print("=" * 70)
        try:
            from app.scripts.seeds.charts import seed_charts

            with Session(engine) as session:
                seed_charts(session)
                print("✅ Gráficos configurados")
        except Exception as e:
            print(f"⚠️  Error cargando charts: {e}")
            import traceback

            traceback.print_exc()

        # Paso 7: Configuración de Boletines
        print("\n" + "=" * 70)
        print("PASO 7/10: CONFIGURACIÓN DE BOLETINES")
        print("=" * 70)
        try:
            from app.domains.boletines.seeds import seed_boletin_template_config

            with Session(engine) as session:
                seed_boletin_template_config(session)
            print("✅ Configuración de boletines cargada")
        except Exception as e:
            print(f"⚠️  Error cargando configuración de boletines: {e}")
            import traceback

            traceback.print_exc()

        # Paso 8: Usuarios (solo si el usuario confirmó al inicio)
        print("\n" + "=" * 70)
        print("PASO 8/10: USUARIOS")
        print("=" * 70)
        superadmin_creado = False
        if crear_superadmin:
            try:
                from app.scripts.seeds.seed_users import seed_superadmin

                with Session(engine) as session:
                    seed_superadmin(session, force=True)
                    superadmin_creado = True
            except Exception as e:
                print(f"⚠️  Error creando usuarios: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(
                "  ⏭️  Superadmin de desarrollo omitido (usar 'make superadmin' para crear uno seguro)"
            )

        # Resumen
        print("\n" + "=" * 70)
        print("✅ SEED COMPLETADO")
        print("=" * 70)
        print(f"\n  ✅ {prov_count} Provincias con coordenadas")
        print(f"  ✅ {dept_count} Departamentos con coordenadas")
        print(f"  ✅ {loc_count} Localidades con coordenadas")
        print("  ✅ Población del Censo 2022")
        print(f"  ✅ {estab_count:,} Establecimientos de Salud (REFES)")
        print("  ✅ Grupos y Tipos ENO")
        print("  ✅ Agentes etiológicos (respiratorios, entéricos, vectoriales)")
        print("  ✅ Estrategias epidemiológicas")
        print("  ✅ Configuración de gráficos")
        print("  ✅ Configuración de boletines (template)")
        if superadmin_creado:
            print("  ✅ Usuario superadmin (admin@admin.com / admin)")
        else:
            print("  ⏭️  Superadmin omitido (usar 'make superadmin')")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
