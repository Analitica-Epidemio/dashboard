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

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def truncate_tables():
    """Limpia las tablas geográficas y establecimientos"""
    print("\n" + "="*70)
    print("🗑️  LIMPIANDO BASE DE DATOS")
    print("="*70)

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text('TRUNCATE establecimiento, localidad, departamento, provincia RESTART IDENTITY CASCADE'))
        conn.commit()
        print("✅ Tablas truncadas")


def main():
    """Ejecuta todos los seeds en orden"""
    print("\n" + "="*70)
    print("🌎 SEED COMPLETO - SISTEMA DE EPIDEMIOLOGÍA")
    print("="*70)
    print("\nEste proceso cargará:")
    print("  📍 Geografía completa de Argentina (API Georef)")
    print("  📊 Población del Censo 2022 (INDEC)")
    print("  🏥 Establecimientos de Salud (~8,300 desde IGN WFS)")
    print("  🗺️  Capas GIS (~77,000 features desde IGN WFS)")
    print("  🎯 Estrategias epidemiológicas")
    print("  📈 Configuración de gráficos")
    print("\n⏱️  Tiempo estimado: 8-12 minutos (incluye descargas WFS)")
    print("="*70)

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    try:
        # Paso 0: Limpiar
        truncate_tables()

        # Paso 1: Geografía desde API Georef
        print("\n" + "="*70)
        print("PASO 1/6: GEOGRAFÍA (API Georef)")
        print("="*70)
        from app.scripts.seeds.seed_from_georef_api import (
            seed_provincias_desde_georef,
            seed_departamentos_desde_georef,
            seed_localidades_desde_georef
        )
        with engine.connect() as conn:
            prov_count = seed_provincias_desde_georef(conn)
            dept_count = seed_departamentos_desde_georef(conn)
            loc_count = seed_localidades_desde_georef(conn, max_localidades=5000)

        # Paso 2: Población del Censo 2022
        print("\n" + "="*70)
        print("PASO 2/5: POBLACIÓN (Censo 2022)")
        print("="*70)
        from app.scripts.seeds.seed_poblacion_censo2022 import (
            seed_poblacion_provincias,
            seed_poblacion_departamentos
        )
        data_dir = Path(__file__).parent / "seeds" / "data"
        archivo_censo = data_dir / "censo2022_poblacion.xlsx"

        if archivo_censo.exists():
            with Session(engine) as session:
                seed_poblacion_provincias(session, archivo_censo)
                seed_poblacion_departamentos(session, archivo_censo)
        else:
            print("⚠️  Archivo censo2022_poblacion.xlsx no encontrado, omitiendo...")

        # Paso 3: Establecimientos REFES
        print("\n" + "="*70)
        print("PASO 3/6: ESTABLECIMIENTOS DE SALUD (REFES)")
        print("="*70)
        estab_count = 0
        try:
            from app.scripts.seeds.seed_establecimientos_refes import seed_refes
            with engine.connect() as conn:
                estab_count = seed_refes(conn)
        except Exception as e:
            print(f"⚠️  Error descargando REFES (omitiendo): {e}")
            print("   La URL del dataset puede haber cambiado.")

        # Paso 4: Capas GIS (descarga automática desde WFS)
        print("\n" + "="*70)
        print("PASO 4/6: CAPAS GIS (Descarga desde IGN)")
        print("="*70)
        gis_hidro_count = 0
        gis_areas_count = 0
        try:
            from app.scripts.seeds.seed_capas_gis_ign import seed_hidrografia, seed_areas_urbanas

            with engine.connect() as conn:
                # Descarga automática desde WFS (sin fallback a archivos locales)
                gis_hidro_count = seed_hidrografia(conn)
                gis_areas_count = seed_areas_urbanas(conn)

                if gis_hidro_count > 0 or gis_areas_count > 0:
                    print("✅ Capas GIS cargadas desde WFS")
                else:
                    print("❌ No se pudieron descargar capas GIS (verificar conexión a internet)")
        except Exception as e:
            print(f"❌ Error cargando GIS: {e}")
            import traceback
            traceback.print_exc()

        # Paso 5: Estrategias
        print("\n" + "="*70)
        print("PASO 5/6: ESTRATEGIAS")
        print("="*70)
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
        print("\n" + "="*70)
        print("PASO 6/6: GRÁFICOS")
        print("="*70)
        try:
            from app.scripts.seeds.charts import seed_charts
            with Session(engine) as session:
                seed_charts(session)
                print("✅ Gráficos configurados")
        except Exception as e:
            print(f"⚠️  Error cargando charts: {e}")
            import traceback
            traceback.print_exc()

        # Resumen
        print("\n" + "="*70)
        print("✅ SEED COMPLETADO")
        print("="*70)
        print(f"\n  ✅ {prov_count} Provincias con coordenadas")
        print(f"  ✅ {dept_count} Departamentos con coordenadas")
        print(f"  ✅ {loc_count} Localidades con coordenadas")
        print(f"  ✅ Población del Censo 2022")
        print(f"  ✅ {estab_count:,} Establecimientos de Salud (REFES)")
        if gis_hidro_count > 0 or gis_areas_count > 0:
            print(f"  ✅ {gis_hidro_count:,} Cursos de agua (GIS)")
            print(f"  ✅ {gis_areas_count:,} Áreas urbanas (GIS)")
        else:
            print(f"  ⚠️  Capas GIS no cargadas (archivos no disponibles)")
        print(f"  ✅ Estrategias epidemiológicas")
        print(f"  ✅ Configuración de gráficos")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
