"""
Script para exportar mapeo de departamentos con sus IDs INDEC.
"""

import asyncio
import json
import unicodedata
from pathlib import Path

from sqlmodel import Session, select

from app.core.database import engine
from app.domains.territorio.geografia_models import Departamento, Provincia


def normalize_name(name: str) -> str:
    """Normaliza un nombre removiendo tildes y convirtiendo a mayúsculas."""
    name = name.upper().strip()
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    return name


async def export_departamentos():
    """Exporta mapeo de departamentos con IDs."""

    with Session(engine) as session:
        # Obtener todos los departamentos con provincia
        statement = select(Departamento, Provincia).join(
            Provincia,
            Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        results = session.exec(statement).all()

        departamentos_map = {}

        for dept, prov in results:
            key = f"{normalize_name(prov.nombre)}_{normalize_name(dept.nombre)}"
            departamentos_map[key] = {
                "provincia": prov.nombre,
                "departamento": dept.nombre,
                "id_provincia_indec": dept.id_provincia_indec,
                "id_departamento_indec": dept.id_departamento_indec,
            }

        # Guardar como JSON
        output_path = Path(__file__).parent.parent.parent.parent / "frontend" / "src" / "app" / "dashboard" / "mapa" / "_components" / "departamentos_ids.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(departamentos_map, f, ensure_ascii=False, indent=2)

        print(f"✅ Exportados {len(departamentos_map)} departamentos")
        print(f"📄 Guardado en: {output_path}")

        # Mostrar algunos ejemplos
        print("\nEjemplos:")
        for i, (key, value) in enumerate(list(departamentos_map.items())[:5]):
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(export_departamentos())
