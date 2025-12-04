"""
Script para vaciar todas las tablas de la base de datos (TRUNCATE).

Mantiene la estructura de las tablas pero elimina todos los datos.
Útil para limpiar la base de datos sin tener que recrearla completamente.
"""

import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def truncate_all_tables():
    """Trunca todas las tablas de la base de datos."""

    # Obtener la URL de la base de datos
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://epidemiologia_user:epidemiologia_password@localhost:5433/epidemiologia_db",
    )

    print("🔗 Conectando a base de datos...")

    # Crear engine asíncrono
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            print("📋 Obteniendo lista de tablas...")

            # Obtener todas las tablas del esquema público
            result = await session.execute(
                text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
            )
            tables = [row[0] for row in result.fetchall()]

            if not tables:
                print("ℹ️  No se encontraron tablas para truncar")
                return

            print(f"🗑️  Truncando {len(tables)} tablas...")

            # Deshabilitar triggers y constraints temporalmente
            await session.execute(text("SET session_replication_role = 'replica';"))

            # Truncar cada tabla
            for table in tables:
                # Ignorar la tabla de migraciones de Alembic
                if table == 'alembic_version':
                    print(f"   ⏭️  Saltando {table} (tabla de migraciones)")
                    continue

                try:
                    await session.execute(
                        text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    )
                    print(f"   ✅ {table}")
                except Exception as e:
                    print(f"   ⚠️  Error en {table}: {e}")

            # Rehabilitar triggers y constraints
            await session.execute(text("SET session_replication_role = 'origin';"))

            # Commit de los cambios
            await session.commit()

            print(f"\n✨ Truncado completo: {len(tables) - 1} tablas vaciadas")
            print("ℹ️  La estructura de las tablas se mantiene intacta")

    except Exception as e:
        print(f"❌ Error durante el truncate: {e}")
        raise
    finally:
        await engine.dispose()


def main():
    """Función principal."""
    try:
        asyncio.run(truncate_all_tables())
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
