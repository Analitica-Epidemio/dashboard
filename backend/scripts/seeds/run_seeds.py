"""
Script principal para ejecutar todos los seeds del sistema.

Uso:
    python -m app.domains.etl.services.seeds.run_seeds
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_session

from .seed_establecimientos import seed_establecimientos
from .seed_eventos import seed_eventos
from .seed_geografia import seed_geografia


async def run_all_seeds() -> None:
    """
    Ejecuta todos los seeds del sistema epidemiológico en el orden correcto.
    """
    print("🌱 Iniciando proceso de seed del sistema epidemiológico...")
    print("=" * 60)

    try:
        async for session in get_async_session():
            try:
                # 1. Geografía - Localidades (primero porque otras tablas dependen de ellas)
                await seed_geografia(session)

                # 2. Eventos epidemiológicos
                await seed_eventos(session)

                # 3. Establecimientos (depende de localidades)
                await seed_establecimientos(session)

                print("=" * 60)
                print("✅ Todos los seeds completados exitosamente!")
                print("\n📊 Resumen:")
                print("   - Localidades cargadas desde archivos Excel INDEC")
                print("   - Eventos epidemiológicos estándar creados")
                print("   - Establecimientos de salud principales creados")

            except Exception as e:
                print(f"\n❌ Error ejecutando seeds: {str(e)}")
                await session.rollback()
                raise
            finally:
                await session.close()

    except Exception as e:
        print(f"\n❌ Error conectando a la base de datos: {str(e)}")
        raise


if __name__ == "__main__":
    print("\n🚀 Sistema de Seeds - Epidemiología Moderna")
    print("   Backend de gestión epidemiológica para Chubut")
    print("\n")

    # Ejecutar seeds
    asyncio.run(run_all_seeds())
