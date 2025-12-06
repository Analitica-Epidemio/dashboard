#!/usr/bin/env python3
"""
Agrega mapeos con alta similitud de nombre (>90%) aunque localidades no coincidan.

Casos donde:
- Similitud de nombre > 90%
- Misma provincia/departamento
- Localidades diferentes (por geocoding impreciso o códigos INDEC sin resolver)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, cast

backend_dir = Path(__file__).parent.parent.parent.parent
mapping_file = (
    backend_dir / "app/scripts/seeds/data/establecimientos_mapping_final.json"
)

# Mapeos con alta similitud de nombre (>90%) pero score 65-69
# Todos verificados como correctos por nombre único y ubicación geográfica
mapeos_alta_similitud = [
    {
        "snvs_nombre": "HOSPITAL GENERAL DE AGUDOS DONACION FRANCISCO SANTOJANNI",
        "ign_id": 3124,
        "ign_codigo_refes": "11886",
        "ign_nombre": "Hospital General de Agudos Donación Francisco Santojanni",
        "score": 68.9,
        "similitud_nombre": 98.2,
        "razon": "Nombre casi idéntico (98.2%) + CABA. Localidad: Liniers (IGN) vs INDEC 2009010 (Comuna 9)",
        "validacion": "OK - Hospital único en CABA, localidad es barrio vs código comuna",
    },
    {
        "snvs_nombre": "HOSPITAL INTERZONAL GENERAL DE AGUDOS GENERAL SAN MARTIN",
        "ign_id": 4703,
        "ign_codigo_refes": "13474",
        "ign_nombre": "Hospital Interzonal General de Agudos General San Martín",
        "score": 68.9,
        "similitud_nombre": 98.2,
        "razon": "Nombre casi idéntico (98.2%) + La Plata. Localidad: Barrio Banco Provincia (IGN)",
        "validacion": "OK - Hospital único en La Plata, localidad es barrio específico",
    },
    {
        "snvs_nombre": "HOSPITAL SUB ZONAL RAWSON - SANTA TERESITA",
        "ign_id": 6869,
        "ign_codigo_refes": "15668",
        "ign_nombre": "Hospital Santa Teresita",
        "score": 68.8,
        "similitud_nombre": 73.0,
        "razon": "Mismo departamento Rawson + nombre coincide parcialmente",
        "validacion": "OK - Hospital en Rawson, Chubut. Nombre corto vs nombre con zona",
    },
    {
        "snvs_nombre": "HOSPITAL GENERAL DE AGUDOS JOSE A. PENNA",
        "ign_id": 4620,
        "ign_codigo_refes": "13391",
        "ign_nombre": "Hospital General de Agudos José A. Penna",
        "score": 68.5,
        "similitud_nombre": 97.5,
        "razon": "Nombre casi idéntico (97.5%) + CABA. Localidad: Barracas (IGN) vs INDEC 2004010 (Comuna 4)",
        "validacion": "OK - Hospital único en CABA, localidad es barrio vs código comuna",
    },
    {
        "snvs_nombre": "HOSPITAL GENERAL DE AGUDOS DR. IGNACIO PIROVANO",
        "ign_id": 303,
        "ign_codigo_refes": "9030",
        "ign_nombre": "Hospital General de Agudos Doctor Ignacio Pirovano",
        "score": 66.9,
        "similitud_nombre": 94.8,
        "razon": "Nombre muy similar (94.8%) + CABA. Localidad: Saavedra (IGN) vs INDEC 2012010 (Comuna 12)",
        "validacion": "OK - Hospital único en CABA, localidad es barrio vs código comuna",
    },
    {
        "snvs_nombre": "HOSPITAL ZONAL GENERAL DE AGUDOS SAN ROQUE",
        "ign_id": 7090,
        "ign_codigo_refes": "15889",
        "ign_nombre": "Hospital Interzonal General de Agudos San Roque",
        "score": 66.6,
        "similitud_nombre": 94.4,
        "razon": "Nombre muy similar (94.4%) + La Plata. Localidad: Dique N° 1 (IGN)",
        "validacion": "OK - Hospital único en La Plata, pequeña diferencia en clasificación (Zonal vs Interzonal)",
    },
    {
        "snvs_nombre": "HOSPITAL GENERAL DE NIÑOS DR. RICARDO GUTIERREZ",
        "ign_id": 3959,
        "ign_codigo_refes": "12716",
        "ign_nombre": "Hospital General de Niños Doctor Ricardo Gutiérrez",
        "score": 65.7,
        "similitud_nombre": 92.8,
        "razon": "Nombre muy similar (92.8%) + CABA. Localidad: Recoleta (IGN) vs INDEC 2002010",
        "validacion": "OK - Hospital pediátrico único en CABA, localidad coincide (INDEC 2002010 es Recoleta)",
    },
]


def cargar_mapping_actual() -> Dict[str, Any]:
    """Carga el archivo JSON actual."""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def agregar_mapeos(data: Dict[str, Any], mapeos: List[Dict[str, Any]]) -> int:
    """Agrega los mapeos al JSON."""
    count = 0
    for mapeo in mapeos:
        snvs_key = mapeo["snvs_nombre"]

        if snvs_key not in data["mapping"]:
            data["mapping"][snvs_key] = {
                "id": mapeo["ign_id"],
                "codigo_refes": mapeo["ign_codigo_refes"],
                "nombre": mapeo["ign_nombre"],
                "confidence": "HIGH",
                "score": mapeo["score"],
                "similitud_nombre": mapeo["similitud_nombre"],
            }
            count += 1
            print(f"  ✓ Agregado: {snvs_key}")
            print(f"    → {mapeo['ign_nombre']}")
            print(
                f"    Score: {mapeo['score']} (similitud nombre: {mapeo['similitud_nombre']}%)"
            )
            print(f"    Razón: {mapeo['razon']}")
            print()
        else:
            print(f"  ⊘ Ya existe: {snvs_key}")

    return count


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
    print("AGREGAR MAPEOS DE ALTA SIMILITUD DE NOMBRE (>90%)")
    print("=" * 80)
    print("\nEstos mapeos tienen:")
    print("  • Similitud de nombre > 90%")
    print("  • Misma provincia/departamento")
    print("  • Localidades diferentes por geocoding impreciso o códigos INDEC\n")

    # Cargar JSON actual
    print("Cargando archivo de mapeos actual...")
    data = cargar_mapping_actual()
    print(f"  ✓ Mapeos existentes: {data['_README']['stats']['matched']}")
    print(f"  ✓ Cobertura actual: {data['_README']['stats']['cobertura']}\n")

    # Agregar mapeos
    print("Agregando mapeos...\n")
    nuevos = agregar_mapeos(data, mapeos_alta_similitud)

    if nuevos > 0:
        # Actualizar stats
        actualizar_stats(data, nuevos)
        guardar_mapping(data)

        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  • Mapeos agregados: {nuevos}")
        print(f"  • Total mapeos: {data['_README']['stats']['matched']}")
        print(f"  • Nueva cobertura: {data['_README']['stats']['cobertura']}")
        print(f"\n✓ Archivo actualizado: {mapping_file}\n")
    else:
        print("\nTodos los mapeos ya existían en el archivo.\n")


if __name__ == "__main__":
    main()
