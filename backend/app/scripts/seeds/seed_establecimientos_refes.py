#!/usr/bin/env python3
"""
🏥 SEED - Establecimientos de Salud (IGN)

Carga establecimientos de salud desde el Instituto Geográfico Nacional (IGN).

FUENTE DE DATOS:
----------------
Nombre: Edificios de Salud - Instituto Geográfico Nacional
URL WFS: https://wms.ign.gob.ar/geoserver/ign/ows
Capa: ign:salud_020801
Formato: GeoJSON descargado automáticamente desde WFS
Cobertura: ~8,300 establecimientos de salud de Argentina
Última actualización: Datos oficiales del IGN (actualizados periódicamente)

DATOS INCLUIDOS:
----------------
- Identificación: GID (código único), nombre completo
- Tipo: Hospital, Centro de Salud, Unidad Sanitaria, etc.
- Geolocalización: latitud, longitud (WGS84) extraída de geometría Point

DATOS NO DISPONIBLES EN IGN:
---------------------------
- Domicilio, código postal
- Teléfonos, emails, sitio web
- ID de localidad INDEC
(Estos campos se dejan en NULL)

REQUISITOS:
-----------
- Tablas provincia, departamento, localidad deben existir
- Conexión a internet para descargar desde WFS del IGN
- PostGIS habilitado (para procesar geometrías)

USO:
----
  python app/scripts/seeds/seed_establecimientos_refes.py

TIEMPO ESTIMADO: 2-3 minutos (~8,300 registros + descarga WFS)
"""

import io
import sys
from pathlib import Path
import warnings

import pandas as pd
import requests
from sqlalchemy import Connection, text

# Suprimir warnings de SSL inseguro
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))


def descargar_establecimientos_wfs():
    """
    Descarga establecimientos de salud desde el servicio WFS del IGN.

    Usa la capa 'Edificio de salud' (ign:salud_020801) del Instituto Geográfico Nacional.
    Implementa caché local para acelerar re-ejecuciones.

    Returns:
        GeoDataFrame con los datos de establecimientos y geometrías
    """
    import geopandas as gpd
    from app.scripts.seeds.cache_helper import download_with_cache

    # URL WFS del IGN para establecimientos de salud
    url = "https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ign:salud_020801&outputFormat=application/json"

    print(f"📥 Descargando establecimientos de salud (IGN WFS)...")
    print(f"   URL: {url[:80]}...")

    try:
        # Descargar con caché (7 días de validez)
        geojson_content = download_with_cache(
            url=url,
            cache_key="establecimientos_ign_salud",
            max_age_days=7,
            timeout=300,
            verify_ssl=False
        )

        # Cargar GeoJSON en GeoDataFrame
        gdf = gpd.read_file(geojson_content)

        print(f"✅ Cargados: {len(gdf):,} establecimientos de salud")

        return gdf

    except Exception as e:
        print(f"❌ Error procesando datos: {e}")
        raise


def limpiar_string(val) -> str | None:
    """Limpia y normaliza strings."""
    if pd.isna(val) or val == "" or val == "S/D" or val == "s/d":
        return None
    # Escapar apóstrofes para SQL (O'Higgins -> O''Higgins)
    return str(val).strip().replace("'", "''")[:200]  # Limitar longitud


def limpiar_coordenada(val) -> float | None:
    """Limpia y valida coordenadas."""
    if pd.isna(val):
        return None
    try:
        coord = float(val)
        # Validar rango razonable para Argentina
        # Latitud: -55 a -21, Longitud: -73 a -53
        if -90 <= coord <= 90 or -180 <= coord <= 180:
            return coord
        return None
    except (ValueError, TypeError):
        return None


def seed_refes(conn: Connection) -> int:
    """
    Carga establecimientos de salud desde WFS del IGN en la tabla 'establecimiento'.

    Estrategia: INSERT directo, asume DB vacía (sin checks de conflicto).

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Número de establecimientos insertados
    """
    print("\n" + "="*70)
    print("🏥 CARGANDO ESTABLECIMIENTOS DE SALUD (IGN)")
    print("="*70)

    # 1. Descargar datos desde WFS del IGN (retorna GeoDataFrame)
    gdf = descargar_establecimientos_wfs()

    print(f"\n📋 Columnas disponibles: {list(gdf.columns)}")
    print(f"📊 Total descargado: {len(gdf):,} establecimientos")

    # 2. Extraer coordenadas de la geometría Point
    # La geometría viene del WFS, extraer lat/lon
    gdf['latitud'] = gdf.geometry.y
    gdf['longitud'] = gdf.geometry.x

    # 3. Mapeo de columnas IGN a nuestro modelo
    # Columnas IGN: id, gid, entidad, fna, gna, nam, fdc, sag
    # fna = Full Name (nombre completo del establecimiento)
    # gna = Generic Name (tipo: Hospital, Centro de Salud, etc.)
    # nam = Name (nombre corto/localidad)
    column_mapping = {
        'gid': 'codigo_refes',           # Usar GID como código único
        'fna': 'nombre',                 # Nombre completo
        'gna': 'tipo_establecimiento',   # Tipo (Hospital, Centro de Salud, etc.)
        'nam': 'nombre_corto',           # Nombre corto
    }

    # Renombrar columnas
    df_renamed = gdf.rename(columns=column_mapping)

    # 4. Limpiar y preparar datos
    establecimientos = []

    for idx, row in df_renamed.iterrows():
        # Datos básicos de IGN
        codigo_refes = limpiar_string(row.get('codigo_refes'))
        nombre = limpiar_string(row.get('nombre'))

        if not nombre:
            continue  # Skip si no hay nombre

        # Coordenadas (ya extraídas de la geometría)
        latitud = limpiar_coordenada(row.get('latitud'))
        longitud = limpiar_coordenada(row.get('longitud'))

        # IGN solo provee: código, nombre y coordenadas
        establecimientos.append({
            'codigo_refes': str(codigo_refes) if codigo_refes else None,
            'nombre': nombre,
            'latitud': latitud,
            'longitud': longitud,
        })

    if not establecimientos:
        print("⚠️  No se encontraron establecimientos válidos")
        return 0

    print(f"📊 Preparados {len(establecimientos):,} establecimientos para insertar")

    # 4. INSERT masivo con raw SQL
    inserted_count = 0
    batch_size = 500
    total_batches = (len(establecimientos) + batch_size - 1) // batch_size

    for i in range(0, len(establecimientos), batch_size):
        batch = establecimientos[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        print(f"📦 Insertando batch {batch_num}/{total_batches} ({len(batch)} establecimientos)...", end=" ")

        # Construir valores para INSERT (solo campos disponibles del IGN)
        values_list = []
        for est in batch:
            values = f"""(
                {f"'{est['codigo_refes']}'" if est['codigo_refes'] else 'NULL'},
                {f"'{est['nombre']}'" if est['nombre'] else 'NULL'},
                {est['latitud'] if est['latitud'] is not None else 'NULL'},
                {est['longitud'] if est['longitud'] is not None else 'NULL'},
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )"""
            values_list.append(values)

        stmt = text(f"""
            INSERT INTO establecimiento (
                codigo_refes, nombre,
                latitud, longitud,
                created_at, updated_at
            ) VALUES {','.join(values_list)}
        """)

        try:
            conn.execute(stmt)
            conn.commit()
            inserted_count += len(batch)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    print("\n" + "="*70)
    print(f"✅ ESTABLECIMIENTOS REFES CARGADOS: {inserted_count:,}")
    print("="*70)

    return inserted_count


if __name__ == "__main__":
    import os
    from sqlalchemy import create_engine

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            count = seed_refes(conn)
            print(f"\n✅ Total insertado: {count:,} establecimientos")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
