"""
Clasificación de agentes etiológicos basada en strings exactos del Excel LAB_P26.

Este diccionario mapea EXACTAMENTE los valores de la columna EVENTO del Excel
a su categoría (virus/bacteria/parasito) y grupo funcional (respiratorio/enterico/etc).

IMPORTANTE: Los strings deben coincidir EXACTAMENTE con los del Excel.
No usar patrones ni "contains", solo match exacto.
"""

from app.domains.catalogos.agentes.models import CategoriaAgente, GrupoAgente

# Tipo de retorno
ClassificacionAgente = tuple[str, str]  # (categoria, grupo)


# Diccionario de clasificación exacta
# Key: nombre exacto del EVENTO en LAB_P26.xlsx
# Value: (CategoriaAgente, GrupoAgente)
CLASIFICACION_AGENTES: dict[str, ClassificacionAgente] = {
    # =========================================================================
    # VIRUS RESPIRATORIOS
    # =========================================================================
    "Virus Influenza A por IF o Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Influenza A por PCR NO estudiados por IF ni Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Influenza A por PCR negativos por IF o Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Influenza B por IF o Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Influenza B por PCR NO estudiados por IF ni Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Influenza B por PCR negativos por IF o Test rápido": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "Virus Sincicial Respiratorio": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Metapneumovirus": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Adenovirus": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Virus Parainfluenza 1": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Virus Parainfluenza 2": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Virus Parainfluenza 3": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "Virus Parainfluenza sin tipificar": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "SARS CoV-2 por PCR o LAMP": (CategoriaAgente.VIRUS, GrupoAgente.RESPIRATORIO),
    "SARS CoV-2 por Test de antígenos": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    "SARS-COV-2 en otras situaciones": (
        CategoriaAgente.VIRUS,
        GrupoAgente.RESPIRATORIO,
    ),
    # =========================================================================
    # BACTERIAS RESPIRATORIAS
    # =========================================================================
    "Streptococcus pneumoniae": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Haemophilus influenzae": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Moraxella catarrhalis": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Klebsiella pneumoniae": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Staphylococcus aureus": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Chlamydophila pneumoniae": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    "Mycoplasma pneumoniae": (CategoriaAgente.BACTERIA, GrupoAgente.RESPIRATORIO),
    # =========================================================================
    # VIRUS ENTÉRICOS
    # =========================================================================
    "Rotavirus (DV)": (CategoriaAgente.VIRUS, GrupoAgente.ENTERICO),
    "Adenovirus (DV)": (CategoriaAgente.VIRUS, GrupoAgente.ENTERICO),
    "Norovirus": (CategoriaAgente.VIRUS, GrupoAgente.ENTERICO),
    # =========================================================================
    # BACTERIAS ENTÉRICAS
    # =========================================================================
    "Salmonella spp.": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Salmonella enteritidis": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Salmonella newport": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Salmonella typhimurium": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella spp.": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella flexneri": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella flexneri 1": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella flexneri 2": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella sonnei": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella boydii": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Shigella dysenteriae": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Campylobacter sp.": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Campylobacter jejuni": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Campylobacter coli": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Bacillus grupo cereus": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Histórico - STEC O157": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Histórico - STEC no O157": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    "Histórico - Vibrio cholerae no O1": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.ENTERICO,
    ),
    "Tamizaje de E. coli enteroagregativo (EAEC)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.ENTERICO,
    ),
    "Tamizaje de E. coli enteroinvasivo (EIEC)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.ENTERICO,
    ),
    "Tamizaje de E. coli enteropatógeno (EPEC)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.ENTERICO,
    ),
    "Tamizaje de E. coli enterotoxigénico (ETEC)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.ENTERICO,
    ),
    "Otros patógenos bacterianos": (CategoriaAgente.BACTERIA, GrupoAgente.ENTERICO),
    # =========================================================================
    # PARÁSITOS ENTÉRICOS
    # =========================================================================
    "Giardia duodenalis": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Cryptosporidium sp. (por coloración o métodos moleculares)": (
        CategoriaAgente.PARASITO,
        GrupoAgente.ENTERICO,
    ),
    "Historico - Cryptosporidium sp.": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Cyclospora cayetanensis (por coloración o métodos moleculares)": (
        CategoriaAgente.PARASITO,
        GrupoAgente.ENTERICO,
    ),
    "Historico - Cyclospora sp.": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Cystoisospora belli": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Entamoeba histolytica (por métodos moleculares)": (
        CategoriaAgente.PARASITO,
        GrupoAgente.ENTERICO,
    ),
    "Entamoeba histolytica/dispar/moshkovski/bangladeshi": (
        CategoriaAgente.PARASITO,
        GrupoAgente.ENTERICO,
    ),
    "Blastocystis": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Balantidium coli": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Microsporidios (por coloración o métodos moleculares)": (
        CategoriaAgente.PARASITO,
        GrupoAgente.ENTERICO,
    ),
    "Historico - Microsporidios": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    # Comensales (no patógenos pero se reportan)
    "Entamoeba coli": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Entamoeba hartmanni": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Endolimax nana": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Iodamoeba bütschlii": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Chilomastix mesnili": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Dientamoeba fragilis": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    # Helmintos
    "Ascaris lumbricoides": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Enterobius vermicularis": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Trichuris trichiura": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Strongyloides stercoralis": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Uncinarias": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Trichostrongylus sp.": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Hymenolepis nana": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Hymenolepis diminuta": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Dipylidium caninum": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Taenia sp.": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Difilobótridos": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Fasciola hepática": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    "Schistosoma mansoni": (CategoriaAgente.PARASITO, GrupoAgente.ENTERICO),
    # =========================================================================
    # PARÁSITOS TISULARES / ZOONÓTICOS
    # =========================================================================
    "Toxoplasmosis": (CategoriaAgente.PARASITO, GrupoAgente.ZOONOTICO),
    "Toxoplasmosis - IgG (E)": (CategoriaAgente.PARASITO, GrupoAgente.ZOONOTICO),
    "Toxoplasmosis - IgM (E)": (CategoriaAgente.PARASITO, GrupoAgente.ZOONOTICO),
    "Toxocariosis": (CategoriaAgente.PARASITO, GrupoAgente.ZOONOTICO),
    "Hidatidosis (ZV)": (CategoriaAgente.PARASITO, GrupoAgente.ZOONOTICO),
    "Brucelosis (BS)": (CategoriaAgente.BACTERIA, GrupoAgente.ZOONOTICO),
    "Brucelosis (Emb)": (CategoriaAgente.BACTERIA, GrupoAgente.ZOONOTICO),
    "Paludismo -  Búsqueda reactiva(ZV)": (
        CategoriaAgente.PARASITO,
        GrupoAgente.VECTORIAL,
    ),
    # =========================================================================
    # CHAGAS
    # =========================================================================
    "Chagas (testeo voluntario)": (CategoriaAgente.PARASITO, GrupoAgente.VECTORIAL),
    "Chagas crónico a demanda": (CategoriaAgente.PARASITO, GrupoAgente.VECTORIAL),
    "Chagas crónico en estudios poblacionales": (
        CategoriaAgente.PARASITO,
        GrupoAgente.VECTORIAL,
    ),
    "Chagas por 2 técnicas (BS)": (CategoriaAgente.PARASITO, GrupoAgente.VECTORIAL),
    "Chagas por 2 técnicas (E)": (CategoriaAgente.PARASITO, GrupoAgente.VECTORIAL),
    # =========================================================================
    # ITS (Infecciones de Transmisión Sexual)
    # =========================================================================
    "Infección por Chlamydia trachomatis": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Infección por Neisseria gonorrhoeae": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Infección por Mycoplasma genitalium": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Infección por Mycoplasma hominis": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Infección por Ureaplasma spp.": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Infección por Trichomonas vaginalis": (
        CategoriaAgente.PARASITO,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    # =========================================================================
    # VIH
    # =========================================================================
    "VIH (testeo voluntario)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "VIH - Hombres (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "VIH - Mujeres (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "VIH por pruebas confirmatorias (diagnóstico)": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH pruebas confirmatorias durante el embarazo": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH pruebas de tamizaje durante el embarazo": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH pruebas de tamizaje en Población Privada de la Libertad (PPL)": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH pruebas de tamizaje en población general": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH test en pareja de mujer embarazada (Emb)": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH test rápidos en población general": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "VIH-Durante el parto sin controles previos (Emb)": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "HTLV I + II (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    # =========================================================================
    # SÍFILIS
    # =========================================================================
    "Sífilis (testeo voluntario)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis Control de tratamiento": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas confirmatorias (Diagnóstico)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas confirmatorias (Emb)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas confirmatorias - Hombres (BS)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas confirmatorias - Mujeres (BS)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas de tamizaje (Emb)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas de tamizaje - Hombres (BS)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas de tamizaje - Mujeres (BS)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Sífilis por pruebas tamizaje (Diagnóstiico)": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    # =========================================================================
    # HEPATITIS
    # =========================================================================
    "Hepatitis A por IgM anti-VHA": (CategoriaAgente.VIRUS, GrupoAgente.ENTERICO),
    "Hepatitis B (testeo voluntario)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis B por HBsAg": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis B por HBsAg (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis B por HBsAg (Emb)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis B por a-HBcore (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis B por anti-HBc": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis C (BS)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis C (testeo voluntario)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis C por anti-VHC": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    "Hepatitis por a-HBcore (Emb)": (CategoriaAgente.VIRUS, GrupoAgente.SANGUINEO),
    # =========================================================================
    # PRUEBAS RÁPIDAS (categorización por el patógeno testeado)
    # =========================================================================
    "Pruebas rápidas para HEPATITIS B en parejas de personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para HEPATITIS B en personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para HEPATITIS B en población general": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para HEPATITIS C en parejas de personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para HEPATITIS C en personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para HEPATITIS C en población general": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para Sífilis en parejas de personas gestantes": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Pruebas rápidas para Sífilis en personas gestantes": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Pruebas rápidas para Sífilis en población general": (
        CategoriaAgente.BACTERIA,
        GrupoAgente.TRANSMISION_SEXUAL,
    ),
    "Pruebas rápidas para VIH en parejas de personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para VIH en personas gestantes": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    "Pruebas rápidas para VIH en población general": (
        CategoriaAgente.VIRUS,
        GrupoAgente.SANGUINEO,
    ),
    # =========================================================================
    # RUBÉOLA
    # =========================================================================
    "Rubéola- IgG (Emb)": (CategoriaAgente.VIRUS, GrupoAgente.OTRO),
    "Estreptococo beta hemolítico (Emb)": (CategoriaAgente.BACTERIA, GrupoAgente.OTRO),
}


def clasificar_agente(nombre_evento: str) -> ClassificacionAgente:
    """
    Clasifica un agente etiológico basándose en el nombre exacto del EVENTO.

    Args:
        nombre_evento: Valor exacto de la columna EVENTO del Excel LAB_P26

    Returns:
        Tupla (categoria, grupo) del agente.
        Si no se encuentra en el diccionario, retorna (OTRO, OTRO).
    """
    resultado = CLASIFICACION_AGENTES.get(nombre_evento)

    if resultado:
        return resultado

    # Fallback: si no está en el diccionario, retornar OTRO
    return (CategoriaAgente.OTRO, GrupoAgente.OTRO)


def generar_slug(nombre_evento: str, id_snvs: int) -> str:
    """
    Genera un slug único para un agente etiológico.

    Args:
        nombre_evento: Nombre del evento/agente
        id_snvs: ID del SNVS para garantizar unicidad

    Returns:
        Slug kebab-case único
    """
    # Normalizar: minúsculas, reemplazar espacios y caracteres especiales
    slug_base = (
        nombre_evento.lower()
        .strip()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(".", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace("ü", "u")
    )

    # Eliminar guiones duplicados
    while "--" in slug_base:
        slug_base = slug_base.replace("--", "-")

    # Añadir ID para unicidad
    return f"{slug_base}-{id_snvs}"


def generar_nombre_corto(nombre_evento: str) -> str:
    """
    Genera un nombre corto para gráficos basado en el nombre del evento.

    Args:
        nombre_evento: Nombre completo del evento

    Returns:
        Nombre corto (máximo 50 caracteres)
    """
    # Mapeo de nombres cortos conocidos
    NOMBRES_CORTOS: dict[str, str] = {
        "Virus Sincicial Respiratorio": "VSR",
        "Virus Influenza A por IF o Test rápido": "Flu A",
        "Virus Influenza A por PCR NO estudiados por IF ni Test rápido": "Flu A (PCR)",
        "Virus Influenza A por PCR negativos por IF o Test rápido": "Flu A (PCR neg)",
        "Virus Influenza B por IF o Test rápido": "Flu B",
        "Virus Influenza B por PCR NO estudiados por IF ni Test rápido": "Flu B (PCR)",
        "Virus Influenza B por PCR negativos por IF o Test rápido": "Flu B (PCR neg)",
        "Metapneumovirus": "hMPV",
        "SARS CoV-2 por PCR o LAMP": "SARS-CoV-2",
        "SARS CoV-2 por Test de antígenos": "SARS-CoV-2 (Ag)",
        "Rotavirus (DV)": "Rotavirus",
        "Adenovirus (DV)": "Adenovirus (DV)",
    }

    if nombre_evento in NOMBRES_CORTOS:
        return NOMBRES_CORTOS[nombre_evento]

    # Si no existe mapeo, truncar a 50 caracteres
    return nombre_evento[:50]
