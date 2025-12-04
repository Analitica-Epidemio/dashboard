"""
Seed para cargar departamentos y localidades desde la API Georef (datos.gob.ar)

Fuente: https://apis.datos.gob.ar/georef/api/

Este script:
1. Descarga departamentos desde la API Georef
2. Los inserta en la BD con coordenadas
3. Descarga localidades desde la API Georef
4. Las inserta en la BD con coordenadas y población (censo 2010)
"""
import json
import os
import time
import urllib.request

from sqlalchemy import create_engine, text


def normalizar_nombre(nombre: str) -> str:
    """Normaliza nombres para matching"""
    return (
        nombre.upper()
        .strip()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )


def seed_provincias_desde_georef(conn):
    """Carga provincias desde API Georef"""
    print("\n📍 Descargando provincias desde API Georef...")

    # API Georef - traer todas las provincias
    url = "https://apis.datos.gob.ar/georef/api/provincias?max=50"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error descargando provincias: {e}")
        return 0

    provincias = data.get("provincias", [])
    print(f"   Descargadas: {len(provincias)} provincias")

    inserted = 0
    errors = 0

    for prov in provincias:
        # Extraer datos
        id_provincia_indec = int(prov["id"])
        nombre = prov["nombre"]

        # Coordenadas del centroide
        latitud = prov["centroide"]["lat"]
        longitud = prov["centroide"]["lon"]

        # INSERT simple (asume DB vacía)
        stmt = text("""
            INSERT INTO provincia (
                id_provincia_indec,
                nombre,
                latitud,
                longitud
            )
            VALUES (:prov_id, :nombre, :lat, :lon)
        """)

        try:
            conn.execute(stmt, {
                "prov_id": id_provincia_indec,
                "nombre": nombre,
                "lat": latitud,
                "lon": longitud
            })
            inserted += 1
        except Exception as e:
            errors += 1
            print(f"   ⚠️  Error con {nombre}: {e}")
            continue

    # Commit
    conn.commit()
    print(f"✅ Provincias procesadas: {inserted}")
    if errors > 0:
        print(f"⚠️  Errores: {errors}")
    return inserted


def seed_departamentos_desde_georef(conn):
    """Carga departamentos desde API Georef"""
    print("\n📍 Descargando departamentos desde API Georef...")

    # API Georef - traer todos los departamentos
    url = "https://apis.datos.gob.ar/georef/api/departamentos?max=1000"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error descargando departamentos: {e}")
        return 0

    departamentos = data.get("departamentos", [])
    print(f"   Descargados: {len(departamentos)} departamentos")

    inserted = 0
    updated = 0
    errors = 0

    for dept in departamentos:
        # Extraer datos
        id_full = dept["id"]  # Ej: "06014"
        nombre = dept["nombre"]
        provincia_id = int(dept["provincia"]["id"])  # Ej: "06" -> 6
        dept_id = int(id_full)  # Usar el ID completo INDEC (5 dígitos)

        # Coordenadas del centroide
        latitud = dept["centroide"]["lat"]
        longitud = dept["centroide"]["lon"]

        # INSERT simple (asume DB vacía)
        stmt = text("""
            INSERT INTO departamento (
                id_departamento_indec,
                nombre,
                id_provincia_indec,
                latitud,
                longitud
            )
            VALUES (:dept_id, :nombre, :prov_id, :lat, :lon)
        """)

        try:
            conn.execute(stmt, {
                "dept_id": dept_id,
                "nombre": nombre,
                "prov_id": provincia_id,
                "lat": latitud,
                "lon": longitud
            })
            inserted += 1
            if inserted % 50 == 0:
                print(f"   Procesados: {inserted}...")
        except Exception as e:
            errors += 1
            if errors < 5:
                print(f"   ⚠️  Error con {nombre}: {e}")
            continue

    # Commit final de toda la sesión
    conn.commit()
    print(f"\n✅ Departamentos procesados: {inserted}")
    if errors > 0:
        print(f"⚠️  Errores: {errors}")
    return inserted


def seed_localidades_desde_georef(conn, max_localidades=5000):
    """
    Carga localidades desde API Georef

    Nota: La API Georef tiene ~60,000 localidades totales.
    Por defecto limitamos a 5000 para no sobrecargar.
    """
    print(f"\n📍 Descargando localidades desde API Georef (máx: {max_localidades})...")

    # API Georef - paginación
    url = "https://apis.datos.gob.ar/georef/api/localidades"

    todas_localidades = []
    inicio = 0
    cantidad_por_pagina = 1000  # Max permitido por la API

    while len(todas_localidades) < max_localidades:
        url_con_params = f"{url}?max={cantidad_por_pagina}&inicio={inicio}"

        try:
            print(f"   Descargando desde {inicio}...")
            with urllib.request.urlopen(url_con_params, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"❌ Error descargando localidades: {e}")
            break

        localidades = data.get("localidades", [])
        if not localidades:
            break

        todas_localidades.extend(localidades)
        inicio += cantidad_por_pagina

        # Respetar rate limits
        time.sleep(0.5)

        if len(localidades) < cantidad_por_pagina:
            break

    print(f"   Descargadas: {len(todas_localidades)} localidades")

    inserted = 0
    skipped_no_dept = 0
    errors = 0

    for loc in todas_localidades:
        # Extraer datos
        id_full = loc["id"]  # Ej: "060014010"
        nombre = loc["nombre"]

        # IDs INDEC
        id_localidad = int(id_full)
        provincia_id = int(loc["provincia"]["id"])

        # Departamento (si existe)
        if loc.get("departamento"):
            dept_id_full = loc["departamento"]["id"]
            dept_id = int(dept_id_full)  # Usar el ID completo INDEC (5 dígitos)
        else:
            skipped_no_dept += 1
            continue

        # Coordenadas
        if loc.get("centroide"):
            latitud = loc["centroide"]["lat"]
            longitud = loc["centroide"]["lon"]
        else:
            latitud = None
            longitud = None

        # Población (del censo 2010)
        poblacion = loc.get("poblacion")
        if poblacion and isinstance(poblacion, dict):
            poblacion = poblacion.get("valor")

        # INSERT simple (asume DB vacía, sin verificar departamento)
        # Nota: id_departamento será NULL, solo guardamos id_departamento_indec
        stmt = text("""
            INSERT INTO localidad (
                id_localidad_indec,
                nombre,
                id_departamento_indec,
                poblacion,
                latitud,
                longitud
            )
            VALUES (:loc_id, :nombre, :dept_id, :poblacion, :lat, :lon)
        """)

        try:
            conn.execute(stmt, {
                "loc_id": id_localidad,
                "nombre": nombre,
                "dept_id": dept_id,
                "poblacion": poblacion,
                "lat": latitud,
                "lon": longitud
            })
            inserted += 1
            if inserted % 500 == 0:
                print(f"   Procesadas: {inserted}...")
        except Exception as e:
            errors += 1
            if errors < 5:
                print(f"   ⚠️  Error con {nombre}: {e}")
            continue

    # Commit final
    conn.commit()
    print(f"\n✅ Localidades procesadas: {inserted}")
    print(f"⚠️  Localidades sin departamento: {skipped_no_dept}")
    if errors > 0:
        print(f"⚠️  Errores: {errors}")
    return inserted


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🗺️  SEED DESDE API GEOREF (datos.gob.ar)")
    print("="*70)
    print("\nEste proceso descargará:")
    print("  📍 ~530 Departamentos con coordenadas")
    print("  📍 ~5,000 Localidades con coordenadas y población")
    print("\n⏱️  Esto puede tomar 2-3 minutos...")
    print("="*70)

    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db"
    )

    # Cambiar postgresql+asyncpg:// por postgresql://
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    # Crear engine y conexión
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Paso 0: Provincias
        print("\n" + "="*70)
        print("PASO 1/3: Provincias")
        print("="*70)
        prov_count = seed_provincias_desde_georef(conn)

        # Paso 1: Departamentos
        print("\n" + "="*70)
        print("PASO 2/3: Departamentos")
        print("="*70)
        dept_count = seed_departamentos_desde_georef(conn)

        # Paso 2: Localidades
        print("\n" + "="*70)
        print("PASO 3/3: Localidades")
        print("="*70)
        loc_count = seed_localidades_desde_georef(conn, max_localidades=5000)

    print("\n" + "="*70)
    print("✅ SEED DESDE GEOREF COMPLETADO")
    print("="*70)
    print("\nDatos cargados:")
    print(f"  ✅ {prov_count} Provincias")
    print(f"  ✅ {dept_count} Departamentos")
    print(f"  ✅ {loc_count} Localidades")
    print("\nLas localidades incluyen:")
    print("  • Coordenadas (latitud/longitud)")
    print("  • Población del Censo 2010")
    print("="*70)


if __name__ == "__main__":
    main()
