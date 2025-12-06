#!/usr/bin/env python3
"""
Investiga hospitales importantes que no fueron mapeados automáticamente.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import os
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
)
if "postgresql+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL)


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para matching."""
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    texto = texto.replace(".", " ").replace(",", " ").replace("-", " ")
    texto = " ".join(texto.split())
    return texto.strip()


# Hospitales no mapeados
hospitales_faltantes = [
    (13845, "HOSPITAL REGIONAL COMODORO RIVADAVIA", 2439),
    (13570, "HOSPITAL RURAL EL HOYO", 18),
    (13584, "HOSPITAL RURAL LAGO PUELO", 14),
    (13680, "HOSPITAL ZONAL TRELEW CENTRO MATERNO INFANTIL", 14),
    (13568, "HOSPITAL RURAL CHOLILA", 5),
]

print("=" * 80)
print("INVESTIGACIÓN DE HOSPITALES NO MAPEADOS")
print("=" * 80)
print()

candidatos_para_agregar = []

with engine.connect() as conn:
    for snvs_id, nombre_snvs, eventos in hospitales_faltantes:
        print(f"🔍 {nombre_snvs} (SNVS: {snvs_id}) - {eventos} eventos")
        print("-" * 80)

        # Normalizar nombre
        nombre_norm = normalizar_texto(nombre_snvs)

        # Buscar en IGN por palabras clave
        palabras = nombre_norm.split()
        palabras_busqueda = [
            p
            for p in palabras
            if p not in ["HOSPITAL", "CENTRO", "DE", "LA", "EL", "Y"]
        ]

        mejor_match = None
        mejor_similitud = 0.0

        for palabra in palabras_busqueda[
            :3
        ]:  # Buscar por las 3 primeras palabras significativas
            # Buscar en la tabla establecimiento (estructura OLD)
            result = conn.execute(
                text("""
                SELECT e.establecimiento as nombre, e.id_establecimiento as codigo_snvs,
                       l.nombre as localidad,
                       d.nombre as departamento,
                       p.nombre as provincia
                FROM establecimiento e
                LEFT JOIN localidad l ON e.id_localidad_establecimiento = l.id_localidad_indec
                LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
                LEFT JOIN provincia p ON d.id_provincia_indec = p.id_provincia_indec
                WHERE e.establecimiento ILIKE :busqueda
                LIMIT 5
            """),
                {"busqueda": f"%{palabra}%"},
            )

            rows = result.fetchall()
            if rows:
                print(f"  📍 Búsqueda por '{palabra}':")
                for row in rows:
                    nombre_db = row[0]
                    id_db = row[1]
                    localidad = row[2] or "SIN LOCALIDAD"
                    depto = row[3] or "SIN DEPTO"
                    prov = row[4] or "SIN PROV"

                    # Calcular similitud
                    nombre_db_norm = normalizar_texto(nombre_db)
                    similitud = (
                        SequenceMatcher(None, nombre_norm, nombre_db_norm).ratio() * 100
                    )

                    print(f"    • {nombre_db}")
                    print(f"      ID: {id_db} | Similitud: {similitud:.1f}%")
                    print(f"      📍 {localidad}, {depto}, {prov}")

                    # Guardar mejor match
                    if similitud > mejor_similitud:
                        mejor_similitud = similitud
                        mejor_match = {
                            "snvs_id": snvs_id,
                            "nombre_snvs": nombre_snvs,
                            "nombre_db": nombre_db,
                            "id_db": id_db,
                            "similitud": similitud,
                            "localidad": localidad,
                            "depto": depto,
                            "prov": prov,
                            "eventos": eventos,
                        }

                    print()
                break  # Solo mostrar resultados de la primera palabra que tenga matches

        if mejor_match and mejor_similitud >= 75:
            candidatos_para_agregar.append(mejor_match)

        print()

print("=" * 80)
print("RESUMEN - CANDIDATOS PARA AGREGAR MANUALMENTE")
print("=" * 80)
print()

if candidatos_para_agregar:
    print(
        f"Encontrados {len(candidatos_para_agregar)} candidatos con similitud >= 75%:"
    )
    print()
    for c in candidatos_para_agregar:
        print(
            f"✓ SNVS: {c['nombre_snvs']} (ID: {c['snvs_id']}) - {c['eventos']} eventos"
        )
        print(f"  → DB: {c['nombre_db']} (ID: {c['id_db']})")
        print(f"  Similitud: {c['similitud']:.1f}%")
        print(f"  Ubicación: {c['localidad']}, {c['depto']}, {c['prov']}")
        print()
else:
    print("No se encontraron candidatos automáticos.")
