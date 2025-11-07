#!/usr/bin/env python3
"""
🗺️ SEED - Capas GIS del Instituto Geográfico Nacional (IGN)

Descarga y carga capas geográficas automáticamente desde el servicio WFS del IGN
para análisis epidemiológico.

FUENTE DE DATOS:
----------------
Nombre: Instituto Geográfico Nacional - Capas SIG
Portal WFS: https://wms.ign.gob.ar/geoserver/ign/ows
Portal Web: https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG
Sistema de coordenadas: WGS 84 (EPSG:4326)

CAPAS DESCARGADAS AUTOMÁTICAMENTE:
-----------------------------------
1. **Hidrografía Perenne**: Cursos de agua permanentes (ríos, arroyos)
   - TypeName WFS: ign:lineas_de_aguas_continentales_perenne
   - Útil para: Análisis de enfermedades transmitidas por vectores (dengue, zika)
   - Tipo: LineString

2. **Hidrografía Intermitente**: Cursos de agua temporales
   - TypeName WFS: ign:lineas_de_aguas_continentales_intermitentes
   - Útil para: Análisis de vectores en zonas con agua estacional
   - Tipo: LineString

3. **Áreas Urbanas**: Plantas urbanas de localidades
   - TypeName WFS: ign:areas_de_asentamientos_y_edificios_020105
   - Útil para: Análisis de densidad poblacional y distribución de eventos
   - Tipo: Polygon

DESCARGA AUTOMÁTICA:
--------------------
Este script SIEMPRE descarga las capas directamente desde el servicio WFS del IGN.
NO usa archivos locales. Requiere conexión a internet estable.

REQUISITOS:
-----------
- PostGIS habilitado en PostgreSQL
- Tablas capa_hidrografia y capa_area_urbana creadas (migración aplicada)
- Conexión a internet para descargar desde WFS
- Dependencias: geopandas, shapely, geoalchemy2, requests

USO:
----
  python app/scripts/seeds/seed_capas_gis_ign.py

TIEMPO ESTIMADO: 3-5 minutos (dependiendo de la velocidad de descarga)
"""

import sys
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import LineString, Polygon
from sqlalchemy import Connection, text

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))


# URLs WFS del IGN para descarga directa
WFS_URLS = {
    'hidrografia_perenne': 'https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ign:lineas_de_aguas_continentales_perenne&outputFormat=application/json',
    'hidrografia_intermitente': 'https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ign:lineas_de_aguas_continentales_intermitentes&outputFormat=application/json',
    'areas_urbanas': 'https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ign:areas_de_asentamientos_y_edificios_020105&outputFormat=application/json',
}


def descargar_desde_wfs_chunked(capa_key: str, chunk_size: int = 5000, timeout: int = 300):
    """
    Descarga una capa GIS desde el servicio WFS del IGN con caché local,
    procesándola en chunks para evitar problemas de memoria.

    Args:
        capa_key: Clave de la capa en WFS_URLS
        chunk_size: Tamaño de chunk para procesar
        timeout: Timeout en segundos para la descarga

    Yields:
        GeoDataFrame con chunks de datos
    """
    from app.scripts.seeds.cache_helper import download_with_cache
    import json
    from io import StringIO

    if capa_key not in WFS_URLS:
        print(f"❌ Capa desconocida: {capa_key}")
        return

    url = WFS_URLS[capa_key]
    print(f"📥 Descargando capa GIS: {capa_key}...")
    print(f"   URL: {url[:80]}...")

    try:
        # Descargar con caché (7 días de validez)
        geojson_content = download_with_cache(
            url=url,
            cache_key=f"gis_ign_{capa_key}",
            max_age_days=7,
            timeout=timeout,
            verify_ssl=True
        )

        # Parsear GeoJSON
        geojson_data = json.loads(geojson_content)
        features = geojson_data.get('features', [])
        total_features = len(features)

        print(f"✅ Descargados {total_features:,} features de {capa_key}")

        # Procesar en chunks
        for i in range(0, total_features, chunk_size):
            chunk_features = features[i:i + chunk_size]

            # Crear un GeoJSON temporal para este chunk
            chunk_geojson = {
                'type': 'FeatureCollection',
                'features': chunk_features
            }

            # Convertir a GeoDataFrame
            chunk_json_str = json.dumps(chunk_geojson)
            gdf = gpd.read_file(StringIO(chunk_json_str))

            # Asegurar que esté en EPSG:4326
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            yield gdf

    except Exception as e:
        print(f"❌ Error procesando {capa_key}: {e}")
        import traceback
        traceback.print_exc()


def seed_hidrografia(conn: Connection) -> int:
    """
    Carga cursos de agua descargándolos desde el servicio WFS del IGN.

    IMPORTANTE: Siempre descarga desde WFS, nunca usa archivos locales.

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Número de cursos de agua insertados
    """
    print("\n" + "="*70)
    print("💧 CARGANDO HIDROGRAFÍA (Cursos de Agua)")
    print("="*70)

    total_inserted = 0

    # Capas de hidrografía desde WFS
    capas_hidro = [
        ('hidrografia_perenne', 'Río/Arroyo Perenne'),
        ('hidrografia_intermitente', 'Curso Intermitente')
    ]

    for capa_key, tipo_curso in capas_hidro:
        print(f"\n📍 Procesando: {tipo_curso}")

        # Descargar y procesar en chunks desde WFS
        inserted = 0
        batch_size = 2000  # 🚀 4x más grande = menos round-trips a DB
        chunk_num = 0

        for gdf_chunk in descargar_desde_wfs_chunked(capa_key, chunk_size=5000):
            chunk_num += 1
            print(f"\n   📦 Chunk {chunk_num} ({len(gdf_chunk):,} features)...")

            # Procesar el chunk en batches más pequeños para inserción
            for i in range(0, len(gdf_chunk), batch_size):
                batch = gdf_chunk.iloc[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(gdf_chunk) + batch_size - 1) // batch_size

                # 🚀 Print solo cada 5 batches (reduce I/O overhead)
                if batch_num % 5 == 1 or batch_num == total_batches:
                    print(f"      → Batch {batch_num}/{total_batches}...", end=" ", flush=True)

                values_list = []
                for idx, row in batch.iterrows():
                    # Extraer nombre si existe
                    nombre = None
                    if 'nombre' in row:
                        nombre = str(row['nombre'])[:200] if row['nombre'] else None
                    elif 'nam' in row:
                        nombre = str(row['nam'])[:200] if row['nam'] else None

                    # Escapar comillas simples en el nombre (SQL injection prevention)
                    if nombre:
                        nombre = nombre.replace("'", "''")

                    # Convertir geometría a WKT
                    geom_wkt = row.geometry.wkt if row.geometry else None

                    if geom_wkt:
                        # Escapar comillas simples en la geometría también
                        geom_wkt = geom_wkt.replace("'", "''")

                        values_list.append(f"""(
                            {f"'{nombre}'" if nombre else 'NULL'},
                            '{tipo_curso}',
                            ST_GeomFromText('{geom_wkt}', 4326),
                            'IGN',
                            CURRENT_TIMESTAMP,
                            CURRENT_TIMESTAMP
                        )""")

                if values_list:
                    stmt = text(f"""
                        INSERT INTO capa_hidrografia (
                            nombre, tipo, geometria, fuente, created_at, updated_at
                        ) VALUES {','.join(values_list)}
                    """)

                    try:
                        conn.execute(stmt)
                        # 🚀 NO commit aquí - solo al final
                        inserted += len(values_list)
                        if batch_num % 5 == 1 or batch_num == total_batches:
                            print("✅")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        conn.rollback()
                        continue

        # 🚀 Commit UNA VEZ al final de cada capa
        conn.commit()
        print(f"\n✅ Insertados {inserted:,} {tipo_curso}")
        total_inserted += inserted

    print("\n" + "="*70)
    print(f"✅ HIDROGRAFÍA CARGADA: {total_inserted:,} cursos de agua")
    print("="*70)

    return total_inserted


def seed_areas_urbanas(conn: Connection) -> int:
    """
    Carga áreas urbanas descargándolas desde el servicio WFS del IGN.

    IMPORTANTE: Siempre descarga desde WFS, nunca usa archivos locales.

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Número de áreas urbanas insertadas
    """
    print("\n" + "="*70)
    print("🏙️  CARGANDO ÁREAS URBANAS")
    print("="*70)

    # Descargar y procesar en chunks desde WFS
    inserted = 0
    batch_size = 2000  # 🚀 4x más grande
    chunk_num = 0

    for gdf_chunk in descargar_desde_wfs_chunked('areas_urbanas', chunk_size=5000):
        chunk_num += 1
        print(f"\n   📦 Chunk {chunk_num} ({len(gdf_chunk):,} features)...")

        # Procesar el chunk en batches más pequeños para inserción
        for i in range(0, len(gdf_chunk), batch_size):
            batch = gdf_chunk.iloc[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(gdf_chunk) + batch_size - 1) // batch_size

            # 🚀 Print solo cada 5 batches
            if batch_num % 5 == 1 or batch_num == total_batches:
                print(f"      → Batch {batch_num}/{total_batches}...", end=" ", flush=True)

            values_list = []
            for idx, row in batch.iterrows():
                # Extraer nombre y población si existen
                nombre = None
                poblacion = None

                if 'nombre' in row:
                    nombre = str(row['nombre'])[:200] if row['nombre'] else None
                elif 'nam' in row:
                    nombre = str(row['nam'])[:200] if row['nam'] else None

                # Escapar comillas simples en el nombre (SQL injection prevention)
                if nombre:
                    nombre = nombre.replace("'", "''")

                if 'poblacion' in row:
                    try:
                        poblacion = int(row['poblacion'])
                    except (ValueError, TypeError):
                        poblacion = None

                # Convertir geometría a WKT
                geom_wkt = row.geometry.wkt if row.geometry else None

                if geom_wkt:
                    # Escapar comillas simples en la geometría también
                    geom_wkt = geom_wkt.replace("'", "''")

                    values_list.append(f"""(
                        {f"'{nombre}'" if nombre else 'NULL'},
                        NULL,
                        NULL,
                        {poblacion if poblacion else 'NULL'},
                        ST_GeomFromText('{geom_wkt}', 4326),
                        'IGN',
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )""")

            if values_list:
                stmt = text(f"""
                    INSERT INTO capa_area_urbana (
                        nombre, id_departamento_indec, id_departamento, poblacion,
                        geometria, fuente, created_at, updated_at
                    ) VALUES {','.join(values_list)}
                """)

                try:
                    conn.execute(stmt)
                    # 🚀 NO commit aquí
                    inserted += len(values_list)
                    if batch_num % 5 == 1 or batch_num == total_batches:
                        print("✅")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    conn.rollback()
                    continue

    # 🚀 Commit UNA VEZ al final
    conn.commit()

    print("\n" + "="*70)
    print(f"✅ ÁREAS URBANAS CARGADAS: {inserted:,}")
    print("="*70)

    return inserted


if __name__ == "__main__":
    import os
    from sqlalchemy import create_engine

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    print("\n" + "="*70)
    print("🗺️  SEED CAPAS GIS - INSTITUTO GEOGRÁFICO NACIONAL")
    print("="*70)
    print("\nEste proceso descarga automáticamente capas GIS desde:")
    print("  🌐 https://wms.ign.gob.ar/geoserver/ign/ows")
    print("\nCapas a descargar:")
    print("  💧 Hidrografía Perenne (~52,000 features)")
    print("  💧 Hidrografía Intermitente (~20,000 features)")
    print("  🏙️  Áreas Urbanas (~5,000 features)")
    print("\n⏱️  Tiempo estimado: 3-5 minutos")
    print("⚠️  IMPORTANTE: Requiere conexión a internet estable")
    print("="*70)

    try:
        with engine.connect() as conn:
            # Verificar PostGIS
            result = conn.execute(text("SELECT PostGIS_Version()")).fetchone()
            print(f"\n✅ PostGIS detectado: {result[0]}")

            # Cargar capas desde WFS
            hidro_count = seed_hidrografia(conn)
            areas_count = seed_areas_urbanas(conn)

            # Resumen
            print("\n" + "="*70)
            print("✅ SEED GIS COMPLETADO")
            print("="*70)
            print(f"\n  ✅ {hidro_count:,} Cursos de agua")
            print(f"  ✅ {areas_count:,} Áreas urbanas")
            print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
