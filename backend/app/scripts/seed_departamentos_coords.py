"""
Seed para actualizar las coordenadas de departamentos desde el JSON extraído del TopoJSON.
"""

import asyncio
import json
from pathlib import Path

from sqlmodel import Session, select

from app.core.database import engine
from app.domains.territorio.geografia_models import Departamento


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


async def seed_departamentos_coords():
    """Actualiza las coordenadas de departamentos desde el JSON."""

    # Leer JSON con centroides
    json_path = Path(__file__).parent / "data" / "departamentos_centroids.json"

    if not json_path.exists():
        print(f"ERROR: No se encontró {json_path}")
        print("Ejecuta primero: python app/scripts/extract_departamento_centroids.py")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        centroids_data = json.load(f)

    print(f"Cargados {len(centroids_data)} centroides desde JSON")

    with Session(engine) as session:
        # Crear un diccionario para búsqueda rápida
        # Clave: (id_provincia_indec, nombre_normalizado)
        centroids_dict = {}
        for item in centroids_data:
            key = (item['id_provincia_indec'], normalize_name(item['departamento']))
            centroids_dict[key] = (item['latitud'], item['longitud'])

        print(f"Índice creado con {len(centroids_dict)} entradas")

        # Obtener todos los departamentos de la BD
        statement = select(Departamento)
        departamentos = session.exec(statement).all()

        print(f"\nActualizando {len(departamentos)} departamentos de la BD...")

        updated = 0
        not_found = []

        for dept in departamentos:
            # Buscar centroide
            key = (dept.id_provincia_indec, normalize_name(dept.nombre))

            if key in centroids_dict:
                lat, lng = centroids_dict[key]
                dept.latitud = lat
                dept.longitud = lng
                updated += 1
            else:
                not_found.append(f"{dept.nombre} (provincia {dept.id_provincia_indec})")

        session.commit()

        print(f"\n✅ Actualizados: {updated} departamentos")

        if not_found:
            print(f"\n⚠️  No encontrados en TopoJSON ({len(not_found)}):")
            for name in not_found[:10]:  # Mostrar solo los primeros 10
                print(f"  - {name}")
            if len(not_found) > 10:
                print(f"  ... y {len(not_found) - 10} más")


if __name__ == "__main__":
    asyncio.run(seed_departamentos_coords())
