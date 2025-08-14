"""
Seed para cargar establecimientos de salud principales de Chubut.
"""

from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.establecimientos.models import Establecimiento

ESTABLECIMIENTOS_PRINCIPALES = [
    # Hospitales Regionales
    {
        "id": 1001,
        "establecimiento": "Hospital Regional de Comodoro Rivadavia",
        "id_localidad_establecimiento": 26021007,  # Comodoro Rivadavia
    },
    {
        "id": 1002,
        "establecimiento": "Hospital Zonal de Trelew",
        "id_localidad_establecimiento": 26077020,  # Trelew
    },
    {
        "id": 1003,
        "establecimiento": "Hospital Zonal de Esquel",
        "id_localidad_establecimiento": 26035020,  # Esquel
    },
    {
        "id": 1004,
        "establecimiento": "Hospital Subzonal de Puerto Madryn",
        "id_localidad_establecimiento": 26007040,  # Puerto Madryn
    },
    {
        "id": 1005,
        "establecimiento": "Hospital Rural de Rawson",
        "id_localidad_establecimiento": 26077010,  # Rawson
    },
    # Centros de Salud importantes
    {
        "id": 2001,
        "establecimiento": "Centro de Salud Norte - Comodoro Rivadavia",
        "id_localidad_establecimiento": 26021007,
    },
    {
        "id": 2002,
        "establecimiento": "Centro de Salud Sur - Trelew",
        "id_localidad_establecimiento": 26077020,
    },
    {
        "id": 2003,
        "establecimiento": "Centro de Salud Fontana - Puerto Madryn",
        "id_localidad_establecimiento": 26007040,
    },
    # Hospitales Rurales
    {
        "id": 3001,
        "establecimiento": "Hospital Rural de Sarmiento",
        "id_localidad_establecimiento": 26091070,  # Sarmiento
    },
    {
        "id": 3002,
        "establecimiento": "Hospital Rural de El Maitén",
        "id_localidad_establecimiento": 26014020,  # El Maitén
    },
    {
        "id": 3003,
        "establecimiento": "Hospital Rural de Río Mayo",
        "id_localidad_establecimiento": 26084010,  # Río Mayo
    },
    {
        "id": 3004,
        "establecimiento": "Hospital Rural de Gobernador Costa",
        "id_localidad_establecimiento": 26098020,  # Gobernador Costa
    },
]


async def seed_establecimientos(session: AsyncSession) -> None:
    """
    Carga los establecimientos de salud principales de Chubut.
    """
    print("🏥 Iniciando carga de establecimientos de salud...")

    # Verificar si ya existen establecimientos
    result = await session.execute(select(Establecimiento).limit(1))
    if result.first():
        print("   ✅ Establecimientos ya existen en la base de datos, saltando...")
        return

    # Verificar que existan las localidades necesarias
    localidades_ids = {
        est["id_localidad_establecimiento"] for est in ESTABLECIMIENTOS_PRINCIPALES
    }
    from app.domains.localidades.models import Localidad

    result = await session.execute(
        select(Localidad).where(col(Localidad.id_localidad_indec).in_(localidades_ids))
    )
    localidades_existentes = {loc.id_localidad_indec for loc in result.scalars().all()}

    # Crear establecimientos solo si existe la localidad
    establecimientos_creados = 0
    establecimientos_omitidos = 0

    for est_data in ESTABLECIMIENTOS_PRINCIPALES:
        if est_data["id_localidad_establecimiento"] in localidades_existentes:
            establecimiento = Establecimiento(**est_data)
            session.add(establecimiento)
            establecimientos_creados += 1
        else:
            print(
                f"   ⚠️ Omitiendo {est_data['establecimiento']} - localidad {est_data['id_localidad_establecimiento']} no encontrada"
            )
            establecimientos_omitidos += 1

    if establecimientos_creados > 0:
        await session.commit()
        print(f"   ✅ Creados {establecimientos_creados} establecimientos")

    if establecimientos_omitidos > 0:
        print(
            f"   ⚠️ Se omitieron {establecimientos_omitidos} establecimientos por falta de localidades"
        )
