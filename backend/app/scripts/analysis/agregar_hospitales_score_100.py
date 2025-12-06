#!/usr/bin/env python3
"""
Agrega hospitales con score 100.0 que NO fueron procesados porque sus códigos
SNVS vienen de columnas diferentes en los CSVs.

PROBLEMA: Un mismo hospital puede tener múltiples códigos SNVS en diferentes
columnas (ID_ESTAB_CLINICA, ID_ESTABLECIMIENTO_CONSULTA, etc.)

SOLUCIÓN: Agregar manualmente los hospitales con score 100.0 usando los códigos
que SÍ se encontraron en las columnas procesadas.
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple, cast

backend_dir = Path(__file__).parent.parent.parent.parent
mapping_file = (
    backend_dir / "app/scripts/seeds/data/establecimientos_mapping_final.json"
)

# Hospitales con score 100.0 del reporte de análisis
HOSPITALES_SCORE_100 = {
    "8862": {  # HOSPITAL ZONAL ESQUEL
        "nombre_snvs": "HOSPITAL ZONAL ESQUEL",
        "codigo_refes": "8946",
        "nombre_ign": "Hospital Zonal Esquel",
        "score": 100.0,
        "similitud_nombre": 100.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Futaleufú + misma localidad",
        "confidence": "HIGH",
        "localidad_snvs": "Esquel",
        "departamento_snvs": "Futaleufú",
        "provincia_snvs": "Chubut",
        "localidad_ign": "Esquel",
        "departamento_ign": "Futaleufú",
        "provincia_ign": "Chubut",
        "agregado_manual": True,
        "nota": "Código SNVS de columnas procesadas. El mismo hospital puede tener código 13571 en otras columnas.",
    },
    "8808": {  # HOSPITAL RURAL GUALJAINA
        "nombre_snvs": "HOSPITAL RURAL GUALJAINA",
        "codigo_refes": "12339",
        "nombre_ign": "Hospital Rural Gualjaina",
        "score": 100.0,
        "similitud_nombre": 100.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Cushamen + misma localidad",
        "confidence": "HIGH",
        "localidad_snvs": "Gualjaina",
        "departamento_snvs": "Cushamen",
        "provincia_snvs": "Chubut",
        "localidad_ign": "Gualjaina",
        "departamento_ign": "Cushamen",
        "provincia_ign": "Chubut",
        "agregado_manual": True,
        "nota": "Código SNVS de columnas procesadas. El mismo hospital puede tener código 13573 en otras columnas.",
    },
}


def cargar_mapping_actual() -> Dict[str, Any]:
    """Carga el archivo JSON actual."""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def agregar_mappings(data: Dict[str, Any]) -> Tuple[int, int]:
    """Agrega los mappings manuales al JSON."""
    count_nuevos = 0
    count_actualizados = 0

    for snvs_code, mapping_data in HOSPITALES_SCORE_100.items():
        if snvs_code in data["mapping"]:
            print(f"  ⚠️  Ya existe: {mapping_data['nombre_snvs']} (actualizando...)")
            count_actualizados += 1
        else:
            print(f"  ✓ Agregando: {mapping_data['nombre_snvs']}")
            print(
                f"    → IGN: {mapping_data['nombre_ign']} (REFES: {mapping_data['codigo_refes']})"
            )
            print(
                f"    → Score: {mapping_data['score']} | Similitud: {mapping_data['similitud_nombre']}%"
            )
            print(f"    → Código SNVS: {snvs_code}")
            count_nuevos += 1

        data["mapping"][snvs_code] = mapping_data

    return count_nuevos, count_actualizados


def guardar_mapping(data: Dict[str, Any]) -> None:
    """Guarda el archivo JSON actualizado."""
    # Ordenar las claves del mapping alfabéticamente
    data["mapping"] = dict(sorted(data["mapping"].items()))

    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    print("=" * 80)
    print("AGREGAR HOSPITALES CON SCORE 100.0")
    print("=" * 80)
    print()

    # Cargar JSON actual
    print("Cargando archivo de mapeos actual...")
    data = cargar_mapping_actual()

    # Contar mapeos existentes
    mapeos_existentes = len(data.get("mapping", {}))
    print(f"  ✓ Mapeos existentes: {mapeos_existentes}")
    print()

    # Agregar mappings
    print(f"Agregando {len(HOSPITALES_SCORE_100)} hospitales con score 100.0...")
    print()
    nuevos, actualizados = agregar_mappings(data)

    if nuevos > 0:
        guardar_mapping(data)

        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  • Hospitales procesados: {len(HOSPITALES_SCORE_100)}")
        print(f"  • Nuevos mapeos agregados: {nuevos}")
        print(f"  • Mapeos actualizados: {actualizados}")
        print(f"  • Total mapeos ahora: {len(data['mapping'])}")
        print()
        print("IMPORTANTE:")
        print("-" * 80)
        print("Estos hospitales tienen MÚLTIPLES códigos SNVS:")
        print(
            "  • HOSPITAL ZONAL ESQUEL: código 8862 (agregado) y 13571 (no procesado)"
        )
        print(
            "  • HOSPITAL RURAL GUALJAINA: código 8808 (agregado) y 13573 (no procesado)"
        )
        print()
        print("Para mapear los códigos 13571 y 13573, es necesario procesar")
        print("TODAS las columnas de establecimientos en los CSVs.")
        print()
        print(f"✓ Archivo actualizado: {mapping_file}")
        print()
    else:
        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  • Hospitales procesados: {len(HOSPITALES_SCORE_100)}")
        print(f"  • Mapeos actualizados: {actualizados}")
        print()
        print("Todos los mapeos ya estaban en el archivo.")
        print()


if __name__ == "__main__":
    main()
