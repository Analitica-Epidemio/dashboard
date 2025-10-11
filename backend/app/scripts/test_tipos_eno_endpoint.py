#!/usr/bin/env python3
"""
Script para probar el endpoint /api/v1/tiposEno/ y verificar que devuelve los grupos correctamente.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.api.v1.tipos_eno.list import list_tipos_eno
from app.domains.autenticacion.models import User


class MockUser:
    """Mock user para testing"""
    def __init__(self):
        self.id = 1
        self.email = "test@example.com"
        self.role = "admin"


async def test_endpoint():
    """Prueba el endpoint list_tipos_eno directamente."""
    print("=" * 70)
    print("🧪 PROBANDO ENDPOINT /api/v1/tiposEno/")
    print("=" * 70)
    print()

    async with AsyncSession(async_engine) as db:
        # Llamar al endpoint directamente
        response = await list_tipos_eno(
            page=1,
            per_page=10,
            nombre=None,
            grupo_id=None,
            grupos=None,
            db=db,
            current_user=MockUser()
        )

        print(f"📊 Total de tipos: {response.meta['total']}")
        print(f"📄 Página: {response.meta['page']}/{response.meta['total_pages']}")
        print()

        # Mostrar primeros 5 tipos
        print("📋 PRIMEROS TIPOS CON SUS GRUPOS:")
        print("-" * 70)
        for tipo in response.data[:5]:
            grupos_str = ", ".join([f"{g.nombre} (ID: {g.id})" for g in tipo.grupos]) if tipo.grupos else "❌ SIN GRUPO"
            print(f"\n  Tipo: {tipo.nombre} (ID: {tipo.id})")
            print(f"  Código: {tipo.codigo or 'N/A'}")
            print(f"  Grupos: {grupos_str}")

        print()
        print("=" * 70)

        # Buscar específicamente Dengue
        print("🔍 BUSCANDO TIPO 'DENGUE' ESPECÍFICAMENTE:")
        print("-" * 70)

        response_dengue = await list_tipos_eno(
            page=1,
            per_page=100,
            nombre="dengue",
            grupo_id=None,
            grupos=None,
            db=db,
            current_user=MockUser()
        )

        if response_dengue.data:
            for tipo in response_dengue.data:
                print(f"\n  ✓ Encontrado: {tipo.nombre} (ID: {tipo.id})")
                print(f"    Código: {tipo.codigo}")
                print(f"    Total grupos: {len(tipo.grupos)}")
                if tipo.grupos:
                    for grupo in tipo.grupos:
                        print(f"      → Grupo: {grupo.nombre} (ID: {grupo.id})")
                else:
                    print("      ❌ SIN GRUPOS ASIGNADOS")
        else:
            print("  ❌ No se encontró ningún tipo con 'dengue'")

        print()
        print("=" * 70)

        # Filtrar por grupo Dengue (ID 47)
        print("🔍 FILTRANDO POR GRUPO 'DENGUE' (ID: 47):")
        print("-" * 70)

        response_grupo = await list_tipos_eno(
            page=1,
            per_page=100,
            nombre=None,
            grupo_id=47,
            grupos=None,
            db=db,
            current_user=MockUser()
        )

        print(f"\n  Total tipos en grupo Dengue: {response_grupo.meta['total']}")
        if response_grupo.data:
            for tipo in response_grupo.data:
                print(f"    → {tipo.nombre} (ID: {tipo.id})")
        else:
            print("    ❌ NO SE ENCONTRARON TIPOS EN ESTE GRUPO")

        print()
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_endpoint())
