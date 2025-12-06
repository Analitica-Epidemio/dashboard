#!/usr/bin/env python3
"""
Seed para agregar/actualizar nombres reales de comunas y barrios de CABA.

Las comunas de CABA en INDEC aparecen como códigos numéricos genéricos
(ej: "Localidad INDEC 2002010"). Este script les asigna nombres descriptivos
basados en los barrios principales de cada comuna.

Fuente: https://www.buenosaires.gob.ar/comunas
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.config import settings

# Mapeo de códigos INDEC a nombres descriptivos de comunas/barrios CABA
# Cada comuna tiene sus barrios principales como referencia
COMUNAS_CABA = {
    2001010: "Comuna 1 (Retiro, San Nicolás, Puerto Madero, San Telmo, Montserrat, Constitución)",
    2002010: "Comuna 2 (Recoleta)",
    2003010: "Comuna 3 (Balvanera, San Cristóbal)",
    2004010: "Comuna 4 (Barracas, La Boca, Nueva Pompeya, Parque Patricios)",
    2005010: "Comuna 5 (Almagro, Boedo)",
    2006010: "Comuna 6 (Caballito)",
    2007010: "Comuna 7 (Flores, Parque Chacabuco)",
    2008010: "Comuna 8 (Villa Soldati, Villa Riachuelo, Villa Lugano)",
    2009010: "Comuna 9 (Liniers, Mataderos, Parque Avellaneda)",
    2010010: "Comuna 10 (Villa Real, Monte Castro, Versalles, Floresta, Vélez Sarsfield, Villa Luro)",
    2011010: "Comuna 11 (Villa General Mitre, Villa Devoto, Villa del Parque, Villa Santa Rita)",
    2012010: "Comuna 12 (Coghlan, Saavedra, Villa Urquiza, Villa Pueyrredón)",
    2013010: "Comuna 13 (Belgrano, Colegiales, Núñez)",
    2014010: "Comuna 14 (Palermo)",
    2015010: "Comuna 15 (Agronomía, Chacarita, Parque Chas, Paternal, Villa Crespo, Villa Ortúzar)",
}


def actualizar_comunas_caba(conn: Connection) -> int:
    """
    Actualiza los nombres de las comunas de CABA con nombres descriptivos.

    Args:
        conn: Conexión SQLAlchemy

    Returns:
        Número de comunas actualizadas
    """
    print("\n" + "=" * 70)
    print("📍 ACTUALIZANDO NOMBRES DE COMUNAS DE CABA")
    print("=" * 70)

    updated = 0
    not_found = 0

    for id_localidad, nombre_descriptivo in COMUNAS_CABA.items():
        # Verificar si existe
        check_stmt = text("""
            SELECT id_localidad_indec, nombre
            FROM localidad
            WHERE id_localidad_indec = :id
        """)

        result = conn.execute(check_stmt, {"id": id_localidad})
        row = result.fetchone()

        if row:
            nombre_actual = row.nombre
            print(f"\n  🔄 Actualizando {id_localidad}:")
            print(f"     Actual: {nombre_actual}")
            print(f"     Nuevo:  {nombre_descriptivo}")

            # Actualizar
            update_stmt = text("""
                UPDATE localidad
                SET nombre = :nombre
                WHERE id_localidad_indec = :id
            """)

            try:
                conn.execute(
                    update_stmt, {"id": id_localidad, "nombre": nombre_descriptivo}
                )
                updated += 1
            except Exception as e:
                print(f"     ❌ Error: {e}")
        else:
            print(f"\n  ⚠️  Comuna {id_localidad} no existe en la DB")
            not_found += 1

    # Commit cambios
    # Commit changes handled by context manager

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  ✅ Comunas actualizadas: {updated}")
    if not_found > 0:
        print(f"  ⚠️  Comunas no encontradas: {not_found}")
    print()

    return updated


def main() -> None:
    """Función principal"""
    print("=" * 70)
    print("SEED: ACTUALIZAR NOMBRES DE COMUNAS DE CABA")
    print("=" * 70)

    # Crear engine desde settings
    database_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    engine = create_engine(database_url, echo=False)

    with engine.begin() as conn:
        actualizar_comunas_caba(conn)

    print("✅ Seed completado\n")


if __name__ == "__main__":
    main()
