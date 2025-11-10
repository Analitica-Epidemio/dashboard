#!/usr/bin/env python3
"""
Agrega manualmente 3 hospitales importantes al archivo de mapping.

Estos hospitales tienen alta confianza (similitud nombre ≥85% o 100%) pero no
fueron agregados automáticamente porque:
- Algunos tienen score <85 debido a falta de datos de localidad en IGN
- Uno cumple criterios pero su código SNVS quizás no estaba en los CSVs procesados
"""

import json
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent.parent
mapping_file = backend_dir / "app/scripts/seeds/data/establecimientos_mapping_final.json"

# Mappings manuales de alta confianza
MAPPINGS_MANUALES = {
    "13845": {  # HOSPITAL REGIONAL COMODORO RIVADAVIA - 2,439 eventos
        "nombre_snvs": "HOSPITAL REGIONAL COMODORO RIVADAVIA",
        "codigo_refes": "11260",
        "nombre_ign": "Hospital Regional Comodoro Rivadavia",
        "score": 60.0,  # Bajo score por falta de localidad en IGN
        "similitud_nombre": 100.0,  # ✓ Nombre perfecto
        "razon": "similitud nombre: 100.0% (MATCH PERFECTO por nombre, score bajo por falta de datos de localidad en IGN)",
        "confidence": "HIGH",
        "localidad_snvs": "Comodoro Rivadavia",
        "localidad_ign": "N/A",
        "provincia_snvs": "Chubut",
        "provincia_ign": "Chubut",
        "agregado_manual": True,
        "eventos": 2439
    },
    "13680": {  # HOSPITAL ZONAL TRELEW CENTRO MATERNO INFANTIL - 14 eventos
        "nombre_snvs": "HOSPITAL ZONAL TRELEW CENTRO MATERNO INFANTIL",
        "codigo_refes": "16307",
        "nombre_ign": "Centro Materno Infantil",
        "score": 91.0,  # ✓ Score alto
        "similitud_nombre": 85.0,  # ✓ Similitud alta
        "razon": "similitud nombre: 85.0% + provincia: Chubut + mismo depto: Rawson + misma localidad",
        "confidence": "HIGH",
        "localidad_snvs": "Trelew",
        "localidad_ign": "Trelew",
        "provincia_snvs": "Chubut",
        "provincia_ign": "Chubut",
        "agregado_manual": True,
        "eventos": 14,
        "nota": "Cumplía criterios automáticos (score ≥85, similitud ≥80%) pero no se agregó. Posiblemente el código SNVS no estaba en las columnas procesadas de los CSVs."
    },
    "13584": {  # HOSPITAL RURAL LAGO PUELO - 14 eventos
        "nombre_snvs": "HOSPITAL RURAL LAGO PUELO",
        "codigo_refes": "8945",
        "nombre_ign": "Hospital Rural Lago Puelo",
        "score": 60.0,  # Bajo score por falta de localidad en IGN
        "similitud_nombre": 100.0,  # ✓ Nombre perfecto
        "razon": "similitud nombre: 100.0% (MATCH PERFECTO por nombre, score bajo por falta de datos de localidad en IGN)",
        "confidence": "HIGH",
        "localidad_snvs": "Lago Puelo",
        "localidad_ign": "N/A",
        "provincia_snvs": "Chubut",
        "provincia_ign": "Chubut",
        "agregado_manual": True,
        "eventos": 14
    }
}


def cargar_mapping_actual():
    """Carga el archivo JSON actual."""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def agregar_mappings(data):
    """Agrega los mappings manuales al JSON."""
    count_nuevos = 0
    count_actualizados = 0

    for snvs_code, mapping_data in MAPPINGS_MANUALES.items():
        if snvs_code in data["mapping"]:
            print(f"  ⚠️  Ya existe: {mapping_data['nombre_snvs']} (actualizando...)")
            count_actualizados += 1
        else:
            print(f"  ✓ Agregando: {mapping_data['nombre_snvs']}")
            print(f"    → {mapping_data['nombre_ign']} (REFES: {mapping_data['codigo_refes']})")
            print(f"    → Similitud: {mapping_data['similitud_nombre']}% | Eventos: {mapping_data.get('eventos', 'N/A')}")
            count_nuevos += 1

        data["mapping"][snvs_code] = mapping_data

    return count_nuevos, count_actualizados


def actualizar_stats(data, nuevos_mapeos):
    """Actualiza las estadísticas si existen."""
    if nuevos_mapeos == 0:
        return

    # Verificar si existe sección de stats
    if "_README" not in data or "stats" not in data.get("_README", {}):
        return

    matched_actual = data["_README"]["stats"]["matched"]
    total = data["_README"]["stats"]["total_csv_establecimientos"]

    nuevo_matched = matched_actual + nuevos_mapeos
    nueva_cobertura = (nuevo_matched / total) * 100

    data["_README"]["stats"]["matched"] = nuevo_matched
    data["_README"]["stats"]["no_matcheable"] = total - nuevo_matched
    data["_README"]["stats"]["cobertura"] = f"{nueva_cobertura:.1f}%"


def guardar_mapping(data):
    """Guarda el archivo JSON actualizado."""
    # Ordenar las claves del mapping alfabéticamente
    data["mapping"] = dict(sorted(data["mapping"].items()))

    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("="*80)
    print("AGREGAR MAPPINGS MANUALES - HOSPITALES IMPORTANTES")
    print("="*80)
    print()

    # Cargar JSON actual
    print("Cargando archivo de mapeos actual...")
    data = cargar_mapping_actual()

    # Contar mapeos existentes
    mapeos_existentes = len(data.get("mapping", {}))
    print(f"  ✓ Mapeos existentes: {mapeos_existentes}")
    print()

    # Agregar mappings
    print(f"Agregando {len(MAPPINGS_MANUALES)} mappings de hospitales importantes...")
    print()
    nuevos, actualizados = agregar_mappings(data)

    if nuevos > 0:
        # Actualizar stats
        actualizar_stats(data, nuevos)
        guardar_mapping(data)

        print()
        print("="*80)
        print("RESUMEN")
        print("="*80)
        print(f"  • Mapeos manuales procesados: {len(MAPPINGS_MANUALES)}")
        print(f"  • Nuevos mapeos agregados: {nuevos}")
        print(f"  • Mapeos actualizados: {actualizados}")
        print(f"  • Total mapeos ahora: {len(data['mapping'])}")
        print()
        print(f"  • Eventos cubiertos por estos 3 hospitales: 2,467")
        print(f"    - COMODORO RIVADAVIA: 2,439 eventos")
        print(f"    - CENTRO MATERNO INFANTIL: 14 eventos")
        print(f"    - LAGO PUELO: 14 eventos")
        print()
        print(f"✓ Archivo actualizado: {mapping_file}")
        print()
    else:
        print()
        print("="*80)
        print("RESUMEN")
        print("="*80)
        print(f"  • Mapeos manuales procesados: {len(MAPPINGS_MANUALES)}")
        print(f"  • Mapeos actualizados: {actualizados}")
        print()
        print("Todos los mapeos ya estaban en el archivo.")
        print()


if __name__ == "__main__":
    main()
