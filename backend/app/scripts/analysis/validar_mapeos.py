#!/usr/bin/env python3
"""
Script para validar y agregar mapeos de alta confianza al archivo JSON.

Procesa:
1. Mapeos con score >90: se agregan automáticamente (alta confianza)
2. Mapeos con score =85: se validan manualmente y se agregan si son correctos
"""

import json
from pathlib import Path
from typing import Dict, List

# Rutas
backend_dir = Path(__file__).parent.parent.parent.parent
mapping_file = backend_dir / "app/scripts/seeds/data/establecimientos_mapping_final.json"

# Mapeos de ALTA CONFIANZA (score >90) - ACEPTAR AUTOMÁTICAMENTE
mapeos_alta_confianza = [
    {
        "snvs_nombre": "HOSPITAL DEL NIÑO JESUS",
        "ign_id": 5349,
        "ign_codigo_refes": "14129",
        "ign_nombre": "Hospital del Niño Jesús",
        "score": 97.4,
        "razon": "similitud nombre: 95.7% + provincia: Tucumán + mismo depto: Capital + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL CENTRO DE SALUD ZENON J. SANTILLAN",
        "ign_id": 5338,
        "ign_codigo_refes": "14118",
        "ign_nombre": "Hospital Centro de Salud Zenón J. Santillán",
        "score": 97.2,
        "razon": "similitud nombre: 95.3% + provincia: Tucumán + mismo depto: Capital + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL PUBLICO DE GESTION DESCENTRALIZADA DR. GUILLERMO RAWSON",
        "ign_id": 8179,
        "ign_codigo_refes": "16982",
        "ign_nombre": "Hospital Público de Gestión Descentralizada Doctor Guillermo Rawson",
        "score": 95.9,
        "razon": "similitud nombre: 93.1% + provincia: San Juan + mismo depto: Capital + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL TEODORO J. SCHESTAKOW.-",
        "ign_id": 6203,
        "ign_codigo_refes": "15002",
        "ign_nombre": "Hospital Teodoro Schestakow",
        "score": 95.9,
        "razon": "similitud nombre: 93.1% + provincia: Mendoza + mismo depto: San Rafael + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL MUNICIPAL DE AGUDOS DR. LEONIDAS LUCERO",
        "ign_id": 645,
        "ign_codigo_refes": "9394",
        "ign_nombre": "Hospital Municipal de Agudos Doctor Leónidas Lucero",
        "score": 95.8,
        "razon": "similitud nombre: 92.9% + provincia: Buenos Aires + mismo depto: Bahía Blanca + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL DE CLINICAS PRESIDENTE DR. NICOLAS AVELLANEDA",
        "ign_id": 6398,
        "ign_codigo_refes": "15196",
        "ign_nombre": "Hospital de Clínicas Presidente Nicolás Avellaneda",
        "score": 95.4,
        "razon": "similitud nombre: 92.3% + provincia: Tucumán + mismo depto: Capital + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL INTERZONAL GENERAL AGUDOS DR. LUIS A. GUEMES",
        "ign_id": 7085,
        "ign_codigo_refes": "15884",
        "ign_nombre": "Hospital Interzonal General de Agudos Doctor Luis A. Güemes",
        "score": 94.6,
        "razon": "similitud nombre: 91.1% + provincia: Buenos Aires + mismo depto: Morón + misma localidad"
    },
    {
        "snvs_nombre": "HOSPITAL INTERZONAL GENERAL DE AGUDOS DR. JOSE PENNA",
        "ign_id": 4720,
        "ign_codigo_refes": "13492",
        "ign_nombre": "Hospital Interzonal de Agudos Doctor José Penna",
        "score": 90.9,
        "razon": "similitud nombre: 84.8% + provincia: Buenos Aires + mismo depto: Bahía Blanca + misma localidad"
    },
]

# Mapeos con score=85 que REQUIEREN VALIDACIÓN MANUAL
# Estos tienen nombre 100% igual pero localidades diferentes
mapeos_validacion_manual = [
    # ===== VALIDADOS OK (se agregarán) =====
    {
        "snvs_nombre": "HOSPITAL RURAL DIADEMA ARGENTINA",
        "ign_id": 5442,
        "ign_codigo_refes": "14234",
        "ign_nombre": "Hospital Rural Diadema Argentina",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Escalante",
        "localidad_snvs": "Diadema Argentina",
        "localidad_ign": "Kilómetro 3 - General Mosconi",
        "validacion": "OK: Km 3 - General Mosconi es una zona/barrio de Diadema Argentina"
    },
    {
        "snvs_nombre": "HOSPITAL SEÑOR DEL MILAGRO",
        "ign_id": 5217,
        "ign_codigo_refes": "13995",
        "ign_nombre": "Hospital Señor del Milagro",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Salta + mismo depto: Capital",
        "localidad_snvs": "Salta",
        "localidad_ign": "Country Club La Almudena",
        "validacion": "OK: Country Club La Almudena es un barrio de Salta capital. Hospital está en Av. Sarmiento 557"
    },
    {
        "snvs_nombre": "HOSPITAL MUNICIPAL JUAN CIRILO SANGUINETTI",
        "ign_id": 7100,
        "ign_codigo_refes": "15899",
        "ign_nombre": "Hospital Municipal Juan Cirilo Sanguinetti",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Buenos Aires + mismo depto: Pilar",
        "localidad_snvs": "Pilar",
        "localidad_ign": "Del Viso",
        "validacion": "OK: Del Viso es una localidad dentro del partido de Pilar. Hospital en Víctor Vergani 860"
    },

    # ===== RECHAZADOS (ubicaciones incorrectas en IGN) =====
    {
        "snvs_nombre": "HOSPITAL ZONAL ESQUEL",
        "ign_id": 220,
        "ign_codigo_refes": "8946",
        "ign_nombre": "Hospital Zonal Esquel",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Futaleufú",
        "localidad_snvs": "Esquel",
        "localidad_ign": "Aldea Escolar (Los Rápidos)",
        "validacion": "RECHAZADO: Hospital está en Esquel (25 de Mayo 150). Aldea Escolar está a 9km de Trevelin, no de Esquel. IGN tiene ubicación incorrecta"
    },
    {
        "snvs_nombre": "HOSPITAL RURAL CORCOVADO",
        "ign_id": 2504,
        "ign_codigo_refes": "11261",
        "ign_nombre": "Hospital Rural Corcovado",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Futaleufú",
        "localidad_snvs": "Corcovado",
        "localidad_ign": "Aldea Escolar (Los Rápidos)",
        "validacion": "RECHAZADO: Corcovado es un pueblo diferente de Aldea Escolar. IGN tiene ubicación incorrecta"
    },
    {
        "snvs_nombre": "HOSPITAL RURAL TECKA",
        "ign_id": 2506,
        "ign_codigo_refes": "11263",
        "ign_nombre": "Hospital Rural Tecka",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Chubut + mismo depto: Languiñeo",
        "localidad_snvs": "Tecka",
        "localidad_ign": "Aldea Epulef",
        "validacion": "RECHAZADO: Hospital está en Tecka. Aldea Epulef está a 92 km de distancia y solo tiene Puesto Sanitario, no hospital. IGN ubicación muy incorrecta"
    },
    {
        "snvs_nombre": "HOSPITAL MELCHORA F. DE CORNEJO",
        "ign_id": 5490,
        "ign_codigo_refes": "14283",
        "ign_nombre": "Hospital Melchora F. de Cornejo",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Salta + mismo depto: Rosario de la Frontera",
        "localidad_snvs": "Rosario de la Frontera",
        "localidad_ign": "Copo Quile",
        "validacion": "RECHAZADO: Hospital está en Rosario de la Frontera (Avellaneda 350). Copo Quile es una aldea rural separada. IGN tiene ubicación incorrecta"
    },
    {
        "snvs_nombre": "HOSPITAL ISAAC WAISMAN",
        "ign_id": 3649,
        "ign_codigo_refes": "12407",
        "ign_nombre": "Hospital Isaac Waisman",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Chaco + mismo depto: 12 de Octubre",
        "localidad_snvs": "General Pinedo",
        "localidad_ign": "Gancedo",
        "validacion": "RECHAZADO: Hospital está en General Pinedo (Calle 23 y 8). Gancedo es otro pueblo conectado por ruta. IGN tiene ubicación incorrecta"
    },

    # ===== REQUIEREN MÁS INVESTIGACIÓN =====
    {
        "snvs_nombre": "ESTABLECIMIENTO ASISTENCIAL GOBERNADOR CENTENO",
        "ign_id": 3803,
        "ign_codigo_refes": "12560",
        "ign_nombre": "Establecimiento Asistencial Gobernador Centeno",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: La Pampa + mismo depto: Maracó",
        "localidad_snvs": "General Pico",
        "localidad_ign": "Dorila",
        "validacion": "INVESTIGAR: Dorila está a 13.5 km de General Pico (19 min por ruta). Requiere confirmar ubicación real del establecimiento"
    },
    {
        "snvs_nombre": "HOSPITAL REGIONAL VILLA DOLORES",
        "ign_id": 4536,
        "ign_codigo_refes": "13308",
        "ign_nombre": "Hospital Regional Villa Dolores",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Córdoba + mismo depto: San Javier",
        "localidad_snvs": "Villa Dolores",
        "localidad_ign": "Alto Resbaloso - El Barrial",
        "validacion": "INVESTIGAR: Hospital está en Av. Belgrano 1800, Villa Dolores. No se encontró info sobre Alto Resbaloso. Requiere verificación"
    },
    {
        "snvs_nombre": "HOSPITAL SAN JUAN BAUTISTA",
        "ign_id": 567,
        "ign_codigo_refes": "9316",
        "ign_nombre": "Hospital San Juan Bautista",
        "score": 85.0,
        "razon": "similitud nombre: 100.0% + provincia: Corrientes + mismo depto: Santo Tomé",
        "localidad_snvs": "Santo Tomé",
        "localidad_ign": "José Rafael Gómez",
        "validacion": "INVESTIGAR: Hospital está en Beltrán 451, Santo Tomé. José Rafael Gómez no aparece en búsquedas. Requiere verificación"
    },
]


def cargar_mapping_actual() -> Dict:
    """Carga el archivo JSON actual."""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def agregar_mapeos_alta_confianza(data: Dict) -> int:
    """
    Agrega mapeos de alta confianza (score >90) automáticamente.
    Retorna el número de mapeos agregados.
    """
    count = 0
    for mapeo in mapeos_alta_confianza:
        snvs_key = mapeo["snvs_nombre"]

        # Solo agregar si no existe ya
        if snvs_key not in data["mapping"]:
            data["mapping"][snvs_key] = {
                "id": mapeo["ign_id"],
                "codigo_refes": mapeo["ign_codigo_refes"],
                "nombre": mapeo["ign_nombre"],
                "confidence": "HIGH",
                "score": mapeo["score"]
            }
            count += 1
            print(f"  ✓ Agregado: {snvs_key} → {mapeo['ign_nombre']} (score: {mapeo['score']})")
        else:
            print(f"  ⊘ Ya existe: {snvs_key}")

    return count


def revisar_mapeos_validacion_manual(data: Dict) -> Dict:
    """
    Revisa los mapeos que requieren validación manual.
    Retorna estadísticas de validación.
    """
    print("\n" + "="*80)
    print("MAPEOS QUE REQUIEREN VALIDACIÓN MANUAL (score=85)")
    print("="*80 + "\n")

    stats = {
        "total": len(mapeos_validacion_manual),
        "validados_ok": [],
        "requieren_investigacion": []
    }

    for i, mapeo in enumerate(mapeos_validacion_manual, 1):
        print(f"{i}. {mapeo['snvs_nombre']}")
        print(f"   SNVS localidad: {mapeo['localidad_snvs']}")
        print(f"   IGN localidad: {mapeo['localidad_ign']}")
        print(f"   → {mapeo['validacion']}")

        if "OK:" in mapeo['validacion']:
            stats['validados_ok'].append(mapeo)
            print("   ✓ VALIDADO - Se agregará al mapping")
        else:
            stats['requieren_investigacion'].append(mapeo)
            print("   ⚠ REQUIERE INVESTIGACIÓN - No se agregará aún")

        print()

    return stats


def agregar_mapeos_validados(data: Dict, mapeos_validados: List[Dict]) -> int:
    """
    Agrega los mapeos que fueron validados como OK.
    Retorna el número de mapeos agregados.
    """
    count = 0
    for mapeo in mapeos_validados:
        snvs_key = mapeo["snvs_nombre"]

        if snvs_key not in data["mapping"]:
            data["mapping"][snvs_key] = {
                "id": mapeo["ign_id"],
                "codigo_refes": mapeo["ign_codigo_refes"],
                "nombre": mapeo["ign_nombre"],
                "confidence": "MANUAL",
                "score": mapeo["score"]
            }
            count += 1
            print(f"  ✓ Agregado (validado): {snvs_key} → {mapeo['ign_nombre']}")

    return count


def actualizar_stats(data: Dict, nuevos_mapeos: int):
    """Actualiza las estadísticas en el README."""
    matched_actual = data["_README"]["stats"]["matched"]
    total = data["_README"]["stats"]["total_csv_establecimientos"]

    nuevo_matched = matched_actual + nuevos_mapeos
    nueva_cobertura = (nuevo_matched / total) * 100

    data["_README"]["stats"]["matched"] = nuevo_matched
    data["_README"]["stats"]["no_matcheable"] = total - nuevo_matched
    data["_README"]["stats"]["cobertura"] = f"{nueva_cobertura:.1f}%"


def guardar_mapping(data: Dict):
    """Guarda el archivo JSON actualizado."""
    # Ordenar las claves del mapping alfabéticamente
    data["mapping"] = dict(sorted(data["mapping"].items()))

    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("="*80)
    print("VALIDACIÓN Y ACTUALIZACIÓN DE MAPEOS")
    print("="*80 + "\n")

    # Cargar JSON actual
    print("Cargando archivo de mapeos actual...")
    data = cargar_mapping_actual()
    print(f"  ✓ Cargado: {data['_README']['stats']['matched']} mapeos existentes\n")

    # Paso 1: Agregar mapeos de alta confianza (score >90)
    print("="*80)
    print("PASO 1: AGREGAR MAPEOS DE ALTA CONFIANZA (score >90)")
    print("="*80 + "\n")

    nuevos_alta = agregar_mapeos_alta_confianza(data)
    print(f"\n✓ Agregados {nuevos_alta} mapeos de alta confianza\n")

    # Paso 2: Revisar mapeos que requieren validación manual
    stats_validacion = revisar_mapeos_validacion_manual(data)

    # Agregar solo los validados como OK
    print("="*80)
    print("PASO 2: AGREGAR MAPEOS VALIDADOS MANUALMENTE")
    print("="*80 + "\n")

    nuevos_validados = agregar_mapeos_validados(data, stats_validacion['validados_ok'])
    print(f"\n✓ Agregados {nuevos_validados} mapeos validados\n")

    # Actualizar stats
    total_nuevos = nuevos_alta + nuevos_validados
    if total_nuevos > 0:
        actualizar_stats(data, total_nuevos)
        guardar_mapping(data)
        print("="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"  • Mapeos de alta confianza agregados: {nuevos_alta}")
        print(f"  • Mapeos validados agregados: {nuevos_validados}")
        print(f"  • Total nuevos mapeos: {total_nuevos}")
        print(f"  • Mapeos que requieren más investigación: {len(stats_validacion['requieren_investigacion'])}")
        print(f"\n  • Cobertura anterior: {data['_README']['stats']['cobertura']}")
        print(f"  • Nueva cobertura: {((data['_README']['stats']['matched']) / data['_README']['stats']['total_csv_establecimientos'] * 100):.1f}%")
        print(f"\n✓ Archivo actualizado: {mapping_file}\n")
    else:
        print("No hay nuevos mapeos para agregar (todos ya existían)\n")

    # Listar los que requieren investigación
    if stats_validacion['requieren_investigacion']:
        print("="*80)
        print("MAPEOS QUE REQUIEREN MÁS INVESTIGACIÓN")
        print("="*80)
        for mapeo in stats_validacion['requieren_investigacion']:
            print(f"  • {mapeo['snvs_nombre']}")
            print(f"    Localidades: {mapeo['localidad_snvs']} (SNVS) vs {mapeo['localidad_ign']} (IGN)")
        print()


if __name__ == "__main__":
    main()
