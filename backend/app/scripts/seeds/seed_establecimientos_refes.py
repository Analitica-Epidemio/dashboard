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

MAPPING SNVS → IGN:
-------------------
Después de cargar los establecimientos IGN, se carga el mapping de códigos SNVS
desde establecimientos_mapping_final.json para relacionar establecimientos del
Sistema Nacional de Vigilancia con los del IGN.

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

import json
import sys
import warnings
from pathlib import Path

import pandas as pd
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

    print("📥 Descargando establecimientos de salud (IGN WFS)...")
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


def asignar_localidad_por_coordenadas(conn: Connection, lat: float, lng: float) -> int | None:
    """
    Asigna localidad INDEC usando reverse geocoding mejorado.

    Estrategia v2 (mejorada):
    1. Buscar departamento más cercano al punto (lat, lng)
    2. Dentro de ese departamento, buscar la localidad MÁS CERCANA al punto
    3. Si no hay localidades con coordenadas, usar la primera del departamento

    Mejoras respecto a v1:
    - Busca localidad más cercana (antes solo tomaba la primera)
    - Considera localidades con coordenadas válidas
    - Fallback a primera localidad si ninguna tiene coords

    Args:
        conn: Conexión SQLAlchemy
        lat: Latitud del punto
        lng: Longitud del punto

    Returns:
        id_localidad_indec o None si no se encuentra
    """
    # Paso 1: Encontrar departamento más cercano
    # Buffer de 0.5 grados (~55km) para limitar búsqueda
    dept_result = conn.execute(text("""
        SELECT id_departamento_indec
        FROM departamento
        WHERE latitud BETWEEN :lat - 0.5 AND :lat + 0.5
          AND longitud BETWEEN :lng - 0.5 AND :lng + 0.5
        ORDER BY
            (latitud - :lat) * (latitud - :lat) +
            (longitud - :lng) * (longitud - :lng)
        LIMIT 1
    """), {"lat": lat, "lng": lng})

    dept_row = dept_result.first()
    if not dept_row:
        return None

    id_departamento = dept_row[0]

    # Paso 2: Dentro de ese departamento, buscar localidad más cercana
    # Priorizar localidades con coordenadas válidas
    loc_result = conn.execute(text("""
        SELECT
            id_localidad_indec,
            latitud,
            longitud,
            (latitud - :lat) * (latitud - :lat) +
            (longitud - :lng) * (longitud - :lng) as distancia
        FROM localidad
        WHERE id_departamento_indec = :dept_id
          AND latitud IS NOT NULL
          AND longitud IS NOT NULL
        ORDER BY distancia
        LIMIT 1
    """), {"lat": lat, "lng": lng, "dept_id": id_departamento})

    loc_row = loc_result.first()

    # Si encontramos localidad con coordenadas, usarla
    if loc_row:
        return loc_row[0]

    # Fallback: Si ninguna localidad tiene coordenadas, usar la primera del departamento
    fallback_result = conn.execute(text("""
        SELECT id_localidad_indec
        FROM localidad
        WHERE id_departamento_indec = :dept_id
        LIMIT 1
    """), {"dept_id": id_departamento})

    fallback_row = fallback_result.first()
    return fallback_row[0] if fallback_row else None


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

    print("\n🗺️  Asignando localidades con reverse geocoding...")
    localidades_asignadas = 0

    for idx, row in df_renamed.iterrows():
        if idx % 1000 == 0 and idx > 0:
            print(f"   Procesados: {idx}/{len(df_renamed)} ({localidades_asignadas} con localidad)")

        # Datos básicos de IGN
        codigo_refes = limpiar_string(row.get('codigo_refes'))
        nombre = limpiar_string(row.get('nombre'))

        if not nombre:
            continue  # Skip si no hay nombre

        # Coordenadas (ya extraídas de la geometría)
        latitud = limpiar_coordenada(row.get('latitud'))
        longitud = limpiar_coordenada(row.get('longitud'))

        # Asignar localidad por reverse geocoding
        id_localidad = None
        if latitud and longitud:
            try:
                id_localidad = asignar_localidad_por_coordenadas(conn, latitud, longitud)
                if id_localidad:
                    localidades_asignadas += 1
            except Exception:
                # Si falla el reverse geocoding, seguir sin localidad
                pass

        # IGN provee: código, nombre, coordenadas + reverse geocoding de localidad
        establecimientos.append({
            'codigo_refes': str(codigo_refes) if codigo_refes else None,
            'nombre': nombre,
            'latitud': latitud,
            'longitud': longitud,
            'id_localidad_indec': id_localidad,
            'source': 'IGN',
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

        # Construir valores para INSERT (incluye localidad y source)
        values_list = []
        for est in batch:
            values = f"""(
                {f"'{est['codigo_refes']}'" if est['codigo_refes'] else 'NULL'},
                {f"'{est['nombre']}'" if est['nombre'] else 'NULL'},
                {est['latitud'] if est['latitud'] is not None else 'NULL'},
                {est['longitud'] if est['longitud'] is not None else 'NULL'},
                {est['id_localidad_indec'] if est.get('id_localidad_indec') else 'NULL'},
                {f"'{est['source']}'" if est.get('source') else 'NULL'},
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )"""
            values_list.append(values)

        stmt = text(f"""
            INSERT INTO establecimiento (
                codigo_refes, nombre,
                latitud, longitud, id_localidad_indec, source,
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
    print(f"🗺️  Con localidad asignada: {localidades_asignadas:,} ({localidades_asignadas/inserted_count*100:.1f}%)")
    print("="*70)

    # Cargar mapping SNVS → IGN
    cargar_mapping_snvs(conn)

    return inserted_count


def cargar_mapping_snvs(conn: Connection) -> int:
    """
    Carga el mapping de códigos SNVS a establecimientos IGN.

    Lee el archivo establecimientos_mapping_final.json y actualiza
    el campo codigo_snvs de los establecimientos IGN que tienen match
    con establecimientos del SNVS.

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Número de establecimientos actualizados con código SNVS
    """
    print("\n" + "="*70)
    print("🔗 CARGANDO MAPPING SNVS → IGN")
    print("="*70)

    # Cargar archivo de mapping
    mapping_path = Path(__file__).parent / "data" / "establecimientos_mapping_final.json"

    if not mapping_path.exists():
        print(f"⚠️  Archivo de mapping no encontrado: {mapping_path}")
        return 0

    with open(mapping_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapping = data.get('mapping', {})

    if not mapping:
        print("⚠️  No se encontró mapping en el archivo")
        return 0

    print(f"📋 Mappings encontrados: {len(mapping):,}")

    # Actualizar establecimientos con código SNVS
    updated_count = 0
    batch_size = 100

    mapping_items = list(mapping.items())
    total_batches = (len(mapping_items) + batch_size - 1) // batch_size

    for i in range(0, len(mapping_items), batch_size):
        batch = mapping_items[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        print(f"📦 Actualizando batch {batch_num}/{total_batches} ({len(batch)} mappings)...", end=" ")

        # Construir CASE para UPDATE masivo
        case_parts = []
        codigo_refes_list = []

        for codigo_snvs, ign_data in batch:
            codigo_refes = ign_data.get('codigo_refes')

            if not codigo_refes or not codigo_snvs:
                continue

            # Guardar el código SNVS del CSV en el establecimiento IGN
            case_parts.append(f"WHEN codigo_refes = '{codigo_refes}' THEN '{codigo_snvs}'")
            codigo_refes_list.append(f"'{codigo_refes}'")

        if not case_parts:
            print("⏭️  (sin mappings válidos)")
            continue

        # UPDATE usando CASE para actualizar múltiples registros
        stmt = text(f"""
            UPDATE establecimiento
            SET codigo_snvs = CASE
                {' '.join(case_parts)}
            END,
            updated_at = CURRENT_TIMESTAMP
            WHERE codigo_refes IN ({','.join(codigo_refes_list)})
        """)

        try:
            result = conn.execute(stmt)
            conn.commit()
            updated_count += result.rowcount
            print(f"✅ ({result.rowcount} actualizados)")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    print("\n" + "="*70)
    print(f"✅ MAPPING SNVS CARGADO: {updated_count:,} establecimientos actualizados")
    print("="*70)

    return updated_count


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
