"""
Seed del registro singleton BoletinTemplateConfig(id=1).

Crea la configuración base del template de boletines con:
- static_content_template: TipTap JSON basado en el Boletín Epidemiológico
  Semanal de Chubut SE 40 2025.
- event_section_template: TipTap JSON con template para cada evento en el loop.
- boletin_metadata: Datos estructurados (institución, autoridades, etc.)

Los blockType/queryType deben coincidir con las definiciones en el frontend:
- MAIN_BLOCKS: top_enos, corredor_evento_especifico, curva_por_agente, etc.
- EVENT_BLOCKS: corredor_loop, curva_loop, edad_loop, agentes_loop, etc.

Las variableKey deben coincidir con VARIABLE_META en variable-node.tsx:
- Base: anio_epidemiologico, semana_epidemiologica_actual, etc.
- Event: nombre_evento_sanitario, descripcion_tendencia_casos, etc.
"""

import logging

from sqlalchemy.orm import Session
from sqlmodel import select

from app.domains.boletines.models import BoletinTemplateConfig

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS para construir nodos TipTap
# ═══════════════════════════════════════════════════════════════════════════════


def _heading(level: int, text: str) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _paragraph(text: str) -> dict:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def _paragraph_with_variables(*parts: dict | str) -> dict:
    """Build a paragraph mixing text and variableNode nodes."""
    content = []
    for part in parts:
        if isinstance(part, str):
            if part:
                content.append({"type": "text", "text": part})
        else:
            content.append(part)
    return {"type": "paragraph", "content": content}


def _variable(key: str) -> dict:
    return {"type": "variableNode", "attrs": {"variableKey": key}}


def _dynamic_block(
    block_id: str,
    block_type: str,
    query_type: str,
    render_type: str = "chart",
    query_params: dict | None = None,
    config: dict | None = None,
    is_in_event_loop: bool = False,
) -> dict:
    return {
        "type": "dynamicBlock",
        "attrs": {
            "blockId": block_id,
            "blockType": block_type,
            "queryType": query_type,
            "renderType": render_type,
            "queryParams": query_params or {},
            "config": config or {},
            "isInEventLoop": is_in_event_loop,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE ESTÁTICO - Estructura base del boletín
# Basado en Boletín Epidemiológico Semanal de Chubut SE 40 2025
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_STATIC_CONTENT: dict = {
    "type": "doc",
    "content": [
        # ── PORTADA ──────────────────────────────────────────────────────────
        _heading(1, "Boletín Epidemiológico Semanal"),
        _paragraph_with_variables(
            "Provincia del Chubut — Semana Epidemiológica ",
            _variable("semana_epidemiologica_actual"),
            " / ",
            _variable("anio_epidemiologico"),
        ),
        _paragraph_with_variables(
            "Período: ",
            _variable("fecha_inicio_semana_epidemiologica"),
            " al ",
            _variable("fecha_fin_semana_epidemiologica"),
        ),
        # ── SECCIÓN 1: ENOs FRECUENTES ───────────────────────────────────────
        _heading(2, "Eventos de Notificación Obligatoria (ENOs)"),
        _paragraph_with_variables(
            "Casos confirmados notificados en SNVS 2.0 más frecuentes. ",
            "SE ",
            _variable("semana_epidemiologica_inicio"),
            " a SE ",
            _variable("semana_epidemiologica_actual"),
            ", ",
            _variable("anio_epidemiologico"),
            ".",
        ),
        _dynamic_block(
            block_id="tabla_top_enos",
            block_type="top_enos",
            query_type="top_enos",
            render_type="table",
            query_params={"limit": 10},
            config={
                "titulo": "Tabla N°1. Casos confirmados notificados en SNVS 2.0 "
                "más frecuentes",
            },
        ),
        # ── SECCIÓN 2: IRA (ETI + NEUMONÍA) ─────────────────────────────────
        _heading(2, "Vigilancia de Infecciones Respiratorias Agudas"),
        _paragraph(
            "Enfermedad Tipo Influenza (ETI) y Neumonía — datos de vigilancia "
            "clínica ambulatoria (CLI_P26)."
        ),
        _dynamic_block(
            block_id="corredor_eti",
            block_type="corredor_evento_especifico",
            query_type="corredor_endemico_chart",
            render_type="chart",
            query_params={"periodo": "anual", "tipo_evento_nombre": "ETI"},
            config={
                "titulo": "Gráfico N°1. Corredor endémico semanal de "
                "Enfermedad Tipo Influenza (ETI). Provincia del Chubut",
                "height": 400,
            },
        ),
        _dynamic_block(
            block_id="corredor_neumonia",
            block_type="corredor_evento_especifico",
            query_type="corredor_endemico_chart",
            render_type="chart",
            query_params={"periodo": "anual", "tipo_evento_nombre": "Neumon"},
            config={
                "titulo": "Gráfico N°2. Corredor endémico semanal de Neumonía. "
                "Provincia del Chubut",
                "height": 400,
            },
        ),
        # ── SECCIÓN 3: BRONQUIOLITIS ────────────────────────────────────────
        _heading(2, "Bronquiolitis"),
        _dynamic_block(
            block_id="corredor_bronquiolitis",
            block_type="corredor_evento_especifico",
            query_type="corredor_endemico_chart",
            render_type="chart",
            query_params={
                "periodo": "anual",
                "tipo_evento_nombre": "Bronquiolitis",
            },
            config={
                "titulo": "Gráfico N°3. Corredor endémico semanal de "
                "Bronquiolitis. Provincia del Chubut",
                "height": 400,
            },
        ),
        _dynamic_block(
            block_id="ira_por_edad",
            block_type="edad_comparar_eventos",
            query_type="distribucion_edad",
            render_type="chart",
            query_params={
                "agrupar_por": "evento",
                "eventos": ["ETI", "Neumonía", "Bronquiolitis"],
            },
            config={
                "titulo": "Gráfico N°4. Casos de ETI, Neumonía y Bronquiolitis "
                "por grupo etario. Provincia del Chubut",
                "height": 400,
                "chart_type": "stacked_bar",
                "show_legend": True,
            },
        ),
        # ── SECCIÓN 4: VIRUS RESPIRATORIOS EN INTERNADOS ────────────────────
        _heading(2, "Vigilancia de Virus Respiratorios en Internados y/o Fallecidos por IRA"),
        _paragraph(
            "Distribución de agentes virales detectados en pacientes internados "
            "por IRA. Fuente: vigilancia nominal (NOM_P26_VR)."
        ),
        _dynamic_block(
            block_id="virus_resp_semana",
            block_type="curva_por_agente",
            query_type="curva_epidemiologica",
            render_type="chart",
            query_params={
                "agrupar_por": "agente",
                "resultado": "positivo",
                "agrupacion": "respiratorio",
            },
            config={
                "titulo": "Gráfico N°5. Casos de internados por IRA según "
                "agente viral detectado por semana epidemiológica. "
                "Provincia del Chubut",
                "height": 400,
                "chart_type": "stacked_bar",
                "show_legend": True,
            },
        ),
        _dynamic_block(
            block_id="virus_resp_edad",
            block_type="edad_por_agente",
            query_type="distribucion_edad",
            render_type="chart",
            query_params={
                "agrupar_por": "agente",
                "resultado": "positivo",
                "agrupacion": "respiratorio",
            },
            config={
                "titulo": "Gráfico N°6. Casos de internado por IRA según "
                "agente viral detectado por grupos de edad. "
                "Provincia del Chubut",
                "height": 400,
                "chart_type": "stacked_bar",
                "show_legend": True,
            },
        ),
        # ── SECCIÓN 5: OCUPACIÓN HOSPITALARIA ───────────────────────────────
        _heading(2, "Ocupación Hospitalaria por IRA"),
        _paragraph(
            "Datos de dotación y ocupación de camas por IRA en establecimientos "
            "de la provincia. Fuente: CLI_P26_INT."
        ),
        # ── SECCIÓN 6: INTOXICACIÓN POR CO ──────────────────────────────────
        _heading(2, "Intoxicación por Monóxido de Carbono (CO)"),
        _dynamic_block(
            block_id="casos_co",
            block_type="curva_evento_especifico",
            query_type="curva_epidemiologica",
            render_type="chart",
            query_params={"tipo_evento_nombre": "Intoxicación por CO"},
            config={
                "titulo": "Gráfico N°7. Casos confirmados de intoxicación "
                "por monóxido de carbono",
                "height": 400,
                "chart_type": "bar",
            },
        ),
        # ── SECCIÓN 7: DIARREAS ─────────────────────────────────────────────
        _heading(2, "Vigilancia de Diarrea"),
        _dynamic_block(
            block_id="corredor_diarrea",
            block_type="corredor_evento_especifico",
            query_type="corredor_endemico_chart",
            render_type="chart",
            query_params={"periodo": "anual", "tipo_evento_nombre": "Diarrea"},
            config={
                "titulo": "Gráfico N°8. Corredor endémico semanal de Diarrea. "
                "Provincia del Chubut",
                "height": 400,
            },
        ),
        _dynamic_block(
            block_id="agentes_diarrea_semana",
            block_type="curva_por_agente",
            query_type="curva_epidemiologica",
            render_type="chart",
            query_params={
                "agrupar_por": "agente",
                "resultado": "positivo",
                "agrupacion": "enterico",
            },
            config={
                "titulo": "Gráfico N°9. Distribución de agentes etiológicos "
                "en Diarreas Agudas según semana epidemiológica. "
                "Provincia del Chubut",
                "height": 400,
                "chart_type": "stacked_bar",
                "show_legend": True,
            },
        ),
        # ── SECCIÓN 8: SUH ──────────────────────────────────────────────────
        _heading(2, "Síndrome Urémico Hemolítico (SUH)"),
        _dynamic_block(
            block_id="suh_serie_historica",
            block_type="curva_evento_especifico",
            query_type="curva_epidemiologica",
            render_type="chart",
            query_params={
                "tipo_evento_nombre": "SUH",
                "rango_temporal": "historico_desde_2014",
            },
            config={
                "titulo": "Gráfico N°10. Distribución de Casos de SUH según "
                "año de consulta. Provincia del Chubut. Período 2014-actual",
                "height": 400,
                "chart_type": "bar",
            },
        ),
        # ── EVENTOS SELECCIONADOS (LOOP) ─────────────────────────────────────
        _heading(2, "Otros eventos bajo vigilancia"),
        _paragraph(
            "Los siguientes eventos se generan automáticamente a partir de "
            "los eventos seleccionados al crear el boletín."
        ),
        {"type": "selectedEventsPlaceholder"},
        # ── METODOLOGÍA ──────────────────────────────────────────────────────
        _heading(2, "Metodología"),
        _paragraph(
            "Los datos provienen del Sistema Nacional de Vigilancia de la "
            "Salud (SNVS 2.0). Se incluyen los eventos notificados al sistema "
            "por todos los efectores de salud públicos y privados de la "
            "provincia del Chubut."
        ),
        _paragraph(
            "Las tasas se calculan sobre las proyecciones poblacionales del "
            "INDEC para el año correspondiente. Los corredores endémicos se "
            "construyen con el método de percentiles sobre los datos de los "
            "últimos 5 años, excluyendo los años de pandemia."
        ),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE DE EVENTO - Se repite por cada evento seleccionado en el loop
# Usa EVENT_BLOCKS (corredor_loop, curva_loop, edad_loop, agentes_loop, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_EVENT_SECTION_TEMPLATE: dict = {
    "type": "doc",
    "content": [
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [
                _variable("nombre_evento_sanitario"),
            ],
        },
        _paragraph_with_variables(
            _variable("descripcion_tendencia_casos"),
        ),
        _dynamic_block(
            block_id="corredor_evento_loop",
            block_type="corredor_loop",
            query_type="corredor_endemico_chart",
            render_type="chart",
            query_params={"periodo": "anual"},
            config={
                "titulo": "Corredor Endémico",
                "height": 400,
            },
            is_in_event_loop=True,
        ),
        _dynamic_block(
            block_id="curva_evento_loop",
            block_type="curva_loop",
            query_type="curva_epidemiologica",
            render_type="chart",
            query_params={},
            config={
                "titulo": "Casos por Semana Epidemiológica",
                "height": 350,
                "chart_type": "bar",
            },
            is_in_event_loop=True,
        ),
        _dynamic_block(
            block_id="edad_evento_loop",
            block_type="edad_loop",
            query_type="distribucion_edad",
            render_type="chart",
            query_params={},
            config={
                "titulo": "Distribución por Grupo Etario",
                "height": 350,
                "chart_type": "bar",
            },
            is_in_event_loop=True,
        ),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# METADATA
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_METADATA: dict = {
    "institucion": "Ministerio de Salud del Chubut",
    "autoridades": [
        {"nombre": "", "cargo": "Ministro de Salud"},
        {"nombre": "", "cargo": "Director de Epidemiología"},
    ],
    "logo_url": None,
    "periodo_default": "ultima_semana",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def seed_template_config(session: Session) -> None:
    """
    Crea el registro singleton BoletinTemplateConfig(id=1) si no existe.

    Idempotente: si ya existe, no hace nada.
    """
    stmt = select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)  # type: ignore[arg-type]
    existing = session.execute(stmt).scalar_one_or_none()

    if existing:
        logger.info("  BoletinTemplateConfig(id=1) ya existe, saltando seed")
        return

    config = BoletinTemplateConfig(
        id=1,
        static_content_template=DEFAULT_STATIC_CONTENT,
        event_section_template=DEFAULT_EVENT_SECTION_TEMPLATE,
        boletin_metadata=DEFAULT_METADATA,
    )
    session.add(config)
    session.commit()
    logger.info("  BoletinTemplateConfig(id=1) creado con template default")
