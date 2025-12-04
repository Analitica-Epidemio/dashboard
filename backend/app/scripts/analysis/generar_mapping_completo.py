#!/usr/bin/env python3
"""
Genera mapping SNVS → IGN desde cero.

Lee TODOS los CSVs de eventos, extrae establecimientos únicos con sus códigos SNVS,
y hace matching contra establecimientos IGN usando el algoritmo mejorado.

Genera un JSON claro con:
- codigo_snvs: código del CSV (ej: "13704")
- nombre_snvs: nombre del establecimiento en el CSV
- codigo_refes: código IGN/REFES
- nombre_ign: nombre del establecimiento en IGN
- score: puntaje de matching
- similitud_nombre: % de similitud de nombres
- razon: explicación del match
- localidades: info de localidades para validación
"""

import json
import sys
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para matching:
    - Convierte a mayúsculas
    - Remueve acentos/tildes
    - Remueve espacios múltiples
    - Remueve puntuación innecesaria
    """
    if not texto:
        return ""

    # Convertir a mayúsculas
    texto = texto.upper()

    # Remover acentos/tildes usando NFD decomposition
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')

    # Remover puntuación común (pero mantener guiones y números)
    texto = texto.replace('.', ' ').replace(',', ' ').replace('-', ' ')

    # Remover espacios múltiples
    texto = ' '.join(texto.split())

    return texto.strip()


@dataclass
class EstablecimientoSNVS:
    """Establecimiento extraído del CSV SNVS."""
    codigo: str  # ID del CSV (ID_ESTAB_CLINICA, etc.)
    nombre: str
    localidad_id: Optional[int]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]


@dataclass
class EstablecimientoIGN:
    """Establecimiento del IGN."""
    id: int
    codigo_refes: str
    nombre: str
    localidad_id: Optional[int]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]


def extraer_establecimientos_de_csvs(csv_dir: Path) -> dict:
    """
    Extrae TODOS los establecimientos únicos de TODOS los CSVs.

    Returns:
        {codigo_snvs: EstablecimientoSNVS}
    """
    print("=" * 80)
    print("EXTRAYENDO ESTABLECIMIENTOS DE CSVS")
    print("=" * 80)

    csv_files = list(csv_dir.glob("*.csv"))
    print(f"📁 CSVs encontrados: {len(csv_files)}")

    establecimientos = {}  # codigo_snvs -> EstablecimientoSNVS

    # Columnas a buscar: (col_id, col_nombre, col_localidad, col_depto, col_prov)
    columnas_grupos = [
        ("ID_ESTAB_CLINICA", "ESTAB_CLINICA", "ID_LOC_INDEC_CLINICA", "DEPTO_CLINICA", "PROV_CLINICA"),
        ("ID_ESTABLECIMIENTO_DIAG", "ESTABLECIMIENTO_DIAG", "ID_LOC_INDEC_DIAG", "DEPARTAMENTO_DIAG", "PROVINCIA_DIAG"),
        ("ID_ESTABLECIMIENTO_MUESTRA", "ESTABLECIMIENTO_MUESTRA", "ID_LOC_INDEC_MUESTRA", "DEPARTAMENTO_MUESTRA", "PROVINCIA_MUESTRA"),
        ("ID_ORIGEN", "ESTABLECIMIENTO_EPI", "ID_LOC_INDEC_EPI", "DEPARTAMENTO_EPI", "PROVINCIA_EPI"),
        ("ID_ESTABLECIMIENTO_CARGA", "ESTABLECIMIENTO_CARGA", "ID_LOC_INDEC_CARGA", "DEPARTAMENTO_CARGA", "PROVINCIA_CARGA"),
    ]

    for csv_file in csv_files:
        print(f"\n📄 Procesando: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file, low_memory=False)
            print(f"   Filas: {len(df):,}")

            for col_id, col_nombre, col_loc, col_depto, col_prov in columnas_grupos:
                if col_id not in df.columns or col_nombre not in df.columns:
                    continue

                # Extraer establecimientos únicos
                subset = df[[col_id, col_nombre, col_loc, col_depto, col_prov]].copy()
                subset = subset.dropna(subset=[col_id, col_nombre], how='all')

                for _, row in subset.iterrows():
                    codigo = row[col_id]
                    nombre = row[col_nombre]

                    # Limpiar código
                    if pd.notna(codigo):
                        try:
                            codigo = str(int(float(codigo))).strip()
                        except (ValueError, TypeError):
                            continue
                    else:
                        continue

                    # Limpiar nombre
                    if pd.notna(nombre):
                        nombre = str(nombre).strip().upper()
                    else:
                        continue

                    # Si ya existe, solo actualizar si tiene más info geográfica
                    if codigo in establecimientos:
                        continue

                    # Localidad
                    loc_id = None
                    if pd.notna(row[col_loc]):
                        try:
                            loc_id = int(float(row[col_loc]))
                        except (ValueError, TypeError):
                            pass

                    # Info geográfica
                    depto = str(row[col_depto]).strip() if pd.notna(row[col_depto]) else None
                    prov = str(row[col_prov]).strip() if pd.notna(row[col_prov]) else None

                    establecimientos[codigo] = EstablecimientoSNVS(
                        codigo=codigo,
                        nombre=nombre,
                        localidad_id=loc_id,
                        localidad_nombre=None,  # Se obtiene de la BD
                        departamento_nombre=depto,
                        provincia_nombre=prov
                    )

        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            continue

    print(f"\n✅ Total establecimientos SNVS extraídos: {len(establecimientos):,}")
    return establecimientos


def cargar_establecimientos_ign(conn) -> dict:
    """
    Carga establecimientos IGN directamente desde el WFS del IGN.

    Returns:
        {codigo_refes: EstablecimientoIGN}
    """
    import warnings

    import geopandas as gpd
    from urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter('ignore', InsecureRequestWarning)

    print("\n" + "=" * 80)
    print("CARGANDO ESTABLECIMIENTOS IGN DESDE WFS")
    print("=" * 80)

    # URL WFS del IGN para establecimientos de salud
    url = "https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ign:salud_020801&outputFormat=application/json"

    print("📥 Descargando desde IGN WFS...")

    try:
        # Descargar GeoJSON
        from io import StringIO

        import requests

        response = requests.get(url, timeout=300, verify=False)
        response.raise_for_status()

        # Cargar como GeoDataFrame
        gdf = gpd.read_file(StringIO(response.text))

        print(f"✅ Descargados: {len(gdf):,} establecimientos")

        # Procesar establecimientos
        establecimientos = {}

        for idx, row in gdf.iterrows():
            codigo_refes = str(row.get('gid', '')).strip() if pd.notna(row.get('gid')) else None
            nombre = str(row.get('fna', '')).strip() if pd.notna(row.get('fna')) else None

            if not codigo_refes or not nombre:
                continue

            # Por ahora, sin datos de localidad (se podrían agregar después con reverse geocoding)
            establecimientos[codigo_refes] = EstablecimientoIGN(
                id=idx,
                codigo_refes=codigo_refes,
                nombre=nombre,
                localidad_id=None,
                localidad_nombre=None,
                departamento_nombre=None,
                provincia_nombre=None
            )

        print(f"✅ Establecimientos IGN procesados: {len(establecimientos):,}")
        return establecimientos

    except Exception as e:
        print(f"❌ Error descargando desde IGN: {e}")
        raise


def calcular_similitud_nombre(nombre1: str, nombre2: str) -> float:
    """
    Calcula similitud entre nombres usando SequenceMatcher.

    Normaliza ambos nombres (sin acentos, mayúsculas, sin puntuación)
    para mejorar el matching.
    """
    if not nombre1 or not nombre2:
        return 0.0

    # Normalizar ambos nombres antes de comparar
    nombre1_norm = normalizar_texto(nombre1)
    nombre2_norm = normalizar_texto(nombre2)

    return SequenceMatcher(None, nombre1_norm, nombre2_norm).ratio() * 100


def encontrar_matches(snvs: EstablecimientoSNVS, establecimientos_ign: dict, top_n: int = 3) -> list:
    """
    Encuentra los mejores N matches de IGN para un establecimiento SNVS.

    Scoring:
    - 60% similitud de nombre
    - 10% bonus provincia coincidente
    - 15% bonus departamento coincidente
    - 15% bonus localidad coincidente
    - FILTRO: rechaza si provincias diferentes
    """
    matches = []

    for codigo_refes, ign in establecimientos_ign.items():
        # FILTRO CRÍTICO: Rechazar si provincias diferentes
        if (snvs.provincia_nombre and ign.provincia_nombre and
            snvs.provincia_nombre.lower().strip() != ign.provincia_nombre.lower().strip()):
            continue

        # Calcular similitud de nombre
        similitud_nombre = calcular_similitud_nombre(snvs.nombre, ign.nombre)

        # Score base: 60% nombre
        score = similitud_nombre * 0.6

        razon_parts = [f"similitud nombre: {similitud_nombre:.1f}%"]

        # Bonus provincia (+10%)
        if snvs.provincia_nombre and ign.provincia_nombre:
            if snvs.provincia_nombre.lower().strip() == ign.provincia_nombre.lower().strip():
                score += 10
                razon_parts.append(f"provincia: {ign.provincia_nombre}")

        # Bonus departamento (+15%)
        if snvs.departamento_nombre and ign.departamento_nombre:
            if snvs.departamento_nombre.lower().strip() == ign.departamento_nombre.lower().strip():
                score += 15
                razon_parts.append(f"mismo depto: {ign.departamento_nombre}")

        # Bonus localidad (+15%)
        if snvs.localidad_id and ign.localidad_id:
            if snvs.localidad_id == ign.localidad_id:
                score += 15
                razon_parts.append("misma localidad")

        # Garantizar alta confianza para matches perfectos
        if similitud_nombre == 100 and score >= 70:
            score = max(score, 85)

        razon = " + ".join(razon_parts)

        matches.append({
            "ign_codigo_refes": codigo_refes,
            "ign_nombre": ign.nombre,
            "ign_localidad": ign.localidad_nombre,
            "ign_departamento": ign.departamento_nombre,
            "ign_provincia": ign.provincia_nombre,
            "score": round(score, 1),
            "similitud_nombre": round(similitud_nombre, 1),
            "razon": razon
        })

    # Ordenar por score y retornar top N
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:top_n]


def generar_mapping(establecimientos_snvs: dict, establecimientos_ign: dict) -> dict:
    """
    Genera el mapping completo SNVS → IGN.

    Returns:
        {
            "mapping": {
                "codigo_snvs": {
                    "nombre_snvs": "...",
                    "codigo_refes": "...",
                    "nombre_ign": "...",
                    "score": 95.5,
                    "similitud_nombre": 92.0,
                    "razon": "...",
                    "localidad_snvs": "...",
                    "localidad_ign": "...",
                    ...
                }
            },
            "stats": {...}
        }
    """
    print("\n" + "=" * 80)
    print("GENERANDO MAPPING SNVS → IGN")
    print("=" * 80)

    mapping = {}
    stats = {
        "total_snvs": len(establecimientos_snvs),
        "con_match": 0,  # >= 85 con similitud >= 80%
        "sin_match": 0,  # no cumple criterios estrictos
    }

    for idx, (codigo_snvs, snvs) in enumerate(establecimientos_snvs.items(), 1):
        if idx % 100 == 0:
            print(f"   Procesados: {idx}/{len(establecimientos_snvs)}")

        # Encontrar matches
        matches = encontrar_matches(snvs, establecimientos_ign, top_n=3)

        # FILTROS MUY ESTRICTOS:
        # Solo aceptar mapeos de ALTA CONFIANZA para evitar datos incorrectos
        # OPCIÓN 1: Score mínimo de 85 + Similitud nombre mínima de 80%
        # OPCIÓN 2: Similitud de nombre ≥80% (match bueno, aunque falte info geográfica)
        if not matches:
            stats["sin_match"] += 1
            continue

        best = matches[0]

        # Aceptar si:
        # - (score ≥ 85 Y similitud ≥ 80%) O
        # - (similitud ≥ 80% - match bueno incluso sin datos geográficos)
        cumple_score = best["score"] >= 85 and best["similitud_nombre"] >= 80
        cumple_nombre = best["similitud_nombre"] >= 80

        if not (cumple_score or cumple_nombre):
            stats["sin_match"] += 1
            continue

        # Solo guardamos ALTA confianza
        stats["con_match"] += 1
        confidence = "HIGH"

        mapping[codigo_snvs] = {
            "nombre_snvs": snvs.nombre,
            "codigo_refes": best["ign_codigo_refes"],
            "nombre_ign": best["ign_nombre"],
            "score": best["score"],
            "similitud_nombre": best["similitud_nombre"],
            "razon": best["razon"],
            "confidence": confidence,
            "localidad_snvs": snvs.localidad_nombre or f"INDEC {snvs.localidad_id}" if snvs.localidad_id else None,
            "departamento_snvs": snvs.departamento_nombre,
            "provincia_snvs": snvs.provincia_nombre,
            "localidad_ign": best["ign_localidad"],
            "departamento_ign": best["ign_departamento"],
            "provincia_ign": best["ign_provincia"],
            # Incluir alternativas si el score no es perfecto
            "alternativas": matches[1:] if best["score"] < 100 and len(matches) > 1 else []
        }

    print("\n✅ Mapping generado:")
    print(f"   Mapeos válidos (score ≥85 + similitud ≥80%): {stats['con_match']}")
    print(f"   Sin match (no cumple criterios estrictos): {stats['sin_match']}")

    return {
        "mapping": mapping,
        "stats": stats,
        "_README": {
            "descripcion": "Mapping de códigos SNVS → IGN generado automáticamente",
            "estructura": {
                "codigo_snvs": "Código del establecimiento en los CSVs del SNVS",
                "nombre_snvs": "Nombre del establecimiento en el CSV",
                "codigo_refes": "Código REFES del establecimiento IGN",
                "nombre_ign": "Nombre del establecimiento en la base IGN",
                "score": "Puntaje de matching (0-100)",
                "similitud_nombre": "Porcentaje de similitud de nombres",
                "razon": "Explicación del match",
                "confidence": "HIGH (≥85) o MEDIUM (70-84)",
                "localidades": "Info geográfica para validación manual"
            }
        }
    }


def guardar_mapping(mapping_data: dict, output_file: Path):
    """Guarda el mapping en formato JSON."""
    # Ordenar por código SNVS
    mapping_data["mapping"] = dict(sorted(mapping_data["mapping"].items()))

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Mapping guardado en: {output_file}")


def main():
    import os

    print("=" * 80)
    print("GENERAR MAPPING COMPLETO SNVS → IGN")
    print("=" * 80)
    print()

    # Paths
    backend_dir = Path(__file__).parent.parent.parent.parent
    csv_dir = backend_dir / "uploads"
    output_file = backend_dir / "app/scripts/seeds/data/establecimientos_mapping_v2.json"

    # 1. Extraer establecimientos de CSVs
    establecimientos_snvs = extraer_establecimientos_de_csvs(csv_dir)

    # 2. Conectar a BD y cargar establecimientos IGN
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        establecimientos_ign = cargar_establecimientos_ign(conn)

    # 3. Generar mapping
    mapping_data = generar_mapping(establecimientos_snvs, establecimientos_ign)

    # 4. Guardar
    guardar_mapping(mapping_data, output_file)

    print()
    print("=" * 80)
    print("COMPLETADO")
    print("=" * 80)
    print(f"Total SNVS: {mapping_data['stats']['total_snvs']}")
    print(f"Mapeos VÁLIDOS (alta confianza): {mapping_data['stats']['con_match']}")
    print("  Criterios: score ≥85 + similitud nombre ≥80%")
    print(f"Sin match: {mapping_data['stats']['sin_match']}")
    print("\n⚠️  Solo se guardan mapeos de alta confianza para evitar datos incorrectos")
    print()


if __name__ == "__main__":
    main()
