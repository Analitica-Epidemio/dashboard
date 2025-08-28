"""
Seed para cargar eventos epidemiológicos estándar.

Estos son los eventos principales del sistema SNVS que se monitorean.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domains.eventos.models import Evento

EVENTOS_EPIDEMIOLOGICOS = [
    # Sífilis
    {"id": 1, "evento": "Sífilis", "grupo_evento": "ITS"},
    {"id": 2, "evento": "Sífilis en personas gestantes", "grupo_evento": "ITS"},
    {"id": 3, "evento": "Sífilis congénita", "grupo_evento": "ITS"},
    {
        "id": 4,
        "evento": "Sífilis - RN expuesto en investigación",
        "grupo_evento": "ITS",
    },
    # Infecciones Respiratorias Agudas
    {
        "id": 5,
        "evento": "Internado y/o fallecido por COVID o IRA",
        "grupo_evento": "IRA",
    },
    {
        "id": 6,
        "evento": "COVID-19, Influenza y OVR en ambulatorios (No UMAs)",
        "grupo_evento": "IRA",
    },
    {
        "id": 7,
        "evento": "Monitoreo de SARS COV-2 y VSR en ambulatorios",
        "grupo_evento": "IRA",
    },
    # Meningoencefalitis
    {"id": 8, "evento": "Meningoencefalitis", "grupo_evento": "Neurológicas"},
    # SUH
    {
        "id": 9,
        "evento": "SUH - Sindrome Urémico Hemolítico",
        "grupo_evento": "Gastrointestinales",
    },
    # Hepatitis
    {"id": 10, "evento": "Hepatitis A", "grupo_evento": "Hepatitis"},
    {"id": 11, "evento": "Hepatitis B", "grupo_evento": "Hepatitis"},
    {"id": 12, "evento": "Hepatitis C", "grupo_evento": "Hepatitis"},
    # Tuberculosis
    {"id": 13, "evento": "Tuberculosis", "grupo_evento": "Micobacterias"},
    # Dengue y otros arbovirus
    {"id": 14, "evento": "Dengue", "grupo_evento": "Arbovirus"},
    {"id": 15, "evento": "Zika", "grupo_evento": "Arbovirus"},
    {"id": 16, "evento": "Chikungunya", "grupo_evento": "Arbovirus"},
]


async def seed_eventos(session: AsyncSession) -> None:
    """
    Carga los eventos epidemiológicos estándar del sistema.
    """
    print("🦠 Iniciando carga de eventos epidemiológicos...")

    # Verificar si ya existen eventos
    result = await session.execute(select(Evento).limit(1))
    if result.first():
        print("   ✅ Eventos ya existen en la base de datos, saltando...")
        return

    # Crear eventos
    eventos_creados = 0
    for evento_data in EVENTOS_EPIDEMIOLOGICOS:
        evento = Evento(**evento_data)
        session.add(evento)
        eventos_creados += 1

    await session.commit()
    print(f"   ✅ Creados {eventos_creados} eventos epidemiológicos")
