"""
Seed de Agentes Etiológicos y sus configuraciones de extracción.

Basado en análisis del CSV epidemiológico de Chubut.

Agentes incluidos:
- Respiratorios: VSR, Influenza A/B, Metaneumovirus, SARS-CoV-2, Adenovirus
- Entéricos: STEC O157, Salmonella, Shigella, Rotavirus, Adenovirus entérico
- Dengue serotipos: DEN-1, DEN-2, DEN-3, DEN-4
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalogos.agentes.models import (
    AgenteEtiologico,
    CategoriaAgente,
    GrupoAgente,
)
from app.domains.vigilancia_nominal.models.agentes import (
    AgenteExtraccionConfig,
)
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad

logger = logging.getLogger(__name__)


# =============================================================================
# CATÁLOGO DE AGENTES ETIOLÓGICOS
# =============================================================================

AGENTES_CATALOGO: list[dict[str, Any]] = [
    # =========================================================================
    # VIRUS RESPIRATORIOS
    # =========================================================================
    {
        "slug": "vsr",
        "nombre": "Virus Sincicial Respiratorio",
        "nombre_corto": "VSR",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Principal causa de bronquiolitis en lactantes",
    },
    {
        "slug": "influenza-a",
        "nombre": "Influenza A",
        "nombre_corto": "Influenza A",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Virus de la gripe tipo A (incluye subtipos H1N1, H3N2, etc.)",
    },
    {
        "slug": "influenza-b",
        "nombre": "Influenza B",
        "nombre_corto": "Influenza B",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Virus de la gripe tipo B",
    },
    {
        "slug": "metaneumovirus",
        "nombre": "Metaneumovirus Humano",
        "nombre_corto": "Metaneumovirus",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Causa infecciones respiratorias similares a VSR",
    },
    {
        "slug": "sars-cov-2",
        "nombre": "SARS-CoV-2",
        "nombre_corto": "SARS-CoV-2",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Coronavirus causante de COVID-19",
    },
    {
        "slug": "adenovirus-respiratorio",
        "nombre": "Adenovirus (respiratorio)",
        "nombre_corto": "Adenovirus",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Adenovirus causante de infecciones respiratorias",
    },
    {
        "slug": "parainfluenza-1",
        "nombre": "Parainfluenza 1",
        "nombre_corto": "Parainfluenza 1",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Virus parainfluenza tipo 1",
    },
    {
        "slug": "parainfluenza-2",
        "nombre": "Parainfluenza 2",
        "nombre_corto": "Parainfluenza 2",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Virus parainfluenza tipo 2",
    },
    {
        "slug": "parainfluenza-3",
        "nombre": "Parainfluenza 3",
        "nombre_corto": "Parainfluenza 3",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.RESPIRATORIO,
        "descripcion": "Virus parainfluenza tipo 3",
    },
    # =========================================================================
    # AGENTES ENTÉRICOS
    # =========================================================================
    {
        "slug": "stec-o157",
        "nombre": "E. coli productor de toxina Shiga O157",
        "nombre_corto": "STEC O157",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Principal causa de SUH en Argentina",
    },
    {
        "slug": "stec-no-o157",
        "nombre": "E. coli productor de toxina Shiga no-O157",
        "nombre_corto": "STEC no-O157",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Otros serotipos de STEC (O145, O121, etc.)",
    },
    {
        "slug": "salmonella-spp",
        "nombre": "Salmonella spp.",
        "nombre_corto": "Salmonella",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Bacteria causante de salmonelosis",
    },
    {
        "slug": "shigella-spp",
        "nombre": "Shigella spp.",
        "nombre_corto": "Shigella",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Bacteria causante de shigelosis (disentería bacilar)",
    },
    {
        "slug": "shigella-flexneri",
        "nombre": "Shigella flexneri",
        "nombre_corto": "S. flexneri",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Especie de Shigella más común en países en desarrollo",
    },
    {
        "slug": "shigella-sonnei",
        "nombre": "Shigella sonnei",
        "nombre_corto": "S. sonnei",
        "categoria": CategoriaAgente.BACTERIA,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Especie de Shigella más común en países desarrollados",
    },
    {
        "slug": "rotavirus",
        "nombre": "Rotavirus",
        "nombre_corto": "Rotavirus",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Principal causa de diarrea viral en niños",
    },
    {
        "slug": "adenovirus-enterico",
        "nombre": "Adenovirus entérico (40/41)",
        "nombre_corto": "Adenovirus (DV)",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.ENTERICO,
        "descripcion": "Adenovirus causante de diarrea viral",
    },
    # =========================================================================
    # SEROTIPOS DENGUE
    # =========================================================================
    {
        "slug": "dengue-1",
        "nombre": "Dengue serotipo 1",
        "nombre_corto": "DEN-1",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.VECTORIAL,
        "descripcion": "Serotipo 1 del virus Dengue",
    },
    {
        "slug": "dengue-2",
        "nombre": "Dengue serotipo 2",
        "nombre_corto": "DEN-2",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.VECTORIAL,
        "descripcion": "Serotipo 2 del virus Dengue",
    },
    {
        "slug": "dengue-3",
        "nombre": "Dengue serotipo 3",
        "nombre_corto": "DEN-3",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.VECTORIAL,
        "descripcion": "Serotipo 3 del virus Dengue",
    },
    {
        "slug": "dengue-4",
        "nombre": "Dengue serotipo 4",
        "nombre_corto": "DEN-4",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.VECTORIAL,
        "descripcion": "Serotipo 4 del virus Dengue",
    },
    {
        "slug": "dengue-sin-serotipo",
        "nombre": "Dengue sin serotipo especificado",
        "nombre_corto": "Dengue s/s",
        "categoria": CategoriaAgente.VIRUS,
        "grupo": GrupoAgente.VECTORIAL,
        "descripcion": "Dengue confirmado sin identificación de serotipo",
    },
]


# =============================================================================
# CONFIGURACIONES DE EXTRACCIÓN
# Mapeo: (codigo_agente, nombre_evento) -> config
# =============================================================================

EXTRACCION_CONFIGS: list[dict[str, Any]] = [
    # =========================================================================
    # VIRUS RESPIRATORIOS - UC-IRAG
    # =========================================================================
    {
        "agente_codigo": "vsr",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"VSR|Sincicial",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo", "Positivo (+)", "Positivo (++)", "Positivo (+++)"],
        "metodo_deteccion_default": "Antígeno/PCR",
    },
    {
        "agente_codigo": "influenza-a",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Ii]nfluenza\s*A|Influenza A",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo", "Positivo (+)", "Positivo (++)", "Positivo (+++)"],
        "metodo_deteccion_default": "Antígeno/PCR",
    },
    {
        "agente_codigo": "influenza-b",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Ii]nfluenza\s*B|Influenza B",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
        "metodo_deteccion_default": "Antígeno/PCR",
    },
    {
        "agente_codigo": "metaneumovirus",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Mm]etaneumovirus",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo", "Positivo (+)", "Positivo (++)", "Positivo (+++)"],
        "metodo_deteccion_default": "PCR",
    },
    {
        "agente_codigo": "sars-cov-2",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"SARS-CoV-2|SARS.*CoV.*2|COVID",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
        "metodo_deteccion_default": "PCR",
    },
    {
        "agente_codigo": "adenovirus-respiratorio",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Aa]denovirus",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
        "metodo_deteccion_default": "Antígeno/PCR",
    },
    # Parainfluenza
    {
        "agente_codigo": "parainfluenza-1",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Pp]arainfluenza\s*1",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable"],
        "metodo_deteccion_default": "Antígeno",
    },
    {
        "agente_codigo": "parainfluenza-2",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Pp]arainfluenza\s*2",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable"],
        "metodo_deteccion_default": "Antígeno",
    },
    {
        "agente_codigo": "parainfluenza-3",
        "evento_nombre": "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Pp]arainfluenza\s*3",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable"],
        "metodo_deteccion_default": "Antígeno",
    },
    # =========================================================================
    # SARS-CoV-2 en otros eventos
    # =========================================================================
    {
        "agente_codigo": "sars-cov-2",
        "evento_nombre": "Estudio de SARS-COV-2 en situaciones especiales",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"SARS-CoV-2|Genoma viral SARS|Antígeno.*SARS",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
        "metodo_deteccion_default": "PCR/Antígeno",
    },
    # =========================================================================
    # AGENTES ENTÉRICOS - Diarrea aguda
    # =========================================================================
    {
        "agente_codigo": "stec-o157",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"STEC.*O157|O157|E\.\s*coli.*O157",
        "campo_resultado": None,  # La clasificación ya indica positivo
        "valores_positivos": None,
        "metodo_deteccion_default": "Cultivo/PCR",
    },
    {
        "agente_codigo": "stec-no-o157",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"STEC\s+no.O157|no-O157",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "Cultivo/PCR",
    },
    {
        "agente_codigo": "rotavirus",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Rr]otavirus",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Reactivo"],
        "metodo_deteccion_default": "Antígeno",
    },
    {
        "agente_codigo": "adenovirus-enterico",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Aa]denovirus",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Reactivo"],
        "metodo_deteccion_default": "Antígeno",
    },
    {
        "agente_codigo": "shigella-spp",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "RESULTADO",
        "patron_busqueda": r"[Ss]higella",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "Cultivo",
    },
    {
        "agente_codigo": "salmonella-spp",
        "evento_nombre": "Diarrea aguda",
        "campo_busqueda": "RESULTADO",
        "patron_busqueda": r"[Ss]almonella",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "Cultivo",
    },
    # =========================================================================
    # AGENTES ENTÉRICOS - SUH
    # =========================================================================
    {
        "agente_codigo": "stec-o157",
        "evento_nombre": "SUH - Sindrome Urémico Hemolítico",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"STEC.*O157|O157|infección por STEC O157",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "Serología/PCR",
    },
    {
        "agente_codigo": "stec-no-o157",
        "evento_nombre": "SUH - Sindrome Urémico Hemolítico",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"STEC\s+no.O157|no-O157",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "Serología/PCR",
    },
    # =========================================================================
    # AGENTES ENTÉRICOS - Brote ETA
    # =========================================================================
    {
        "agente_codigo": "rotavirus",
        "evento_nombre": "Sospecha de brote de ETA, o por agua o ruta fecal-oral",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Rr]otavirus",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo", "Reactivo"],
        "metodo_deteccion_default": "Antígeno",
    },
    {
        "agente_codigo": "shigella-spp",
        "evento_nombre": "Sospecha de brote de ETA, o por agua o ruta fecal-oral",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Ss]higella",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo"],
        "metodo_deteccion_default": "Cultivo",
    },
    {
        "agente_codigo": "salmonella-spp",
        "evento_nombre": "Sospecha de brote de ETA, o por agua o ruta fecal-oral",
        "campo_busqueda": "DETERMINACION",
        "patron_busqueda": r"[Ss]almonella",
        "campo_resultado": "RESULTADO",
        "valores_positivos": ["Positivo"],
        "metodo_deteccion_default": "Cultivo",
    },
    # =========================================================================
    # DENGUE SEROTIPOS
    # =========================================================================
    {
        "agente_codigo": "dengue-1",
        "evento_nombre": "Dengue",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"DEN-1|DEN1|serotipo 1",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "PCR/Serología",
    },
    {
        "agente_codigo": "dengue-2",
        "evento_nombre": "Dengue",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"DEN-2|DEN2|serotipo 2",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "PCR/Serología",
    },
    {
        "agente_codigo": "dengue-3",
        "evento_nombre": "Dengue",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"DEN-3|DEN3|serotipo 3",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "PCR/Serología",
    },
    {
        "agente_codigo": "dengue-4",
        "evento_nombre": "Dengue",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"DEN-4|DEN4|serotipo 4",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "PCR/Serología",
    },
    {
        "agente_codigo": "dengue-sin-serotipo",
        "evento_nombre": "Dengue",
        "campo_busqueda": "CLASIFICACION_MANUAL",
        "patron_busqueda": r"confirmado sin serotipo|sin serotipo",
        "campo_resultado": None,
        "valores_positivos": None,
        "metodo_deteccion_default": "PCR/Serología",
    },
]


async def seed_agentes_etiologicos(db: AsyncSession) -> None:
    """
    Crea o actualiza el catálogo de agentes etiológicos y sus configuraciones.

    Args:
        db: Sesión de base de datos async
    """
    logger.info("=" * 70)
    logger.info("SEED: Agentes Etiológicos")
    logger.info("=" * 70)

    # =========================================================================
    # 1. Crear/actualizar agentes
    # =========================================================================
    agentes_creados = 0
    agentes_actualizados = 0
    agentes_map: dict[str, AgenteEtiologico] = {}

    for agente_data in AGENTES_CATALOGO:
        codigo = agente_data["slug"]

        # Buscar existente
        stmt = select(AgenteEtiologico).where(AgenteEtiologico.slug == codigo)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Actualizar
            for key, value in agente_data.items():
                setattr(existing, key, value)
            agentes_map[codigo] = existing
            agentes_actualizados += 1
        else:
            # Crear nuevo
            agente = AgenteEtiologico(**agente_data)
            db.add(agente)
            agentes_map[codigo] = agente
            agentes_creados += 1

    await db.flush()  # Para obtener IDs

    logger.info(f"  Agentes: {agentes_creados} creados, {agentes_actualizados} actualizados")

    # =========================================================================
    # 2. Crear configuraciones de extracción
    # =========================================================================
    configs_creadas = 0
    configs_actualizadas = 0
    configs_error = 0

    # Obtener mapa de tipo_eno por nombre
    stmt = select(Enfermedad)
    result = await db.execute(stmt)
    tipo_enos = {te.nombre: te for te in result.scalars().all()}

    for config_data in EXTRACCION_CONFIGS:
        agente_codigo = config_data.pop("agente_codigo")
        evento_nombre = config_data.pop("evento_nombre")

        # Buscar agente
        agente = agentes_map.get(agente_codigo)
        if not agente:
            logger.warning(f"  ⚠ Agente no encontrado: {agente_codigo}")
            configs_error += 1
            continue

        # Buscar tipo_eno
        tipo_eno = tipo_enos.get(evento_nombre)
        if not tipo_eno:
            logger.warning(f"  ⚠ Enfermedad no encontrado: {evento_nombre}")
            configs_error += 1
            continue

        # Buscar config existente
        stmt = select(AgenteExtraccionConfig).where(
            AgenteExtraccionConfig.id_agente == agente.id,
            AgenteExtraccionConfig.id_enfermedad == tipo_eno.id,
            AgenteExtraccionConfig.campo_busqueda == config_data["campo_busqueda"],
        )
        result = await db.execute(stmt)
        existing_config = result.scalar_one_or_none()

        if existing_config:
            # Actualizar
            for key, value in config_data.items():
                setattr(existing_config, key, value)
            configs_actualizadas += 1
        else:
            # Crear nueva
            config = AgenteExtraccionConfig(
                id_agente=agente.id,
                id_enfermedad=tipo_eno.id,
                **config_data
            )
            db.add(config)
            configs_creadas += 1

    await db.commit()

    logger.info(f"  Configs: {configs_creadas} creadas, {configs_actualizadas} actualizadas, {configs_error} errores")
    logger.info("")
    logger.info("  Grupos de agentes:")
    logger.info("    - Respiratorios: VSR, Influenza A/B, Metaneumovirus, SARS-CoV-2, etc.")
    logger.info("    - Entéricos: STEC O157, Salmonella, Shigella, Rotavirus, etc.")
    logger.info("    - Vectoriales: Dengue serotipos 1-4")
    logger.info("")
    logger.info("✅ Seed de agentes etiológicos completado")
