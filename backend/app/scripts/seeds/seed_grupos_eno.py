"""
Seed de Grupos ENO (CasoEpidemiologicos de Notificación Obligatoria).

Este seed carga todos los grupos ENO oficiales del SNVS con:
- Nombre completo
- Código kebab-case único
- Descripción
- Ventana de días para visualización temporal (NULL = acumulado)

La ventana_dias_default define cuántos días considerar para "casos activos"
en la visualización temporal del mapa:
- NULL = usar modo acumulado (VIH, Sífilis, enfermedades crónicas)
- Valor en días = ventana de casos activos (Dengue=21, IRA=7, etc.)

FUENTE: Sistema Nacional de Vigilancia de la Salud (SNVS) - Argentina
"""

from typing import List, TypedDict

from sqlalchemy import text
from sqlalchemy.orm import Session


class GrupoEnoData(TypedDict):
    nombre: str
    codigo: str
    descripcion: str
    ventana_dias_default: int | None


# Lista completa de grupos ENO con sus configuraciones
# Excluye "Vigilancia Epidemiológica" que era un hack genérico
GRUPOS_ENO: List[GrupoEnoData] = [
    # Enfermedades transmitidas por vectores
    {
        "nombre": "Dengue",
        "codigo": "dengue",
        "descripcion": "Vigilancia de casos de Dengue (serotipos DEN-1 a DEN-4)",
        "ventana_dias_default": 21,  # Período virémico + incubación mosquito
    },
    {
        "nombre": "Infección por Virus del Zika",
        "codigo": "infeccion-por-virus-del-zika",
        "descripcion": "Vigilancia de infección por virus Zika",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Fiebre Amarilla",
        "codigo": "fiebre-amarilla",
        "descripcion": "Vigilancia de Fiebre Amarilla selvática y urbana",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Leishmaniasis",
        "codigo": "leishmaniasis",
        "descripcion": "Vigilancia de Leishmaniasis cutánea y visceral",
        "ventana_dias_default": 30,  # Período de incubación largo
    },
    {
        "nombre": "Paludismo",
        "codigo": "paludismo",
        "descripcion": "Vigilancia de Paludismo/Malaria",
        "ventana_dias_default": 30,
    },
    {
        "nombre": "Hantavirosis",
        "codigo": "hantavirosis",
        "descripcion": "Vigilancia de Síndrome Pulmonar por Hantavirus",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Fiebre del Nilo Occidental",
        "codigo": "fiebre-del-nilo-occidental",
        "descripcion": "Vigilancia de infección por virus del Nilo Occidental",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Fiebre Hemorrágica Argentina (FHA)",
        "codigo": "fiebre-hemorragica-argentina",
        "descripcion": "Vigilancia de Fiebre Hemorrágica Argentina (virus Junín)",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Chagas",
        "codigo": "chagas",
        "descripcion": "Vigilancia de Enfermedad de Chagas aguda y crónica",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    # Enfermedades respiratorias
    {
        "nombre": "Infecciones Respiratorias Agudas",
        "codigo": "infecciones-respiratorias-agudas",
        "descripcion": "Vigilancia de IRA, ETI, Bronquiolitis, Neumonía",
        "ventana_dias_default": 7,  # Contagio corto
    },
    {
        "nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "codigo": "unidad-centinela-de-infeccion-respiratoria-aguda-grave-uc-irag",
        "descripcion": "Vigilancia centinela de IRAG con internación",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Coqueluche",
        "codigo": "coqueluche",
        "descripcion": "Vigilancia de Tos Convulsa (Bordetella pertussis)",
        "ventana_dias_default": 21,  # Período contagioso más largo
    },
    {
        "nombre": "Tuberculosis",
        "codigo": "tuberculosis",
        "descripcion": "Vigilancia de Tuberculosis pulmonar y extrapulmonar",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    {
        "nombre": "Estudio de SARS-CoV-2 en Situaciones Especiales",
        "codigo": "estudio-de-sars-cov-2-en-situaciones-especiales",
        "descripcion": "Vigilancia de COVID-19 en situaciones especiales",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Vigilancia Genómica de SARS-CoV-2",
        "codigo": "vigilancia-genomica-de-sars-cov-2",
        "descripcion": "Vigilancia genómica de variantes de SARS-CoV-2",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Psitacosis",
        "codigo": "psitacosis",
        "descripcion": "Vigilancia de Psitacosis (Chlamydia psittaci)",
        "ventana_dias_default": 14,
    },
    # ITS y enfermedades crónicas
    {
        "nombre": "VIH-SIDA",
        "codigo": "vih-sida",
        "descripcion": "Vigilancia de infección por VIH y casos de SIDA",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    {
        "nombre": "Infecciones de Transmisión Sexual",
        "codigo": "infecciones-de-transmision-sexual",
        "descripcion": "Vigilancia de Sífilis, Gonorrea, Clamidia y otras ITS",
        "ventana_dias_default": None,  # Incluye sífilis (crónica)
    },
    {
        "nombre": "Infecciones de Transmisión Vertical",
        "codigo": "infecciones-de-transmision-vertical",
        "descripcion": "Vigilancia de Sífilis congénita, VIH perinatal, Chagas congénito",
        "ventana_dias_default": None,  # Condiciones congénitas
    },
    {
        "nombre": "Hepatitis Virales",
        "codigo": "hepatitis-virales",
        "descripcion": "Vigilancia de Hepatitis A, B, C, D y E",
        "ventana_dias_default": None,  # B y C pueden ser crónicas
    },
    # Enfermedades gastrointestinales
    {
        "nombre": "Diarreas y Patógenos de Transmisión Alimentaria",
        "codigo": "diarreas-y-patogenos-de-transmision-alimentaria",
        "descripcion": "Vigilancia de diarreas agudas y ETA",
        "ventana_dias_default": 7,  # Brotes cortos
    },
    {
        "nombre": "SUH y Diarreas por STEC",
        "codigo": "suh-y-diarreas-por-stec",
        "descripcion": "Vigilancia de Síndrome Urémico Hemolítico y E. coli productora de toxina Shiga",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Fiebre Tifoidea y Paratifoidea",
        "codigo": "fiebre-tifoidea-y-paratifoidea",
        "descripcion": "Vigilancia de Fiebre Tifoidea y Paratifoidea",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Listeriosis",
        "codigo": "listeriosis",
        "descripcion": "Vigilancia de Listeriosis invasiva",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Triquinelosis",
        "codigo": "triquinelosis",
        "descripcion": "Vigilancia de Triquinelosis",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Botulismo",
        "codigo": "botulismo",
        "descripcion": "Vigilancia de Botulismo alimentario, del lactante y de heridas",
        "ventana_dias_default": 7,
    },
    {
        "nombre": "Cólera",
        "codigo": "colera",
        "descripcion": "Vigilancia de Cólera (evento de notificación internacional - RSI)",
        "ventana_dias_default": 7,
    },
    # Zoonosis
    {
        "nombre": "Rabia",
        "codigo": "rabia",
        "descripcion": "Vigilancia de Rabia humana y animal, accidentes potencialmente rábicos",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Brucelosis",
        "codigo": "brucelosis",
        "descripcion": "Vigilancia de Brucelosis",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Hidatidosis",
        "codigo": "hidatidosis",
        "descripcion": "Vigilancia de Hidatidosis/Equinococosis",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    {
        "nombre": "Leptospirosis",
        "codigo": "leptospirosis",
        "descripcion": "Vigilancia de Leptospirosis",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Carbunco (Ántrax)",
        "codigo": "carbunco",
        "descripcion": "Vigilancia de Carbunco/Ántrax cutáneo, inhalatorio y gastrointestinal",
        "ventana_dias_default": 14,
    },
    # Envenenamientos/intoxicaciones
    {
        "nombre": "Envenenamiento por Animales Ponzoñosos",
        "codigo": "envenenamiento-por-animales-ponzonosos",
        "descripcion": "Vigilancia de Ofidismo, Araneísmo, Escorpionismo",
        "ventana_dias_default": 7,  # CasoEpidemiologicos puntuales
    },
    {
        "nombre": "Intoxicaciones",
        "codigo": "intoxicaciones",
        "descripcion": "Vigilancia de intoxicaciones por monóxido de carbono, plaguicidas, etc.",
        "ventana_dias_default": 7,
    },
    # Lesiones
    {
        "nombre": "Lesiones Intencionales",
        "codigo": "lesiones-intencionales",
        "descripcion": "Vigilancia de violencias, intento de suicidio, lesiones autoinfligidas",
        "ventana_dias_default": 7,
    },
    {
        "nombre": "Lesiones No Intencionales",
        "codigo": "lesiones-no-intencionales",
        "descripcion": "Vigilancia de accidentes de tránsito, caídas, quemaduras",
        "ventana_dias_default": 7,
    },
    # Enfermedades prevenibles por vacunas
    {
        "nombre": "Enfermedad Febril Exantemática (EFE)",
        "codigo": "enfermedad-febril-exantematica-efe",
        "descripcion": "Vigilancia de Sarampión, Rubéola y síndromes febriles con exantema",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Parotiditis",
        "codigo": "parotiditis",
        "descripcion": "Vigilancia de Paperas",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Poliomielitis-Parálisis Flácida Aguda en Menores de 15 Años",
        "codigo": "poliomielitis-paralisis-flacida-aguda-en-menores-de-15-anos",
        "descripcion": "Vigilancia de Parálisis Flácida Aguda para mantener erradicación de Polio",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Tétanos",
        "codigo": "tetanos",
        "descripcion": "Vigilancia de Tétanos (incluye neonatal)",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Difteria",
        "codigo": "difteria",
        "descripcion": "Vigilancia de Difteria",
        "ventana_dias_default": 14,
    },
    # Meningitis/encefalitis
    {
        "nombre": "Meningoencefalitis",
        "codigo": "meningoencefalitis",
        "descripcion": "Vigilancia de Meningitis y Encefalitis de diversas etiologías",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Otras Infecciones Invasivas",
        "codigo": "otras-infecciones-invasivas",
        "descripcion": "Vigilancia de infecciones invasivas bacterianas y otras",
        "ventana_dias_default": 14,
    },
    # Micosis
    {
        "nombre": "Micosis Sistémicas Endémicas",
        "codigo": "micosis-sistemicas-endemicas",
        "descripcion": "Vigilancia de Histoplasmosis, Coccidioidomicosis, Paracoccidioidomicosis",
        "ventana_dias_default": None,  # Pueden ser crónicas
    },
    {
        "nombre": "Micosis Sistémicas Oportunistas",
        "codigo": "micosis-sistemicas-oportunistas",
        "descripcion": "Vigilancia de Criptococosis, Aspergilosis, Candidiasis invasiva",
        "ventana_dias_default": None,
    },
    # Síndrome febril
    {
        "nombre": "Síndrome Febril Agudo Inespecífico (SFAI)",
        "codigo": "sindrome-febril-agudo-inespecifico",
        "descripcion": "Vigilancia de síndromes febriles sin etiología definida",
        "ventana_dias_default": 14,
    },
    # Otras
    {
        "nombre": "Rickettsiosis",
        "codigo": "rickettsiosis",
        "descripcion": "Vigilancia de Fiebre Manchada, Tifus y otras rickettsiosis",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Bartonelosis",
        "codigo": "bartonelosis",
        "descripcion": "Vigilancia de Enfermedad por arañazo de gato y otras bartonelosis",
        "ventana_dias_default": 14,
    },
    {
        "nombre": "Citomegalovirosis",
        "codigo": "citomegalovirosis",
        "descripcion": "Vigilancia de infección por Citomegalovirus",
        "ventana_dias_default": None,  # Latente/crónica
    },
    {
        "nombre": "Viruela",
        "codigo": "viruela",
        "descripcion": "Vigilancia de Viruela (erradicada) y Viruela del mono",
        "ventana_dias_default": 21,
    },
    {
        "nombre": "Cisticercosis",
        "codigo": "cisticercosis",
        "descripcion": "Vigilancia de Cisticercosis/Neurocisticercosis",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    {
        "nombre": "Parasitosis Hemáticas y Tisulares (Otras)",
        "codigo": "parasitosis-hematicas-y-tisulares-otras",
        "descripcion": "Vigilancia de otras parasitosis sistémicas",
        "ventana_dias_default": None,
    },
    {
        "nombre": "Celiaquía",
        "codigo": "celiaquia",
        "descripcion": "Registro de casos de Enfermedad Celíaca",
        "ventana_dias_default": None,  # Enfermedad crónica
    },
    {
        "nombre": "Pesquisa Neonatal",
        "codigo": "pesquisa-neonatal",
        "descripcion": "Vigilancia de enfermedades detectadas por pesquisa neonatal",
        "ventana_dias_default": None,
    },
    # Vigilancia especial
    {
        "nombre": "Vigilancia Animal",
        "codigo": "vigilancia-animal",
        "descripcion": "Vigilancia de enfermedades en animales con impacto en salud pública",
        "ventana_dias_default": None,
    },
    {
        "nombre": "Banco de Sangre",
        "codigo": "banco-de-sangre",
        "descripcion": "Vigilancia de marcadores infecciosos en donantes de sangre",
        "ventana_dias_default": None,
    },
]


def seed_grupos_eno(session: Session) -> int:
    """
    Carga todos los grupos ENO en la base de datos.

    Usa UPSERT: inserta si no existe, actualiza si existe (por código).

    Returns:
        Número de grupos insertados/actualizados
    """
    print("\n" + "=" * 70)
    print("🏥 CARGANDO GRUPOS ENO (CasoEpidemiologicos de Notificación Obligatoria)")
    print("=" * 70)

    # Primero eliminar el grupo "Vigilancia Epidemiológica" si existe (era un hack)
    delete_hack = text("""
        DELETE FROM grupo_de_enfermedades
        WHERE slug = 'vigilancia-epidemiologica'
    """)
    result = session.execute(delete_hack)
    if result.rowcount > 0:
        print("  🗑️  Eliminado grupo hack 'vigilancia-epidemiologica'")

    inserted = 0
    updated = 0

    for grupo in GRUPOS_ENO:
        # UPSERT usando ON CONFLICT
        stmt = text("""
            INSERT INTO grupo_de_enfermedades (nombre, slug, descripcion, ventana_dias_visualizacion, created_at, updated_at)
            VALUES (:nombre, :slug, :descripcion, :ventana_dias, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (slug) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                descripcion = EXCLUDED.descripcion,
                ventana_dias_visualizacion = EXCLUDED.ventana_dias_visualizacion,
                updated_at = CURRENT_TIMESTAMP
            RETURNING (xmax = 0) AS inserted
        """)

        result = session.execute(
            stmt,
            {
                "nombre": grupo["nombre"],
                "slug": grupo["codigo"],
                "descripcion": grupo["descripcion"],
                "ventana_dias": grupo["ventana_dias_default"],
            },
        )

        row = result.fetchone()
        if row and row[0]:  # xmax = 0 means INSERT
            inserted += 1
            ventana_str = (
                f"{grupo['ventana_dias_default']} días"
                if grupo["ventana_dias_default"]
                else "acumulado"
            )
            print(f"  ✓ {grupo['codigo']} ({ventana_str})")
        else:
            updated += 1

    session.commit()

    print(f"\n✅ Grupos ENO: {inserted} insertados, {updated} actualizados")
    print(f"   Total: {len(GRUPOS_ENO)} grupos configurados")
    return inserted + updated


def main() -> None:
    """Función principal para ejecutar el seed."""
    import os

    from sqlmodel import create_engine

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db",
    )

    if "postgresql+asyncpg" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(database_url)

    with Session(engine) as session:
        seed_grupos_eno(session)

    print("\n" + "=" * 70)
    print("✅ SEED COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
