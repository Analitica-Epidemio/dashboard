"""
Seed para crear los departamentos de Chubut con nombres reales y zonas UGD
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domains.territorio.geografia_models import Departamento, Provincia
from app.core.constants.geografia_chubut import (
    DEPARTAMENTOS_CHUBUT,
    POBLACION_DEPARTAMENTOS,
    get_zona_ugd
)


def seed_departamentos_chubut(session: Session):
    """Crea los departamentos de Chubut con nombres reales y zonas UGD"""
    try:
        # Primero asegurar que existe la provincia de Chubut
        stmt_provincia = select(Provincia).where(Provincia.id_provincia_indec == 26)
        provincia = session.execute(stmt_provincia).scalar_one_or_none()

        if not provincia:
            provincia = Provincia(
                id_provincia_indec=26,
                nombre="CHUBUT",
                poblacion=618994,  # Población estimada 2024
                superficie_km2=224686  # Superficie de Chubut en km²
            )
            session.add(provincia)
            session.commit()
            print("✅ Provincia CHUBUT creada (Código 26)")

        created_count = 0
        updated_count = 0

        for codigo_indec, nombre_real in DEPARTAMENTOS_CHUBUT.items():
            # Verificar si el departamento existe
            stmt = select(Departamento).where(
                Departamento.id_departamento_indec == codigo_indec,
                Departamento.id_provincia_indec == 26
            )
            departamento = session.execute(stmt).scalar_one_or_none()

            poblacion = POBLACION_DEPARTAMENTOS.get(codigo_indec, 0)
            zona_ugd = get_zona_ugd(codigo_indec)

            if not departamento:
                # Crear el departamento si no existe
                departamento = Departamento(
                    id_departamento_indec=codigo_indec,
                    id_provincia_indec=26,
                    nombre=nombre_real,
                    poblacion=poblacion,
                    region_sanitaria=zona_ugd
                )
                session.add(departamento)
                created_count += 1
                print(f"✅ Creado: {nombre_real} (Código {codigo_indec})")
                print(f"   - Población: {poblacion:,}")
                print(f"   - Zona UGD: {zona_ugd}")
            else:
                # Actualizar si ya existe pero con datos incorrectos
                if (departamento.nombre != nombre_real or
                    departamento.poblacion != poblacion or
                    departamento.region_sanitaria != zona_ugd):

                    departamento.nombre = nombre_real
                    departamento.poblacion = poblacion
                    departamento.region_sanitaria = zona_ugd

                    updated_count += 1
                    print(f"✅ Actualizado: {nombre_real} (Código {codigo_indec})")
                    print(f"   - Población: {poblacion:,}")
                    print(f"   - Zona UGD: {zona_ugd}")

        session.commit()
        print(f"\n✅ {created_count} departamentos creados")
        print(f"✅ {updated_count} departamentos actualizados")

        # Verificar la actualización
        stmt_verify = select(Departamento).where(
            Departamento.id_provincia_indec == 26
        ).order_by(Departamento.nombre)
        departamentos = session.execute(stmt_verify).scalars().all()

        print("\n=== DEPARTAMENTOS DE CHUBUT EN LA BASE DE DATOS ===")
        for depto in departamentos:
            print(f"  {depto.nombre} (Código {depto.id_departamento_indec})")
            if depto.poblacion:
                print(f"    - Población: {depto.poblacion:,}")
            if depto.region_sanitaria:
                print(f"    - Zona UGD: {depto.region_sanitaria}")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise


def main():
    """Función principal del seed"""
    print("\n🗺️ Seeding Departamentos de Chubut...")

    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db"
    )

    # Cambiar postgresql+asyncpg:// por postgresql:// para usar psycopg2 síncrono
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    # Crear engine y sesión
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session:
        seed_departamentos_chubut(session)

    print("\n✅ Seed de departamentos completado")


if __name__ == "__main__":
    main()