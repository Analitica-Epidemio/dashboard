"""
Script para extraer centroides de departamentos desde TopoJSON.

Este script lee el archivo TopoJSON con las geometrías de departamentos argentinos
y calcula el centroide de cada uno para usarlo en la visualización del mapa.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Path al TopoJSON
TOPOJSON_PATH = Path(__file__).parent.parent.parent.parent / "frontend" / "public" / "topojson" / "departamentos-argentina.topojson"


def decode_arcs(topology: dict) -> List[List[Tuple[float, float]]]:
    """Decodifica los arcs del TopoJSON a coordenadas absolutas."""
    arcs = topology["arcs"]
    transform = topology.get("transform")

    decoded_arcs = []

    for arc in arcs:
        coordinates = []
        x, y = 0, 0

        for point in arc:
            x += point[0]
            y += point[1]

            if transform:
                # Aplicar transformación
                coord_x = x * transform["scale"][0] + transform["translate"][0]
                coord_y = y * transform["scale"][1] + transform["translate"][1]
                coordinates.append((coord_x, coord_y))
            else:
                coordinates.append((x, y))

        decoded_arcs.append(coordinates)

    return decoded_arcs


def get_polygon_coordinates(geometry: dict, decoded_arcs: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
    """Obtiene las coordenadas de un polígono desde los arcs."""
    if geometry["type"] == "Polygon":
        rings = geometry["arcs"]
    elif geometry["type"] == "MultiPolygon":
        # Para MultiPolygon, usar solo el primer polígono (el más grande generalmente)
        rings = geometry["arcs"][0] if geometry["arcs"] else []
    else:
        return []

    polygon_coords = []
    for ring in rings:
        ring_coords = []
        for arc_index in ring:
            arc = decoded_arcs[abs(arc_index)]
            if arc_index < 0:
                arc = list(reversed(arc))
            ring_coords.extend(arc)
        polygon_coords.append(ring_coords)

    return polygon_coords


def calculate_centroid(coordinates: List[List[Tuple[float, float]]]) -> Tuple[float, float]:
    """Calcula el centroide de un polígono (promedio de coordenadas del anillo exterior)."""
    if not coordinates:
        return (0.0, 0.0)

    # Usar solo el anillo exterior (primer anillo)
    outer_ring = coordinates[0]

    if not outer_ring:
        return (0.0, 0.0)

    sum_x = sum(x for x, y in outer_ring)
    sum_y = sum(y for x, y in outer_ring)
    count = len(outer_ring)

    return (sum_y / count, sum_x / count)  # (lat, lng)


# Mapeo manual de nombres de provincia a ID INDEC
PROVINCIA_NAME_TO_ID = {
    "CIUDAD AUTONOMA DE BUENOS AIRES": 2,
    "BUENOS AIRES": 6,
    "CATAMARCA": 10,
    "CORDOBA": 14,
    "CORRIENTES": 18,
    "CHACO": 22,
    "CHUBUT": 26,
    "ENTRE RIOS": 30,
    "FORMOSA": 34,
    "JUJUY": 38,
    "LA PAMPA": 42,
    "LA RIOJA": 46,
    "MENDOZA": 50,
    "MISIONES": 54,
    "NEUQUEN": 58,
    "RIO NEGRO": 62,
    "SALTA": 66,
    "SAN JUAN": 70,
    "SAN LUIS": 74,
    "SANTA CRUZ": 78,
    "SANTA FE": 82,
    "SANTIAGO DEL ESTERO": 86,
    "TUCUMAN": 90,
    "TIERRA DEL FUEGO": 94,
}


def normalize_name(name: str) -> str:
    """Normaliza un nombre removiendo tildes y convirtiendo a mayúsculas."""
    import unicodedata
    name = name.upper().strip()
    # Remover tildes
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    return name


def main():
    print(f"Leyendo TopoJSON desde: {TOPOJSON_PATH}")

    if not TOPOJSON_PATH.exists():
        print(f"ERROR: No se encontró el archivo {TOPOJSON_PATH}")
        sys.exit(1)

    with open(TOPOJSON_PATH, 'r', encoding='utf-8') as f:
        topology = json.load(f)

    # Decodificar arcs
    print("Decodificando arcs...")
    decoded_arcs = decode_arcs(topology)

    # Procesar geometrías
    print("Procesando departamentos...")
    object_name = "departamentos-argentina"
    geometries = topology["objects"][object_name]["geometries"]

    departamentos_data = []

    for geometry in geometries:
        props = geometry.get("properties", {})
        departamento_nombre = props.get("departamento", "").strip()
        provincia_nombre = normalize_name(props.get("provincia", ""))

        if not departamento_nombre or not provincia_nombre:
            continue

        # Obtener ID de provincia
        id_provincia_indec = PROVINCIA_NAME_TO_ID.get(provincia_nombre)
        if not id_provincia_indec:
            print(f"ADVERTENCIA: No se encontró ID para provincia '{provincia_nombre}'")
            continue

        # Obtener coordenadas del polígono
        polygon_coords = get_polygon_coordinates(geometry, decoded_arcs)

        if not polygon_coords:
            print(f"ADVERTENCIA: No se pudieron obtener coordenadas para {departamento_nombre}, {provincia_nombre}")
            continue

        # Calcular centroide
        lat, lng = calculate_centroid(polygon_coords)

        departamentos_data.append({
            "departamento": departamento_nombre,
            "provincia": provincia_nombre,
            "id_provincia_indec": id_provincia_indec,
            "latitud": round(lat, 6),
            "longitud": round(lng, 6),
        })

    print(f"\nProcesados {len(departamentos_data)} departamentos")

    # Guardar como JSON
    output_path = Path(__file__).parent / "data" / "departamentos_centroids.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(departamentos_data, f, ensure_ascii=False, indent=2)

    print(f"Datos guardados en: {output_path}")

    # Mostrar algunos ejemplos
    print("\nEjemplos:")
    for dept in departamentos_data[:5]:
        print(f"  {dept['departamento']} ({dept['provincia']}): {dept['latitud']}, {dept['longitud']}")


if __name__ == "__main__":
    main()
