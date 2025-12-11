"""
Seed de agrupaciones de agentes etiológicos.

Crea las agrupaciones requeridas por el boletín epidemiológico:
- Virus respiratorios: Flu A, Flu B, VSR, Metaneumovirus, Adenovirus, SARS-CoV-2
- Patógenos entéricos: Rotavirus, Salmonella, Shigella, etc.

Los agentes deben existir previamente en la tabla agente_etiologico
(se crean automáticamente al procesar LAB_P26).
"""

import logging

from sqlmodel import Session, col, select

from app.domains.catalogos.agentes.agrupacion import (
    AgrupacionAgenteLink,
    AgrupacionAgentes,
)
from app.domains.catalogos.agentes.models import AgenteEtiologico, GrupoAgente

logger = logging.getLogger(__name__)


# Definición de agrupaciones por categoría
# Key: slug de la agrupación
# Value: dict con metadata y lista de nombres EXACTOS de agentes del Excel
AGRUPACIONES_RESPIRATORIAS = {
    "influenza-a": {
        "nombre": "Influenza A",
        "nombre_corto": "Flu A",
        "color": "#F44336",  # Rojo
        "orden": 1,
        "descripcion": "Agrupación de todas las variantes de Influenza A (IF, PCR, etc.)",
        "agentes": [
            "Virus Influenza A por IF o Test rápido",
            "Virus Influenza A por PCR NO estudiados por IF ni Test rápido",
            "Virus Influenza A por PCR negativos por IF o Test rápido",
        ],
    },
    "influenza-b": {
        "nombre": "Influenza B",
        "nombre_corto": "Flu B",
        "color": "#2196F3",  # Azul
        "orden": 2,
        "descripcion": "Agrupación de todas las variantes de Influenza B (IF, PCR, etc.)",
        "agentes": [
            "Virus Influenza B por IF o Test rápido",
            "Virus Influenza B por PCR NO estudiados por IF ni Test rápido",
            "Virus Influenza B por PCR negativos por IF o Test rápido",
        ],
    },
    "vsr": {
        "nombre": "Virus Sincicial Respiratorio",
        "nombre_corto": "VSR",
        "color": "#4CAF50",  # Verde
        "orden": 3,
        "descripcion": "Virus Sincicial Respiratorio",
        "agentes": [
            "Virus Sincicial Respiratorio",
        ],
    },
    "metapneumovirus": {
        "nombre": "Metapneumovirus Humano",
        "nombre_corto": "hMPV",
        "color": "#9C27B0",  # Púrpura
        "orden": 4,
        "descripcion": "Metapneumovirus humano",
        "agentes": [
            "Metapneumovirus",
        ],
    },
    "adenovirus-respiratorio": {
        "nombre": "Adenovirus Respiratorio",
        "nombre_corto": "Adenovirus",
        "color": "#FF9800",  # Naranja
        "orden": 5,
        "descripcion": "Adenovirus de vías respiratorias (no entérico)",
        "agentes": [
            "Adenovirus",
        ],
    },
    "parainfluenza": {
        "nombre": "Parainfluenza",
        "nombre_corto": "PIV",
        "color": "#00BCD4",  # Cyan
        "orden": 6,
        "descripcion": "Virus Parainfluenza tipos 1, 2, 3",
        "agentes": [
            "Virus Parainfluenza 1",
            "Virus Parainfluenza 2",
            "Virus Parainfluenza 3",
            "Virus Parainfluenza sin tipificar",
        ],
    },
    "sars-cov-2": {
        "nombre": "SARS-CoV-2",
        "nombre_corto": "COVID-19",
        "color": "#795548",  # Marrón
        "orden": 7,
        "descripcion": "Coronavirus SARS-CoV-2 (todas las técnicas)",
        "agentes": [
            "SARS CoV-2 por PCR o LAMP",
            "SARS CoV-2 por Test de antígenos",
            "SARS-COV-2 en otras situaciones",
        ],
    },
}

AGRUPACIONES_ENTERICAS = {
    "rotavirus": {
        "nombre": "Rotavirus",
        "nombre_corto": "Rotavirus",
        "color": "#E91E63",  # Rosa
        "orden": 10,
        "descripcion": "Rotavirus (diarrea viral)",
        "agentes": [
            "Rotavirus (DV)",
        ],
    },
    "norovirus": {
        "nombre": "Norovirus",
        "nombre_corto": "Norovirus",
        "color": "#673AB7",  # Violeta oscuro
        "orden": 11,
        "descripcion": "Norovirus (gastroenteritis viral)",
        "agentes": [
            "Norovirus",
        ],
    },
    "adenovirus-enterico": {
        "nombre": "Adenovirus Entérico",
        "nombre_corto": "Adenovirus (DV)",
        "color": "#FFEB3B",  # Amarillo
        "orden": 12,
        "descripcion": "Adenovirus entérico (diarrea viral)",
        "agentes": [
            "Adenovirus (DV)",
        ],
    },
    "salmonella": {
        "nombre": "Salmonella",
        "nombre_corto": "Salmonella",
        "color": "#FF5722",  # Naranja oscuro
        "orden": 20,
        "descripcion": "Todas las especies de Salmonella",
        "agentes": [
            "Salmonella spp.",
            "Salmonella enteritidis",
            "Salmonella newport",
            "Salmonella typhimurium",
        ],
    },
    "shigella": {
        "nombre": "Shigella",
        "nombre_corto": "Shigella",
        "color": "#3F51B5",  # Índigo
        "orden": 21,
        "descripcion": "Todas las especies de Shigella",
        "agentes": [
            "Shigella spp.",
            "Shigella flexneri",
            "Shigella flexneri 1",
            "Shigella flexneri 2",
            "Shigella sonnei",
            "Shigella boydii",
            "Shigella dysenteriae",
        ],
    },
    "campylobacter": {
        "nombre": "Campylobacter",
        "nombre_corto": "Campylobacter",
        "color": "#009688",  # Teal
        "orden": 22,
        "descripcion": "Todas las especies de Campylobacter",
        "agentes": [
            "Campylobacter sp.",
            "Campylobacter jejuni",
            "Campylobacter coli",
        ],
    },
    "stec": {
        "nombre": "STEC (E. coli productora de toxina Shiga)",
        "nombre_corto": "STEC",
        "color": "#8BC34A",  # Verde claro
        "orden": 23,
        "descripcion": "E. coli productora de toxina Shiga (incluye O157)",
        "agentes": [
            "Histórico - STEC O157",
            "Histórico - STEC no O157",
            "Tamizaje de E. coli enteroagregativo (EAEC)",
            "Tamizaje de E. coli enteroinvasivo (EIEC)",
            "Tamizaje de E. coli enteropatógeno (EPEC)",
            "Tamizaje de E. coli enterotoxigénico (ETEC)",
        ],
    },
}


def seed_agrupaciones(session: Session, dry_run: bool = False) -> dict:
    """
    Crea o actualiza las agrupaciones de agentes.

    Args:
        session: Sesión de base de datos
        dry_run: Si True, no guarda cambios (solo reporta)

    Returns:
        Dict con estadísticas de la operación
    """
    agrupaciones_creadas = 0
    agrupaciones_actualizadas = 0
    agentes_vinculados = 0
    agentes_no_encontrados: list[str] = []

    todas_agrupaciones = {
        **{
            slug: {**data, "categoria": GrupoAgente.RESPIRATORIO}
            for slug, data in AGRUPACIONES_RESPIRATORIAS.items()
        },
        **{
            slug: {**data, "categoria": GrupoAgente.ENTERICO}
            for slug, data in AGRUPACIONES_ENTERICAS.items()
        },
    }

    for slug, config in todas_agrupaciones.items():
        agentes_nombres = config.pop("agentes")
        categoria = config.pop("categoria")

        # Buscar o crear agrupación
        stmt = select(AgrupacionAgentes).where(col(AgrupacionAgentes.slug) == slug)
        agrupacion = session.execute(stmt).scalars().first()

        if agrupacion:
            # Actualizar campos
            for key, value in config.items():
                setattr(agrupacion, key, value)
            agrupacion.categoria = categoria
            agrupaciones_actualizadas += 1
            logger.info(f"✏️ Agrupación actualizada: {slug}")
        else:
            agrupacion = AgrupacionAgentes(
                slug=slug,
                categoria=categoria,
                **config,
            )
            session.add(agrupacion)
            agrupaciones_creadas += 1
            logger.info(f"➕ Agrupación creada: {slug}")

        if not dry_run:
            session.flush()

        # Vincular agentes
        for nombre_agente in agentes_nombres:
            stmt = select(AgenteEtiologico).where(
                col(AgenteEtiologico.nombre) == nombre_agente
            )
            agente = session.execute(stmt).scalars().first()

            if agente:
                # Verificar si ya está vinculado
                link_stmt = select(AgrupacionAgenteLink).where(
                    col(AgrupacionAgenteLink.agrupacion_id) == agrupacion.id,
                    col(AgrupacionAgenteLink.agente_id) == agente.id,
                )
                existing_link = session.execute(link_stmt).scalars().first()

                if not existing_link and not dry_run:
                    link = AgrupacionAgenteLink(
                        agrupacion_id=agrupacion.id,
                        agente_id=agente.id,
                    )
                    session.add(link)
                    agentes_vinculados += 1
                    logger.debug(f"  🔗 {nombre_agente}")
            else:
                agentes_no_encontrados.append(nombre_agente)
                logger.warning(f"  ⚠️ Agente no encontrado: {nombre_agente}")

    if not dry_run:
        session.commit()

    stats = {
        "agrupaciones_creadas": agrupaciones_creadas,
        "agrupaciones_actualizadas": agrupaciones_actualizadas,
        "agentes_vinculados": agentes_vinculados,
        "agentes_no_encontrados": agentes_no_encontrados,
    }
    logger.info(f"📊 Seed completado: {stats}")
    return stats


def get_agente_ids_for_agrupacion(session: Session, slug: str) -> list[int]:
    """
    Obtiene los IDs de agentes para una agrupación.

    Útil para el sistema de métricas que necesita resolver
    una agrupación a sus agentes individuales.

    Args:
        session: Sesión de base de datos
        slug: Slug de la agrupación (ej: "influenza-a")

    Returns:
        Lista de IDs de agentes, vacía si no existe la agrupación
    """
    stmt = select(AgrupacionAgentes).where(
        col(AgrupacionAgentes.slug) == slug,
        col(AgrupacionAgentes.activo).is_(True),
    )
    agrupacion = session.execute(stmt).scalars().first()

    if not agrupacion:
        return []

    # Obtener IDs via la tabla de enlace
    link_stmt = select(AgrupacionAgenteLink.agente_id).where(
        col(AgrupacionAgenteLink.agrupacion_id) == agrupacion.id
    )
    return list(session.execute(link_stmt).scalars().all())


def list_agrupaciones_by_categoria(
    session: Session,
    categoria: str,
) -> list[AgrupacionAgentes]:
    """
    Lista agrupaciones por categoría funcional.

    Args:
        session: Sesión de base de datos
        categoria: "respiratorio", "enterico", etc.

    Returns:
        Lista de agrupaciones ordenadas
    """
    stmt = (
        select(AgrupacionAgentes)
        .where(
            col(AgrupacionAgentes.categoria) == categoria,
            col(AgrupacionAgentes.activo).is_(True),
        )
        .order_by(col(AgrupacionAgentes.orden))
    )
    return list(session.execute(stmt).scalars().all())
