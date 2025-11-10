#!/usr/bin/env python3
"""
Actualiza las asignaciones de localidad para establecimientos IGN existentes.

Usa el algoritmo mejorado de reverse geocoding para re-asignar localidades
a establecimientos IGN que ya están en la base de datos, sin eliminarlos
(para preservar relaciones con eventos).

Algoritmo v2 (mejorado):
1. Buscar departamento más cercano al punto (lat, lng)
2. Dentro de ese departamento, buscar la localidad MÁS CERCANA al punto
3. Si no hay localidades con coordenadas, usar la primera del departamento
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import os

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))


def asignar_localidad_por_coordenadas(conn, lat: float, lng: float) -> int | None:
    """
    Asigna localidad INDEC usando reverse geocoding mejorado.

    Estrategia v2 (mejorada):
    1. Buscar departamento más cercano al punto (lat, lng)
    2. Dentro de ese departamento, buscar la localidad MÁS CERCANA al punto
    3. Si no hay localidades con coordenadas, usar la primera del departamento

    Args:
        conn: Conexión SQLAlchemy
        lat: Latitud del punto
        lng: Longitud del punto

    Returns:
        id_localidad_indec o None si no se encuentra
    """
    # Paso 1: Encontrar departamento más cercano
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


def actualizar_localidades_ign(conn):
    """
    Actualiza las localidades de establecimientos IGN con coordenadas válidas.

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Tuple (actualizados, sin_cambio, sin_coords)
    """
    print("\n" + "="*70)
    print("🗺️  ACTUALIZANDO LOCALIDADES DE ESTABLECIMIENTOS IGN")
    print("="*70)

    # Obtener establecimientos IGN con coordenadas
    result = conn.execute(text("""
        SELECT id, nombre, latitud, longitud, id_localidad_indec
        FROM establecimiento
        WHERE source = 'IGN'
          AND latitud IS NOT NULL
          AND longitud IS NOT NULL
        ORDER BY id
    """))

    establecimientos = result.fetchall()
    print(f"\n📊 Total establecimientos IGN con coordenadas: {len(establecimientos):,}")

    actualizados = 0
    sin_cambio = 0
    sin_coords = 0
    errores = 0

    for idx, row in enumerate(establecimientos, 1):
        if idx % 1000 == 0:
            print(f"   Procesados: {idx}/{len(establecimientos)} ({actualizados} actualizados, {sin_cambio} sin cambio)")

        estab_id = row[0]
        nombre = row[1]
        lat = row[2]
        lng = row[3]
        localidad_actual = row[4]

        try:
            # Calcular nueva localidad con algoritmo mejorado
            nueva_localidad = asignar_localidad_por_coordenadas(conn, lat, lng)

            if nueva_localidad is None:
                sin_coords += 1
                continue

            # Si cambió la localidad, actualizar
            if nueva_localidad != localidad_actual:
                conn.execute(text("""
                    UPDATE establecimiento
                    SET id_localidad_indec = :nueva_localidad,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :estab_id
                """), {"nueva_localidad": nueva_localidad, "estab_id": estab_id})
                actualizados += 1
            else:
                sin_cambio += 1

        except Exception as e:
            errores += 1
            if errores <= 10:  # Solo mostrar primeros 10 errores
                print(f"   ⚠️  Error procesando {nombre}: {e}")

    # Commit cambios
    conn.commit()

    print(f"\n   Procesados: {len(establecimientos)}/{len(establecimientos)} ({actualizados} actualizados, {sin_cambio} sin cambio)")

    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"  ✅ Localidades actualizadas: {actualizados:,}")
    print(f"  ⚪ Sin cambio: {sin_cambio:,}")
    print(f"  ⚠️  Sin localidad asignada: {sin_coords:,}")
    if errores > 0:
        print(f"  ❌ Errores: {errores}")
    print()

    return actualizados, sin_cambio, sin_coords


def main():
    """Función principal"""
    print("="*70)
    print("ACTUALIZAR LOCALIDADES DE ESTABLECIMIENTOS IGN")
    print("="*70)

    # Crear engine desde settings
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        actualizados, sin_cambio, sin_coords = actualizar_localidades_ign(conn)

    print("✅ Actualización completada\n")
    return actualizados


if __name__ == "__main__":
    main()
