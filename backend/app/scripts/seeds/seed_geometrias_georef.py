"""
Seed para cargar GEOMETRÍAS de provincias y departamentos desde API Georef.

Descarga los GeoJSON completos desde:
- https://infra.datos.gob.ar/georef/provincias.geojson
- https://infra.datos.gob.ar/georef/departamentos.geojson

Y actualiza las tablas provincia y departamento con las geometrías.

IMPORTANTE: Este seed solo actualiza registros existentes (no crea nuevos).
Debe ejecutarse DESPUÉS del seed principal de geografía.
"""

import json
import os
import urllib.request
from typing import Any, Dict, Optional

from shapely.geometry import shape
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

# URLs de descarga directa de GeoJSON
PROVINCIAS_GEOJSON_URL = "https://infra.datos.gob.ar/georef/provincias.geojson"
DEPARTAMENTOS_GEOJSON_URL = "https://infra.datos.gob.ar/georef/departamentos.geojson"

# Fuente para metadata
FUENTE = "Georef API (datos.gob.ar)"


def descargar_geojson(url: str, nombre: str) -> Optional[Dict[str, Any]]:
    """Descarga un GeoJSON desde una URL."""
    print(f"   Descargando {nombre} desde {url}...")
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            import typing

            return typing.cast(Dict[str, Any], data)
    except Exception as e:
        print(f"❌ Error descargando {nombre}: {e}")
        return None


def geometry_to_multipolygon_wkt(geometry: dict) -> str:
    """
    Convierte una geometría GeoJSON a WKT MultiPolygon.

    Maneja tanto Polygon como MultiPolygon.
    """
    geom = shape(geometry)

    # Si es Polygon, convertir a MultiPolygon
    if geom.geom_type == "Polygon":
        from shapely.geometry import MultiPolygon

        geom = MultiPolygon([geom])

    return str(geom.wkt)


def seed_geometrias_provincias(conn: Connection) -> int:
    """
    Descarga GeoJSON de provincias y actualiza las geometrías en la BD.

    Solo actualiza provincias que ya existen (por id_provincia_indec).
    """
    print("\n🗺️  Cargando geometrías de PROVINCIAS...")

    # Verificar si ya hay geometrías cargadas
    check_stmt = text("""
        SELECT COUNT(*) FROM provincia WHERE geometria IS NOT NULL
    """)
    result = conn.execute(check_stmt).scalar()

    if result and result > 0:
        print(f"   ✓ Ya hay {result} provincias con geometría. Saltando...")
        return 0

    # Descargar GeoJSON
    geojson = descargar_geojson(PROVINCIAS_GEOJSON_URL, "provincias")
    if not geojson:
        return 0

    features = geojson.get("features", [])
    print(f"   Descargadas: {len(features)} provincias con geometría")

    updated = 0
    errors = 0

    for feature in features:
        props = {}
        try:
            props = feature.get("properties", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # ID de provincia INDEC
            id_provincia_indec = int(props.get("id", 0))
            if not id_provincia_indec:
                continue

            # Convertir geometría a WKT MultiPolygon
            geom_wkt = geometry_to_multipolygon_wkt(geometry)

            # UPDATE usando ST_GeomFromText
            stmt = text("""
                UPDATE provincia
                SET
                    geometria = ST_GeomFromText(:geom_wkt, 4326),
                    fuente_geometria = :fuente
                WHERE id_provincia_indec = :prov_id
            """)

            result = conn.execute(
                stmt,
                {"geom_wkt": geom_wkt, "fuente": FUENTE, "prov_id": id_provincia_indec},
            )

            if result.rowcount > 0:
                updated += 1

        except Exception as e:
            errors += 1
            if errors < 5:
                print(
                    f"   ⚠️  Error procesando provincia {props.get('nombre', 'desconocida')}: {e}"
                )

    # Commit automático al salir del contexto engine.begin()
    print(f"✅ Geometrías de provincias actualizadas: {updated}")
    if errors > 0:
        print(f"⚠️  Errores: {errors}")

    return updated


def seed_geometrias_departamentos(conn: Connection) -> int:
    """
    Descarga GeoJSON de departamentos y actualiza las geometrías en la BD.

    Solo actualiza departamentos que ya existen (por id_departamento_indec + id_provincia_indec).
    """
    print("\n🗺️  Cargando geometrías de DEPARTAMENTOS...")

    # Verificar si ya hay geometrías cargadas
    check_stmt = text("""
        SELECT COUNT(*) FROM departamento WHERE geometria IS NOT NULL
    """)
    result = conn.execute(check_stmt).scalar()

    if result and result > 0:
        print(f"   ✓ Ya hay {result} departamentos con geometría. Saltando...")
        return 0

    # Descargar GeoJSON
    geojson = descargar_geojson(DEPARTAMENTOS_GEOJSON_URL, "departamentos")
    if not geojson:
        return 0

    features = geojson.get("features", [])
    print(f"   Descargados: {len(features)} departamentos con geometría")

    updated = 0
    errors = 0
    not_found = 0

    for feature in features:
        props = {}
        try:
            props = feature.get("properties", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # ID completo de departamento INDEC (5 dígitos, ej: "06014")
            id_full = props.get("id", "")
            if not id_full or len(id_full) < 4:
                continue

            id_departamento_indec = int(id_full)

            # ID de provincia desde las props anidadas
            provincia_info = props.get("provincia", {})
            id_provincia_indec = int(provincia_info.get("id", 0))

            if not id_provincia_indec:
                continue

            # Convertir geometría a WKT MultiPolygon
            geom_wkt = geometry_to_multipolygon_wkt(geometry)

            # UPDATE usando ST_GeomFromText
            stmt = text("""
                UPDATE departamento
                SET
                    geometria = ST_GeomFromText(:geom_wkt, 4326),
                    fuente_geometria = :fuente
                WHERE id_departamento_indec = :dept_id
                  AND id_provincia_indec = :prov_id
            """)

            result = conn.execute(
                stmt,
                {
                    "geom_wkt": geom_wkt,
                    "fuente": FUENTE,
                    "dept_id": id_departamento_indec,
                    "prov_id": id_provincia_indec,
                },
            )

            if result.rowcount > 0:
                updated += 1
                if updated % 100 == 0:
                    print(f"   Actualizados: {updated}...")
            else:
                not_found += 1

        except Exception as e:
            errors += 1
            if errors < 5:
                print(
                    f"   ⚠️  Error procesando departamento {props.get('nombre', 'desconocido')}: {e}"
                )

    # Commit automático al salir del contexto engine.begin()
    print(f"✅ Geometrías de departamentos actualizadas: {updated}")
    if not_found > 0:
        print(
            f"ℹ️  Departamentos no encontrados en BD: {not_found} (normal si no están todos)"
        )
    if errors > 0:
        print(f"⚠️  Errores: {errors}")

    return updated


def main() -> None:
    """Función principal para ejecutar standalone."""
    print("\n" + "=" * 70)
    print("🗺️  SEED DE GEOMETRÍAS DESDE API GEOREF")
    print("=" * 70)
    print("\nEste proceso descargará geometrías (polígonos) para:")
    print("  📍 24 Provincias (~15 MB)")
    print("  📍 ~530 Departamentos (~80 MB)")
    print("\n⏱️  Esto puede tomar 2-5 minutos...")
    print("=" * 70)

    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
    )

    # Cambiar postgresql+asyncpg:// por postgresql://
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Crear engine y conexión
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        # Provincias
        prov_count = seed_geometrias_provincias(conn)

        # Departamentos
        dept_count = seed_geometrias_departamentos(conn)

    print("\n" + "=" * 70)
    print("✅ SEED DE GEOMETRÍAS COMPLETADO")
    print("=" * 70)
    print("\nGeometrías cargadas:")
    print(f"  ✅ {prov_count} Provincias")
    print(f"  ✅ {dept_count} Departamentos")
    print("=" * 70)


if __name__ == "__main__":
    main()
