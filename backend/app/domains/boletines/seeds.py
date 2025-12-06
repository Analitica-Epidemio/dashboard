"""
Seed de configuracion del template de boletines epidemiologicos.

Basado en el Boletin Epidemiologico Semanal de Chubut (estructura completa).

Este seed crea la configuracion singleton (id=1) con:
- static_content_template: Estructura base del boletin con todas las secciones
- event_section_template: Template repetible para cada evento seleccionado

USO DE CODIGOS EN LUGAR DE IDS:
===============================
Todos los filtros en queryParams usan CODIGOS (strings) para mayor claridad:

- evento_codigo: Codigo del tipo de evento
  Ejemplos: "uc-irag", "dengue", "diarrea-aguda", "suh"

- agente_codigo: Codigo del agente etiologico
  Ejemplos: "vsr", "influenza-a", "stec-o157", "rotavirus", "dengue-1"

- eventos_codigos: Lista de codigos de eventos (para graficos multi-evento)
  Ejemplo: ["diarrea-aguda", "suh"] para agentes entericos

- agentes_codigos: Lista de agentes a incluir en el grafico
  Ejemplo: ["vsr", "influenza-a", "influenza-b", "sars-cov-2"]

- resultado: Filtro por resultado de deteccion
  Valores: "positivo", "negativo", "indeterminado"

Query types disponibles para dynamicBlock:
==========================================
- top_enos: Top N eventos del periodo
- corredor_endemico_chart: Corredor endemico (52 semanas)
- curva_epidemiologica: Curva epidemiologica del periodo (X=semana)
  - agrupar_por: "agente" -> stacked bar por agente (Grafico N°5, N°9)
  - agrupar_por: "evento" -> stacked bar por evento
  - Filtra por evento_codigo o eventos_codigos
  - Filtra por agentes_codigos (lista de codigos)
  - Filtra por resultado ("positivo", "negativo", etc.)
  - solo_internados: true para filtrar solo internados
- distribucion_agentes: Distribucion de agentes detectados (totales, sin eje temporal)
  - Filtra por evento_codigo o eventos_codigos
  - Filtra por agentes_codigos (lista de codigos)
  - Filtra por resultado ("positivo", "negativo", etc.)
- distribucion_edad: Distribucion por grupos etarios (X=grupo_etario)
  - agrupar_por: "agente" -> stacked bar por agente (Grafico N°6)
  - agrupar_por: "evento" -> stacked bar por evento (Grafico N°4)
  - Filtra por evento_codigo o eventos_codigos
  - Filtra por agentes_codigos (lista de codigos)
  - solo_internados: true para filtrar solo internados
- distribucion_geografica: Distribucion por departamento
- insight_*: Generacion de texto descriptivo automatico

Parametro agrupar_por (en queryParams):
=======================================
- "agente": Cada agente es una serie (ej: VSR, Influenza A, etc.)
- "evento": Cada evento es una serie (ej: ETI, Neumonia, Bronquiolitis)
- Sin agrupar_por: Una sola serie con el total

Configuracion de series (en config.series):
==========================================
Cuando se usa agrupar_por, se puede customizar cada serie con:
- codigo: El codigo del agente o evento (debe coincidir con agentes_codigos o eventos_codigos)
- label: El texto a mostrar en la leyenda
- color: Color hex para la serie

Ejemplo:
  "config": {
    "series": [
      {"codigo": "vsr", "label": "VSR", "color": "#2196F3"},
      {"codigo": "influenza-a", "label": "Influenza A", "color": "#F44336"},
    ]
  }

Variables de template:
=====================
- {{ evento_codigo }}: Codigo del evento (en event_section_template)
- {{ nombre_evento_sanitario }}: Nombre legible del evento
- {{ anio_epidemiologico }}: Anio del analisis
- {{ semana_epidemiologica_actual }}: Semana final
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.boletines.models import BoletinTemplateConfig
from app.domains.boletines.seed_event_section_template import (
    crear_template_seccion_evento,
)
from app.domains.boletines.seed_static_section import crear_template_contenido_estatico

logger = logging.getLogger(__name__)


async def seed_boletin_template_config(db: AsyncSession) -> None:
    """
    Crea o actualiza la configuración del template de boletines (singleton id=1).

    Args:
        db: Sesión de base de datos async
    """
    logger.info("=" * 70)
    logger.info("SEED: Configuración de Template de Boletines")
    logger.info("=" * 70)

    # Verificar si ya existe configuración
    stmt = select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    result = await db.execute(stmt)
    existing_config = result.scalar_one_or_none()

    static_template = crear_template_contenido_estatico()
    event_template = crear_template_seccion_evento()

    if existing_config:
        logger.info("  ↻ Actualizando configuración existente (id=1)")
        existing_config.static_content_template = static_template
        existing_config.event_section_template = event_template
    else:
        logger.info("  ✚ Creando nueva configuración (id=1)")
        config = BoletinTemplateConfig(
            id=1,
            static_content_template=static_template,
            event_section_template=event_template,
        )
        db.add(config)

    await db.commit()

    # Log resumen
    static_nodes = len(static_template.get("content", []))
    event_nodes = len(event_template.get("content", []))

    logger.info("")
    logger.info("  📋 Template estático: %d nodos", static_nodes)
    logger.info("  📋 Template de evento: %d nodos", event_nodes)
    logger.info("")
    logger.info("  Secciones (basadas en Boletín Epi Chubut SE 40 2025):")
    logger.info("    1. Portada")
    logger.info("    2. Tabla N°1: ENOs más frecuentes")
    logger.info("    3. Vigilancia IRAs:")
    logger.info("       - Gráfico N°1: Corredor ETI")
    logger.info("       - Gráfico N°2: Corredor Neumonía")
    logger.info("    4. Bronquiolitis:")
    logger.info("       - Gráfico N°3: Corredor Bronquiolitis")
    logger.info("       - Gráfico N°4: ETI, Neumonía y Bronquiolitis por grupo etario")
    logger.info("    5. Virus Respiratorios en Internados:")
    logger.info("       - Gráfico N°5: Internados por IRA según agente por SE")
    logger.info("       - Gráfico N°6: Internados por IRA según agente por edad")
    logger.info("    6. Intoxicación por CO (Gráfico N°7)")
    logger.info("    7. Vigilancia de Diarreas:")
    logger.info("       - Gráfico N°8: Corredor Diarrea")
    logger.info("       - Gráfico N°9: Agentes etiológicos en Diarreas")
    logger.info("    8. SUH (Gráfico N°10)")
    logger.info("    9. Análisis por CasoEpidemiologico (placeholder para loop)")
    logger.info("   10. Anexos, Metodología, Material de Consulta")
    logger.info("")
    logger.info("✅ Configuración de boletines guardada")
