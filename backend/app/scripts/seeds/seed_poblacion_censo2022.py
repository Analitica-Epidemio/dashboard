"""
Seed para cargar datos de población del Censo 2022 (INDEC)

Fuente: https://www.indec.gob.ar/ftp/cuadros/poblacion/cnphv2022_resultados_provisionales.xlsx

Poblamos:
- Población de provincias (Cuadro 1)
- Población de departamentos (Cuadros 2.1 a 2.24)

El archivo se descarga automáticamente si no existe.
"""

import os
import sys
import urllib.request
from pathlib import Path

import pandas as pd

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import col, select, update

from app.domains.territorio.geografia_models import Departamento, Provincia

# URL del archivo del Censo 2022
CENSO_2022_URL = "https://www.indec.gob.ar/ftp/cuadros/poblacion/cnphv2022_resultados_provisionales.xlsx"


def descargar_censo_si_no_existe(archivo_path: Path) -> bool:
    """
    Descarga el archivo del Censo 2022 si no existe localmente.

    Returns:
        True si el archivo existe o se descargó correctamente, False en caso de error.
    """
    if archivo_path.exists():
        print(f"   ✓ Archivo censo ya existe: {archivo_path.name}")
        return True

    print("   Descargando Censo 2022 desde INDEC...")
    print(f"   URL: {CENSO_2022_URL}")

    try:
        # Crear directorio si no existe
        archivo_path.parent.mkdir(parents=True, exist_ok=True)

        # Descargar archivo
        urllib.request.urlretrieve(CENSO_2022_URL, archivo_path)

        # Verificar que se descargó correctamente
        if archivo_path.exists() and archivo_path.stat().st_size > 0:
            size_kb = archivo_path.stat().st_size / 1024
            print(f"   ✓ Descargado: {archivo_path.name} ({size_kb:.0f} KB)")
            return True
        else:
            print("   ❌ Error: archivo descargado está vacío")
            return False

    except Exception as e:
        print(f"   ❌ Error descargando censo: {e}")
        return False


# Mapeo de nombres de provincias del censo a códigos INDEC
PROVINCIA_CODES = {
    "CIUDAD AUTÓNOMA DE BUENOS AIRES": 2,
    "CIUDAD AUTONOMA DE BUENOS AIRES": 2,
    "BUENOS AIRES": 6,
    "CATAMARCA": 10,
    "CÓRDOBA": 14,
    "CORDOBA": 14,
    "CORRIENTES": 18,
    "CHACO": 22,
    "CHUBUT": 26,
    "ENTRE RÍOS": 30,
    "ENTRE RIOS": 30,
    "FORMOSA": 34,
    "JUJUY": 38,
    "LA PAMPA": 42,
    "LA RIOJA": 46,
    "MENDOZA": 50,
    "MISIONES": 54,
    "NEUQUÉN": 58,
    "NEUQUEN": 58,
    "RÍO NEGRO": 62,
    "RIO NEGRO": 62,
    "SALTA": 66,
    "SAN JUAN": 70,
    "SAN LUIS": 74,
    "SANTA CRUZ": 78,
    "SANTA FE": 82,
    "SANTIAGO DEL ESTERO": 86,
    "TUCUMÁN": 90,
    "TUCUMAN": 90,
    "TIERRA DEL FUEGO": 94,
    "TIERRA DEL FUEGO, ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR": 94,
    "TIERRA DEL FUEGO, ANTARTIDA E ISLAS DEL ATLANTICO SUR": 94,
}


def normalizar_nombre(nombre: str) -> str:
    """Normaliza nombre eliminando tildes y caracteres especiales"""
    return (
        nombre.upper()
        .strip()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ñ", "N")
        # Minúsculas con tilde
        .replace("á", "A")
        .replace("é", "E")
        .replace("í", "I")
        .replace("ó", "O")
        .replace("ú", "U")
        .replace("ñ", "N")
    )


def seed_poblacion_provincias(session: Session, archivo_path: Path) -> None:
    """Carga población de provincias desde Cuadro 1"""

    print("\n📊 Cargando población de provincias...")

    # Leer Cuadro 1
    df = pd.read_excel(archivo_path, sheet_name="Cuadro 1", header=2)

    updated_count = 0

    for _, row in df.iterrows():
        jurisdiccion = str(row["Jurisdicción"]).strip()

        # Saltar filas que no son provincias
        if pd.isna(jurisdiccion) or jurisdiccion == "Total":
            continue
        if "24 Partidos" in jurisdiccion or "Resto de partidos" in jurisdiccion:
            continue

        # Verificar que hay datos válidos
        if pd.isna(row["Total de población"]):
            continue

        poblacion_total = int(row["Total de población"])

        # Obtener código INDEC
        nombre_norm = normalizar_nombre(jurisdiccion)
        codigo_indec = PROVINCIA_CODES.get(nombre_norm)

        if not codigo_indec:
            print(f"⚠️  Provincia no encontrada en mapeo: {jurisdiccion}")
            continue

        # Actualizar provincia (en caso de que ya exista por otro seed previo)
        # O insertar si no existe
        # Actualizar provincia
        stmt = (
            update(Provincia)
            .where(col(Provincia.id_provincia_indec) == codigo_indec)
            .values(poblacion=poblacion_total)
        )
        result = session.execute(stmt)

        if result.rowcount > 0:  # type: ignore[union-attr]
            updated_count += 1
            print(f"✅ {jurisdiccion}: {poblacion_total:,} habitantes")
        else:
            print(
                f"⚠️  Provincia no encontrada en BD: {jurisdiccion} (código {codigo_indec})"
            )

    session.commit()
    print(f"\n✅ Actualizadas {updated_count} provincias")


def seed_poblacion_departamentos(session: Session, archivo_path: Path) -> None:
    """Carga población de departamentos desde Cuadros 2.1 a 2.24"""

    print("\n📊 Cargando población de departamentos...")

    # Mapeo de cuadros a provincias
    cuadros_provincias = {
        "Cuadro 2.1": 2,  # CABA
        "Cuadro 2.2": 6,  # Buenos Aires
        "Cuadro 2.3": 10,  # Catamarca
        "Cuadro 2.4": 22,  # Chaco
        "Cuadro 2.5": 26,  # Chubut
        "Cuadro 2.6": 14,  # Córdoba
        "Cuadro 2.7": 18,  # Corrientes
        "Cuadro 2.8": 30,  # Entre Ríos
        "Cuadro 2.9": 34,  # Formosa
        "Cuadro 2.10": 38,  # Jujuy
        "Cuadro 2.11": 42,  # La Pampa
        "Cuadro 2.12": 46,  # La Rioja
        "Cuadro 2.13": 50,  # Mendoza
        "Cuadro 2.14": 54,  # Misiones
        "Cuadro 2.15": 58,  # Neuquén
        "Cuadro 2.16": 62,  # Río Negro
        "Cuadro 2.17": 66,  # Salta
        "Cuadro 2.18": 70,  # San Juan
        "Cuadro 2.19": 74,  # San Luis
        "Cuadro 2.20": 78,  # Santa Cruz
        "Cuadro 2.21": 82,  # Santa Fe
        "Cuadro 2.22": 86,  # Santiago del Estero
        "Cuadro 2.23": 94,  # Tierra del Fuego
        "Cuadro 2.24": 90,  # Tucumán
    }

    total_updated = 0
    total_not_found = 0

    for cuadro, id_provincia_indec in cuadros_provincias.items():
        try:
            df = pd.read_excel(archivo_path, sheet_name=cuadro, header=2)

            # Obtener nombre de provincia
            stmt_prov = select(Provincia.nombre).where(
                Provincia.id_provincia_indec == id_provincia_indec
            )
            result_prov = session.execute(stmt_prov).first()

            if not result_prov:
                print(f"⚠️  Provincia no encontrada: código {id_provincia_indec}")
                continue

            print(f"\n  Procesando {result_prov[0]}...")

            # Pre-cargar departamentos de la provincia para normalizar en Python
            # Esto evita la query compleja con REPLACE múltiples en SQL
            deptos_result = session.execute(
                select(Departamento).where(
                    Departamento.id_provincia_indec == id_provincia_indec
                )
            )
            deptos_bd = deptos_result.scalars().all()

            # Mapa: nombre_normalizado -> id_departamento
            depto_map = {normalizar_nombre(d.nombre): d.id for d in deptos_bd}

            # La primera columna tiene el nombre del departamento/comuna/partido
            # La segunda columna tiene "Total" con la población
            primera_col = df.columns[0]

            for _, row in df.iterrows():
                nombre_depto = str(row[primera_col]).strip()

                # Saltar filas inválidas
                if pd.isna(nombre_depto) or nombre_depto == "Total":
                    continue
                if nombre_depto.startswith("Cuadro") or nombre_depto == "nan":
                    continue
                # Saltar filas que son números (comunas de CABA)
                if nombre_depto.isdigit():
                    continue
                # Saltar agregados
                if "24 Partidos" in nombre_depto or "Resto de partidos" in nombre_depto:
                    continue

                # Obtener población (segunda columna = Total)
                try:
                    poblacion = int(
                        row["Total (1)"]
                        if "Total (1)" in df.columns
                        else row[df.columns[1]]
                    )
                except (ValueError, KeyError):
                    continue

                # Limpiar nombre
                nombre_depto = (
                    nombre_depto.replace("Comuna ", "").replace("Partido ", "").strip()
                )
                nombre_norm = normalizar_nombre(nombre_depto)

                # Buscar en mapa
                id_depto = depto_map.get(nombre_norm)

                if id_depto:
                    # UPDATE usando ID
                    stmt_update = (
                        update(Departamento)
                        .where(col(Departamento.id) == id_depto)
                        .values(poblacion=poblacion)
                    )
                    session.execute(stmt_update)
                    total_updated += 1
                    print(f"    ✅ {nombre_depto}: {poblacion:,} hab")
                else:
                    total_not_found += 1
                    print(f"    ⚠️  No encontrado en BD: {nombre_depto}")

        except Exception as e:
            print(f"❌ Error procesando {cuadro}: {e}")
            continue

    session.commit()

    print(f"\n{'=' * 60}")
    print("✅ RESUMEN DEPARTAMENTOS:")
    print(f"   Actualizados: {total_updated}")
    print(f"   No encontrados: {total_not_found}")
    print(f"{'=' * 60}")


def main() -> None:
    """Función principal del seed"""
    print("\n🗺️  Seed de Población - Censo 2022...")

    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
    )

    # Cambiar postgresql+asyncpg:// por postgresql:// para usar psycopg2 síncrono
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Verificar/descargar archivo del censo
    data_dir = Path(__file__).parent / "data"
    archivo_censo = data_dir / "censo2022_poblacion.xlsx"

    if not descargar_censo_si_no_existe(archivo_censo):
        print("❌ No se pudo obtener el archivo del censo")
        return

    # Crear engine y sesión
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session:
        seed_poblacion_provincias(session, archivo_censo)
        seed_poblacion_departamentos(session, archivo_censo)

    print("\n✅ Seed de población completado\n")


if __name__ == "__main__":
    main()
