#!/usr/bin/env python3
"""
Agrega mapeos automáticos de alta confianza (score >= 85) al archivo de mapping.

Lee el reporte de análisis generado por top_establecimientos.py y extrae
todos los mapeos de alta confianza para agregarlos al JSON de mapping.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

backend_dir = Path(__file__).parent.parent.parent.parent
mapping_file = (
    backend_dir / "app/scripts/seeds/data/establecimientos_mapping_final.json"
)
reporte_file = backend_dir / "temp/establecimientos.txt"


def cargar_mapping_actual() -> Dict[str, Any]:
    """Carga el archivo JSON actual."""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def extraer_mapeos_del_reporte() -> List[Dict[str, Any]]:
    """
    Extrae mapeos de alta confianza del reporte.

    Formato del reporte:
    • SNVS: "HOSPITAL ZONAL ESQUEL" [ID: 8862]
      → IGN: "Hospital Zonal Esquel" [ID: 220]
      Score: 100.0 | Razón: similitud nombre: 100.0% + provincia: Chubut...
      REFES: 8946
    """
    with open(reporte_file, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Buscar sección de alta confianza
    match = re.search(
        r"MAPEOS DE ALTA CONFIANZA.*?(?=MAPEOS DE CONFIANZA MEDIA|$)",
        contenido,
        re.DOTALL,
    )
    if not match:
        print("⚠️  No se encontró sección de alta confianza")
        return []

    seccion_alta = match.group(0)

    # Extraer mapeos
    mapeos = []
    patron = r'• SNVS: "(.+?)" \[ID: (\d+)\]\s+→ IGN: "(.+?)" \[ID: (\d+)\]\s+Score: ([\d.]+).*?REFES: (\d+)'

    for match in re.finditer(patron, seccion_alta, re.DOTALL):
        snvs_nombre = match.group(1)
        snvs_id = match.group(2)
        ign_nombre = match.group(3)
        ign_id = match.group(4)
        score = float(match.group(5))
        codigo_refes = match.group(6)

        mapeos.append(
            {
                "snvs_nombre": snvs_nombre,
                "snvs_id": snvs_id,
                "ign_id": int(ign_id),
                "ign_codigo_refes": codigo_refes,
                "ign_nombre": ign_nombre,
                "score": score,
            }
        )

    return mapeos


def agregar_mapeos(
    data: Dict[str, Any], mapeos: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """Agrega los mapeos al JSON."""
    count_nuevos = 0
    count_existentes = 0

    for mapeo in mapeos:
        snvs_key = mapeo["snvs_nombre"]

        if snvs_key not in data["mapping"]:
            data["mapping"][snvs_key] = {
                "id": mapeo["ign_id"],
                "codigo_refes": mapeo["ign_codigo_refes"],
                "nombre": mapeo["ign_nombre"],
                "confidence": "HIGH",
                "score": mapeo["score"],
            }
            count_nuevos += 1
            print(f"  ✓ {snvs_key}")
            print(f"    → {mapeo['ign_nombre']} (score: {mapeo['score']})")
        else:
            count_existentes += 1

    return count_nuevos, count_existentes


def actualizar_stats(data: Dict[str, Any], nuevos_mapeos: int) -> None:
    """Actualiza las estadísticas."""
    matched_actual = data["_README"]["stats"]["matched"]
    total = data["_README"]["stats"]["total_csv_establecimientos"]

    nuevo_matched = matched_actual + nuevos_mapeos
    nueva_cobertura = (nuevo_matched / total) * 100

    data["_README"]["stats"]["matched"] = nuevo_matched
    data["_README"]["stats"]["no_matcheable"] = total - nuevo_matched
    data["_README"]["stats"]["cobertura"] = f"{nueva_cobertura:.1f}%"


def guardar_mapping(data: Dict[str, Any]) -> None:
    """Guarda el archivo JSON actualizado."""
    # Ordenar las claves del mapping alfabéticamente
    data["mapping"] = dict(sorted(data["mapping"].items()))

    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    print("=" * 80)
    print("AGREGAR MAPEOS AUTOMÁTICOS DE ALTA CONFIANZA")
    print("=" * 80)
    print()

    # Cargar JSON actual
    print("Cargando archivo de mapeos actual...")
    data = cargar_mapping_actual()
    print(f"  ✓ Mapeos existentes: {data['_README']['stats']['matched']}")
    print(f"  ✓ Cobertura actual: {data['_README']['stats']['cobertura']}")
    print()

    # Extraer mapeos del reporte
    print("Extrayendo mapeos del reporte de análisis...")
    mapeos = extraer_mapeos_del_reporte()
    print(f"  ✓ Mapeos de alta confianza encontrados: {len(mapeos)}")
    print()

    if not mapeos:
        print("No hay mapeos para agregar.")
        return

    # Agregar mapeos
    print("Agregando mapeos al JSON...")
    print()
    nuevos, existentes = agregar_mapeos(data, mapeos)

    if nuevos > 0:
        # Actualizar stats
        actualizar_stats(data, nuevos)
        guardar_mapping(data)

        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  • Mapeos en reporte: {len(mapeos)}")
        print(f"  • Mapeos nuevos agregados: {nuevos}")
        print(f"  • Mapeos que ya existían: {existentes}")
        print(f"  • Total mapeos ahora: {data['_README']['stats']['matched']}")
        print(f"  • Nueva cobertura: {data['_README']['stats']['cobertura']}")
        print(f"\n✓ Archivo actualizado: {mapping_file}\n")
    else:
        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  • Mapeos en reporte: {len(mapeos)}")
        print(f"  • Mapeos que ya existían: {existentes}")
        print("\nTodos los mapeos ya estaban en el archivo.\n")


if __name__ == "__main__":
    main()
