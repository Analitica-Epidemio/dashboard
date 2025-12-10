"""
Generate draft boletin - genera borrador de boletín basado en configuración DB.

REFACTORIZADO: Sistema configurable con queries y renderers reutilizables.
"""

import json
import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.api.v1.boletines.schemas import (
    BoletinMetadata,
    GenerateDraftRequest,
    GenerateDraftResponse,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import (
    BoletinInstance,
    BoletinSeccion,
)
from app.domains.boletines.services.block_renderer import BoletinBlockRenderer
from app.domains.boletines.services.query import BoletinQueryService

logger = logging.getLogger(__name__)


async def generate_draft(
    request: GenerateDraftRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[GenerateDraftResponse]:
    """
    Genera un borrador de boletín epidemiológico usando configuración desde DB.

    El template usa formato unificado: bloques dinámicos embebidos en
    static_content_template como nodos TipTap tipo 'dynamicBlock'.

    Proceso:
    1. Cargar BoletinTemplateConfig (singleton)
    2. Construir contexto con variables Jinja2
    3. Procesar template: reemplazar variables y ejecutar bloques dinámicos
    4. Validar contenido generado
    5. Crear BoletinInstance en DB

    Args:
        request: Parámetros de generación (semana, año, eventos)
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        SuccessResponse con boletin_instance_id, content y warnings
    """

    logger.info(
        f"Generando borrador de boletín - SE {request.semana}/{request.anio}, "
        f"{len(request.eventos_seleccionados)} eventos"
    )

    try:
        # 1. Cargar secciones y bloques activos desde DB
        secciones = await get_secciones_activas(db)
        if not secciones:
            logger.warning("No hay secciones configuradas, generando boletín básico")

        # 2. Construir contexto Jinja2
        context = build_context(request)

        # 3. Generar contenido desde secciones y bloques
        final_content, validation_warnings = await generate_content_from_secciones(
            db=db,
            secciones=secciones,
            request=request,
            context=context,
        )

        # 7. Guardar instancia
        boletin = await save_boletin_instance(
            db=db,
            request=request,
            content=final_content,
            context=context,
            current_user=current_user,
        )

        logger.info(f"✓ Boletín generado exitosamente: ID {boletin.id}")

        # 8. Preparar metadata
        metadata = BoletinMetadata(
            periodo_analisis={
                "semana_inicio": context["semana_inicio"],
                "semana_fin": context["semana"],
                "anio": context["anio"],
                "fecha_inicio": context["fecha_inicio"],
                "fecha_fin": context["fecha_fin"],
                "num_semanas": request.num_semanas,
            },
            eventos_incluidos=[
                {"tipo_eno_id": e.tipo_eno_id, "incluir_charts": e.incluir_charts}
                for e in request.eventos_seleccionados
            ],
            fecha_generacion=datetime.now(timezone.utc),
        )

        # Verificar que el ID del boletín no sea None
        if boletin.id is None:
            raise HTTPException(
                status_code=500, detail="Error: boletín guardado sin ID"
            )

        return SuccessResponse(
            data=GenerateDraftResponse(
                boletin_instance_id=boletin.id,
                content=json.dumps(final_content),  # TipTap JSON como string
                metadata=metadata,
                warnings=validation_warnings,
            )
        )

    except Exception as e:
        logger.error(f"Error generando borrador: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error al generar borrador: {str(e)}"
        )


# ==================== HELPER FUNCTIONS ====================


def _calculate_previous_period(
    fecha_inicio: "date", fecha_fin: "date"
) -> tuple["date", "date"]:
    """
    Calcula el período anterior equivalente al período dado.

    Por ejemplo, si el período actual es de 4 semanas (28 días),
    el período anterior serán las 4 semanas inmediatamente anteriores.

    Args:
        fecha_inicio: Fecha inicio del período actual
        fecha_fin: Fecha fin del período actual

    Returns:
        Tuple (fecha_inicio_anterior, fecha_fin_anterior)
    """
    from datetime import timedelta

    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=dias_periodo - 1)

    return (fecha_inicio_anterior, fecha_fin_anterior)


async def process_unified_template(
    db: AsyncSession,
    template: dict[str, Any],
    request: "GenerateDraftRequest",
    context: dict[str, Any],
    event_template: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], list[str]]:
    """
    Procesa un template en formato unificado (bloques embebidos en TipTap).

    Recorre el documento TipTap y reemplaza cada nodo 'dynamicBlock'
    con el contenido renderizado correspondiente.

    También maneja `selectedEventsPlaceholder`: lo reemplaza con secciones
    renderizadas para cada evento seleccionado usando `event_template`.

    Args:
        db: Sesión de base de datos
        template: TipTap JSON con bloques embebidos
        request: Parámetros de generación
        context: Contexto con variables
        event_template: Template de sección de evento (se repite por cada evento)

    Returns:
        Tuple de (contenido procesado, warnings)
    """
    from copy import deepcopy

    query_service = BoletinQueryService()
    renderer = BoletinBlockRenderer()
    warnings = []

    logger.info("=" * 60)
    logger.info("PROCESANDO TEMPLATE UNIFICADO")
    logger.info(f"  - Contexto disponible: {list(context.keys())}")
    logger.info(
        f"  - CasoEpidemiologicos seleccionados: {len(request.eventos_seleccionados)}"
    )
    logger.info(f"  - Event template presente: {event_template is not None}")
    logger.info("=" * 60)

    # Trabajar con una copia
    result = deepcopy(template)
    new_content = []

    total_nodes = len(result.get("content", []))
    for idx, node in enumerate(result.get("content", [])):
        node_type = node.get("type")

        logger.debug(f"[{idx + 1}/{total_nodes}] Procesando nodo tipo: {node_type}")

        if node_type == "selectedEventsPlaceholder":
            # ════════════════════════════════════════════════════════════════
            # PLACEHOLDER: Expandir template de evento para cada evento seleccionado
            # ════════════════════════════════════════════════════════════════
            logger.info("─" * 50)
            logger.info("📋 ENCONTRADO: selectedEventsPlaceholder")

            if not event_template:
                logger.warning(
                    "⚠️  No hay event_template definido - saltando placeholder"
                )
                new_content.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "⚠️ No hay template de evento configurado",
                            }
                        ],
                    }
                )
                warnings.append("No hay template de evento configurado")
                continue

            if not request.eventos_seleccionados:
                logger.warning("⚠️  No hay eventos seleccionados - saltando placeholder")
                new_content.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "ℹ️ No se seleccionaron eventos para incluir",
                            }
                        ],
                    }
                )
                continue

            logger.info(
                f"🔄 Expandiendo placeholder para {len(request.eventos_seleccionados)} eventos"
            )

            for evento_idx, evento in enumerate(request.eventos_seleccionados):
                logger.info(
                    f"  [{evento_idx + 1}/{len(request.eventos_seleccionados)}] Procesando evento ID: {evento.tipo_eno_id}"
                )
                try:
                    # Obtener info del evento
                    evento_info = await get_evento_info(db, evento.tipo_eno_id)
                    if not evento_info:
                        logger.warning(
                            f"    ⚠️ CasoEpidemiologico {evento.tipo_eno_id} no encontrado en DB"
                        )
                        warnings.append(
                            f"CasoEpidemiologico {evento.tipo_eno_id} no encontrado"
                        )
                        new_content.append(
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"⚠️ CasoEpidemiologico ID {evento.tipo_eno_id} no encontrado",
                                    }
                                ],
                            }
                        )
                        continue

                    logger.info(
                        f"    ✓ CasoEpidemiologico: {evento_info.get('nombre')} (código: {evento_info.get('codigo')})"
                    )

                    # Crear contexto específico para este evento
                    evento_context = context.copy()
                    evento_context.update(
                        {
                            # Variables con nombres explícitos para templates
                            "nombre_evento_sanitario": evento_info.get(
                                "nombre", f"CasoEpidemiologico {evento.tipo_eno_id}"
                            ),
                            "codigo_evento_snvs": evento_info.get(
                                "codigo", str(evento.tipo_eno_id)
                            ),
                            # Variables internas (compatibilidad)
                            "tipo_evento": evento_info.get(
                                "nombre", f"CasoEpidemiologico {evento.tipo_eno_id}"
                            ),
                            "evento_codigo": evento_info.get(
                                "codigo", str(evento.tipo_eno_id)
                            ),
                            "evento_id": evento.tipo_eno_id,
                        }
                    )

                    # Obtener análisis de tendencia para este evento
                    logger.info("    📊 Analizando tendencia...")
                    trend_analysis = await analyze_event_trend(
                        db=db,
                        query_service=query_service,
                        evento_id=evento.tipo_eno_id,
                        context=evento_context,
                    )
                    evento_context.update(trend_analysis)
                    logger.info(
                        f"    ✓ Tendencia: {trend_analysis.get('tendencia_tipo', 'N/A')} ({trend_analysis.get('casos_semana_actual', 0)} casos)"
                    )

                    # Log de variables disponibles para este evento
                    logger.info("    📝 Variables de evento disponibles:")
                    for key in [
                        "nombre_evento_sanitario",
                        "codigo_evento_snvs",
                        "descripcion_tendencia_casos",
                        "casos_semana_actual",
                        "casos_semana_anterior",
                        "porcentaje_cambio",
                    ]:
                        val = evento_context.get(key, "[NO DEFINIDA]")
                        logger.info(
                            f"       - {key}: {str(val)[:60]}{'...' if len(str(val)) > 60 else ''}"
                        )

                    # Procesar template de evento recursivamente
                    logger.info("    🔧 Procesando template de evento...")
                    event_content, event_warnings = await process_event_template(
                        db=db,
                        event_template=event_template,
                        evento_context=evento_context,
                        query_service=query_service,
                        renderer=renderer,
                    )

                    if event_content:
                        logger.info(
                            f"    ✓ Template procesado: {len(event_content)} nodos generados"
                        )
                        new_content.extend(event_content)
                    else:
                        logger.warning("    ⚠️ Template no generó contenido")
                        new_content.append(
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"ℹ️ Sin datos para {evento_info.get('nombre')}",
                                    }
                                ],
                            }
                        )

                    if event_warnings:
                        logger.warning(f"    ⚠️ Warnings: {event_warnings}")
                    warnings.extend(event_warnings)

                except Exception as e:
                    logger.error(
                        f"    ❌ Error procesando evento {evento.tipo_eno_id}: {e}",
                        exc_info=True,
                    )
                    warnings.append(f"Error en evento {evento.tipo_eno_id}: {str(e)}")
                    new_content.append(
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"⚠️ Error procesando evento: {str(e)}",
                                }
                            ],
                        }
                    )

        elif node_type == "dynamicBlock":
            # Extraer configuración del bloque
            attrs = node.get("attrs", {})
            block_id = attrs.get("blockId", f"block_{id(node)}")
            query_type = attrs.get("queryType", "")
            render_type = attrs.get("renderType", "table")
            query_params = attrs.get("queryParams", {})
            render_config = attrs.get("config", {})

            logger.info("─" * 50)
            logger.info(f"📊 BLOQUE DINÁMICO: {block_id}")
            logger.info(f"   Query: {query_type}, Render: {render_type}")

            try:
                # Actualizar context con tipo_evento del bloque si aplica
                block_context = context.copy()
                if "tipo_evento" in query_params:
                    block_context["tipo_evento"] = query_params["tipo_evento"]
                if "num_semanas" in query_params:
                    block_context["num_semanas"] = query_params["num_semanas"]

                # Merge render_config into query_params so execute_query can access chart_type, series, etc.
                merged_query_params = query_params.copy()
                merged_query_params["config"] = render_config

                # Ejecutar query
                logger.info("   Ejecutando query...")
                data = await execute_query(
                    db=db,
                    query_service=query_service,
                    query_type=query_type,
                    query_params=merged_query_params,
                    context=block_context,
                )

                # Verificar si hay data
                if not data or (isinstance(data, (list, dict)) and len(data) == 0):
                    logger.warning("   ⚠️ Query no retornó datos")
                    titulo = render_config.get("titulo", block_id)
                    # Reemplazar variables en el título
                    titulo = replace_template_variables_in_string(titulo, block_context)
                    new_content.append(
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ℹ️ {titulo}: Sin datos disponibles para el período seleccionado",
                                }
                            ],
                        }
                    )
                    continue

                logger.info(f"   ✓ Query retornó datos: {type(data).__name__}")

                # Renderizar bloque
                rendered = render_block(
                    renderer=renderer,
                    render_type=render_type,
                    data=data,
                    render_config=render_config,
                    context=block_context,
                )

                # Extraer contenido del bloque renderizado y agregar al documento
                if isinstance(rendered, dict) and "content" in rendered:
                    logger.info(f"   ✓ Renderizado: {len(rendered['content'])} nodos")
                    new_content.extend(rendered["content"])
                elif isinstance(rendered, dict):
                    logger.info("   ✓ Renderizado como nodo único")
                    new_content.append(rendered)
                else:
                    logger.warning("   ⚠️ Bloque no generó contenido válido")
                    warnings.append(f"Bloque '{block_id}' no generó contenido válido")

            except Exception as e:
                logger.error(
                    f"   ❌ Error procesando bloque '{block_id}': {e}", exc_info=True
                )
                warnings.append(f"Error en bloque '{block_id}': {str(e)}")
                # Agregar un placeholder de error
                new_content.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"⚠️ Error en {block_id}: {str(e)}"}
                        ],
                    }
                )
        else:
            # Nodo normal: aplicar reemplazo de variables si es texto
            processed_node = replace_template_variables_in_node(
                node, context, log_replacements=True
            )
            new_content.append(processed_node)

    logger.info("=" * 60)
    logger.info(f"✓ TEMPLATE PROCESADO: {len(new_content)} nodos finales")
    if warnings:
        logger.warning(f"⚠️ Warnings totales: {len(warnings)}")
    logger.info("=" * 60)

    result["content"] = new_content
    return result, warnings


async def get_evento_info(db: AsyncSession, evento_id: int) -> Optional[dict[str, Any]]:
    """
    Obtiene información de un evento/tipo ENO.

    Args:
        db: Sesión de base de datos
        evento_id: ID del tipo de ENO

    Returns:
        Dict con nombre, código, etc. del evento
    """
    from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad

    stmt = select(Enfermedad).where(col(Enfermedad.id) == evento_id)
    result = await db.execute(stmt)
    tipo_eno = result.scalar_one_or_none()

    if tipo_eno:
        return {
            "id": tipo_eno.id,
            "nombre": tipo_eno.nombre,
            "codigo": tipo_eno.slug if hasattr(tipo_eno, "slug") else str(tipo_eno.id),
        }
    return None


async def analyze_event_trend(
    db: AsyncSession,
    query_service: BoletinQueryService,
    evento_id: int,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Analiza la tendencia de un evento comparando semana actual vs anterior.

    Genera texto descriptivo como:
    - "Se observa un incremento del 25% respecto a la semana anterior"
    - "Los casos disminuyeron un 10% comparado con SE {{ semana_anterior }}"

    Args:
        db: Sesión de base de datos
        query_service: Servicio de queries
        evento_id: ID del evento
        context: Contexto con semana, año, etc.

    Returns:
        Dict con variables de tendencia para usar en templates
    """
    try:
        # Obtener casos de semana actual
        casos_actual = await query_service.consultar_casos_semana(
            db=db, evento_id=evento_id, semana=context["semana"], anio=context["anio"]
        )

        # Calcular semana anterior
        semana_anterior = context["semana"] - 1
        anio_anterior = context["anio"]
        if semana_anterior < 1:
            semana_anterior = 52
            anio_anterior -= 1

        # Obtener casos de semana anterior
        casos_anterior = await query_service.consultar_casos_semana(
            db=db, evento_id=evento_id, semana=semana_anterior, anio=anio_anterior
        )

        # Calcular diferencia y porcentaje
        diferencia = casos_actual - casos_anterior
        if casos_anterior > 0:
            porcentaje_cambio = ((casos_actual - casos_anterior) / casos_anterior) * 100
        else:
            porcentaje_cambio = 100 if casos_actual > 0 else 0

        # Generar texto descriptivo
        if abs(porcentaje_cambio) < 5:
            tendencia_texto = f"Se mantiene estable respecto a la SE {semana_anterior} ({casos_anterior} casos)"
            tendencia_tipo = "estable"
        elif porcentaje_cambio > 0:
            tendencia_texto = (
                f"Se observa un incremento del {abs(porcentaje_cambio):.0f}% respecto a la "
                f"SE {semana_anterior} ({casos_anterior} → {casos_actual} casos)"
            )
            tendencia_tipo = "aumento"
        else:
            tendencia_texto = (
                f"Se observa una disminución del {abs(porcentaje_cambio):.0f}% respecto a la "
                f"SE {semana_anterior} ({casos_anterior} → {casos_actual} casos)"
            )
            tendencia_tipo = "descenso"

        return {
            "casos_semana_actual": casos_actual,
            "casos_semana_anterior": casos_anterior,
            "semana_anterior": semana_anterior,
            "anio_semana_anterior": anio_anterior,
            "diferencia_casos": diferencia,
            "porcentaje_cambio": porcentaje_cambio,
            # Variable con nombre explícito para templates
            "descripcion_tendencia_casos": tendencia_texto,
            # Mantener compatibilidad
            "tendencia_texto": tendencia_texto,
            "tendencia_tipo": tendencia_tipo,
        }

    except Exception as e:
        logger.warning(f"Error analizando tendencia para evento {evento_id}: {e}")
        return {
            "casos_semana_actual": 0,
            "casos_semana_anterior": 0,
            "descripcion_tendencia_casos": "Datos de tendencia no disponibles",
            "tendencia_texto": "Datos de tendencia no disponibles",
            "tendencia_tipo": "desconocido",
        }


async def process_event_template(
    db: AsyncSession,
    event_template: dict[str, Any],
    evento_context: dict[str, Any],
    query_service: BoletinQueryService,
    renderer: BoletinBlockRenderer,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Procesa el template de un evento específico.

    Args:
        db: Sesión de base de datos
        event_template: Template TipTap de la sección de evento
        evento_context: Contexto con variables del evento
        query_service: Servicio de queries
        renderer: Renderer de bloques

    Returns:
        Tuple de (lista de nodos procesados, warnings)
    """
    from copy import deepcopy

    warnings = []
    processed_nodes = []

    template_content = event_template.get("content", [])
    evento_nombre = evento_context.get("nombre_evento_sanitario", "CasoEpidemiologico")

    logger.info(
        f"      📄 Procesando {len(template_content)} nodos del template para '{evento_nombre}'"
    )

    for node_idx, node in enumerate(template_content):
        node_type = node.get("type")
        logger.debug(
            f"      [{node_idx + 1}/{len(template_content)}] Nodo tipo: {node_type}"
        )

        if node_type == "dynamicBlock":
            attrs = node.get("attrs", {})
            block_id = attrs.get("blockId", "")
            query_type = attrs.get("queryType", "")
            render_type = attrs.get("renderType", "table")
            query_params = attrs.get("queryParams", {})
            render_config = attrs.get("config", {})

            # Reemplazar variables en block_id y config
            block_id = replace_template_variables_in_string(block_id, evento_context)
            render_config = replace_template_variables_in_node(
                render_config, evento_context
            )

            logger.info(f"      📊 Bloque dinámico: {block_id} (query: {query_type})")

            # Agregar evento_id a query_params y merge render_config
            query_params = query_params.copy()
            query_params["tipo_evento"] = evento_context.get("tipo_evento")
            query_params["evento_id"] = evento_context.get("evento_id")
            query_params["config"] = (
                render_config  # Include config for chart_type, series, etc.
            )

            try:
                data = await execute_query(
                    db=db,
                    query_service=query_service,
                    query_type=query_type,
                    query_params=query_params,
                    context=evento_context,
                    evento_id=evento_context.get("evento_id"),
                )

                # Verificar si hay data
                if not data or (isinstance(data, (list, dict)) and len(data) == 0):
                    logger.warning(f"      ⚠️ Sin datos para {block_id}")
                    titulo = (
                        render_config.get("titulo", block_id)
                        if isinstance(render_config, dict)
                        else block_id
                    )
                    # Reemplazar variables Jinja2 en el título
                    titulo = replace_template_variables_in_string(
                        titulo, evento_context
                    )
                    processed_nodes.append(
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ℹ️ {titulo}: Sin datos disponibles",
                                }
                            ],
                        }
                    )
                    continue

                rendered = render_block(
                    renderer=renderer,
                    render_type=render_type,
                    data=data,
                    render_config=render_config,
                    context=evento_context,
                    evento_id=evento_context.get("evento_id"),
                )

                if isinstance(rendered, dict) and "content" in rendered:
                    logger.info(
                        f"      ✓ Bloque renderizado: {len(rendered['content'])} nodos"
                    )
                    processed_nodes.extend(rendered["content"])
                elif isinstance(rendered, dict):
                    processed_nodes.append(rendered)
                else:
                    logger.warning("      ⚠️ Bloque no generó contenido")

            except Exception as e:
                logger.error(f"      ❌ Error en bloque {block_id}: {e}", exc_info=True)
                warnings.append(f"Error en {block_id}: {str(e)}")
                processed_nodes.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"⚠️ Error en {block_id}: {str(e)}"}
                        ],
                    }
                )
        else:
            # Nodo normal - reemplazar variables
            logger.debug(
                f"      Procesando nodo {node_type} con reemplazo de variables"
            )
            processed_node = replace_template_variables_in_node(
                deepcopy(node), evento_context, log_replacements=True
            )
            processed_nodes.append(processed_node)

    logger.info(
        f"      ✓ Template de evento procesado: {len(processed_nodes)} nodos resultantes"
    )
    return processed_nodes, warnings


def replace_template_variables_in_string(text: str, context: dict[str, Any]) -> str:
    """Reemplaza variables Jinja2 en un string."""
    from jinja2 import BaseLoader, Environment

    if "{{" not in text and "{%" not in text:
        return text

    try:
        env = Environment(loader=BaseLoader(), autoescape=False)
        template = env.from_string(text)
        return template.render(**context)
    except Exception:
        return text


def replace_template_variables_in_node(
    node: dict[str, Any], context: dict[str, Any], log_replacements: bool = False
) -> dict[str, Any]:
    """
    Reemplaza variables Jinja2 en un nodo TipTap recursivamente.

    También convierte nodos `variableNode` a texto con el valor real de la variable.

    Args:
        node: Nodo TipTap
        context: Contexto con variables
        log_replacements: Si es True, loguea cada reemplazo de variable

    Returns:
        Nodo con variables reemplazadas
    """
    from copy import deepcopy

    from jinja2 import BaseLoader, Environment

    env = Environment(loader=BaseLoader(), autoescape=False)
    replacements_made = []

    def process_node(n: dict[str, Any]) -> dict[str, Any]:
        """Procesa un nodo, convirtiendo variableNode a texto."""
        if not isinstance(n, dict):
            return n

        node_type = n.get("type")

        # ═══════════════════════════════════════════════════════════════════
        # Caso especial: variableNode -> convertir a texto con valor real
        # ═══════════════════════════════════════════════════════════════════
        if node_type == "variableNode":
            attrs = n.get("attrs", {})
            variable_key = attrs.get("variableKey", "")

            # Buscar el valor en el contexto
            value = context.get(variable_key)

            if value is not None:
                # Convertir a string si no lo es
                value_str = str(value)
                replacements_made.append((variable_key, value_str[:50]))
                logger.debug(
                    f"   🔄 variableNode '{variable_key}' → '{value_str[:50]}{'...' if len(value_str) > 50 else ''}'"
                )
                return {"type": "text", "text": value_str}
            else:
                # Variable no encontrada - dejar placeholder legible
                logger.warning(
                    f"   ⚠️ variableNode '{variable_key}' NO encontrada en contexto. Claves disponibles: {list(context.keys())[:10]}..."
                )
                return {"type": "text", "text": f"[{variable_key}]"}

        # ═══════════════════════════════════════════════════════════════════
        # Nodos normales: procesar recursivamente
        # ═══════════════════════════════════════════════════════════════════
        result = {}
        for key, value in n.items():
            if key == "content" and isinstance(value, list):
                # Procesar lista de nodos hijos
                result[key] = [
                    process_node(child) if isinstance(child, dict) else child
                    for child in value
                ]
            elif key == "text" and isinstance(value, str):
                # Reemplazar variables Jinja2 en texto
                if "{{" in value or "{%" in value:
                    try:
                        template = env.from_string(value)
                        rendered = template.render(**context)
                        if rendered != value:
                            logger.debug(
                                f"   🔄 Jinja2: '{value[:30]}...' → '{rendered[:30]}...'"
                            )
                        result[key] = rendered
                    except Exception as e:
                        logger.warning(f"   ⚠️ Error Jinja2 en '{value[:30]}': {e}")
                        result[key] = value
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = process_node(value)
            elif isinstance(value, list):
                result[key] = [
                    process_node(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    processed = process_node(deepcopy(node))

    if log_replacements and replacements_made:
        logger.info(f"   📝 Variables reemplazadas: {len(replacements_made)}")

    return processed


async def get_secciones_activas(db: AsyncSession) -> list[BoletinSeccion]:
    """
    Obtiene las secciones activas con sus bloques ordenados.

    Args:
        db: Sesión de base de datos

    Returns:
        Lista de BoletinSeccion con bloques cargados
    """
    from sqlalchemy.orm import selectinload

    stmt = (
        select(BoletinSeccion)
        .where(col(BoletinSeccion.activo).is_(True))
        .options(selectinload(BoletinSeccion.bloques))  # type: ignore[arg-type]
        .order_by(col(BoletinSeccion.orden))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def generate_content_from_secciones(
    db: AsyncSession,
    secciones: list[BoletinSeccion],
    request: "GenerateDraftRequest",
    context: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Genera contenido TipTap desde las secciones y bloques configurados.

    Args:
        db: Sesión de base de datos
        secciones: Lista de secciones activas con bloques
        request: Parámetros de generación
        context: Contexto con variables Jinja2

    Returns:
        Tuple de (TipTap JSON document, warnings)
    """
    from sqlalchemy.orm import Session as SyncSession

    from app.domains.boletines.services.adapter import (
        BloqueQueryAdapter,
        BoletinContexto,
    )

    warnings: list[str] = []
    content_nodes: list[dict[str, Any]] = []

    # Título del boletín
    titulo = (
        request.titulo_custom
        or f"Boletín Epidemiológico SE {request.semana}/{request.anio}"
    )
    content_nodes.append(
        {
            "type": "heading",
            "attrs": {"level": 1},
            "content": [{"type": "text", "text": titulo}],
        }
    )

    # Subtítulo con período
    content_nodes.append(
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": f"Período: SE {context['semana_inicio']}-{context['semana']}/{context['anio']} "
                    f"({context['fecha_inicio']} al {context['fecha_fin']})",
                }
            ],
        }
    )

    # Espacio
    content_nodes.append({"type": "paragraph", "content": []})

    # Si no hay secciones, generar contenido básico
    if not secciones:
        content_nodes.append(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "No hay secciones configuradas. Configure las secciones en la base de datos.",
                    }
                ],
            }
        )
        warnings.append("No hay secciones configuradas")
        return {"type": "doc", "content": content_nodes}, warnings

    # Crear sesión síncrona con engine separado
    # No podemos usar el bind de la async session porque causa errores de greenlet
    import os

    from sqlalchemy import create_engine

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5433/epidemiologia_db",
    )
    # Asegurar que usamos driver síncrono
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    sync_engine = create_engine(DATABASE_URL)
    sync_session = SyncSession(bind=sync_engine)

    try:
        adapter = BloqueQueryAdapter(sync_session)
        bloque_contexto = BoletinContexto(
            semana_actual=context["semana"],
            anio_actual=context["anio"],
            num_semanas=context["num_semanas"],
        )

        for seccion in secciones:
            logger.info(f"📄 Procesando sección: {seccion.titulo}")

            # Título de sección
            content_nodes.append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": seccion.titulo}],
                }
            )

            # Contenido introductorio si existe
            if seccion.contenido_intro:
                intro_content = seccion.contenido_intro.get("content", [])
                content_nodes.extend(intro_content)

            # Procesar bloques activos de la sección
            bloques_activos = [b for b in seccion.bloques if b.activo]

            if not bloques_activos:
                content_nodes.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "marks": [{"type": "italic"}],
                                "text": "Sin bloques configurados para esta sección.",
                            }
                        ],
                    }
                )
                continue

            for bloque in bloques_activos:
                try:
                    logger.info(f"  📊 Procesando bloque: {bloque.slug}")

                    # Ejecutar el bloque usando el adapter (síncrono)
                    resultado = adapter.ejecutar_bloque(
                        bloque=bloque,
                        contexto=bloque_contexto,
                    )

                    # Agregar título del bloque
                    content_nodes.append(
                        {
                            "type": "heading",
                            "attrs": {"level": 3},
                            "content": [{"type": "text", "text": resultado.titulo}],
                        }
                    )

                    # Agregar contenido del bloque según tipo de visualización
                    if resultado.series and len(resultado.series) > 0:
                        # Renderizar datos como tabla simple por ahora
                        content_nodes.extend(_render_resultado_como_tiptap(resultado))
                    else:
                        content_nodes.append(
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "marks": [{"type": "italic"}],
                                        "text": "Sin datos disponibles para este bloque.",
                                    }
                                ],
                            }
                        )

                    # Espacio después del bloque
                    content_nodes.append({"type": "paragraph", "content": []})

                except Exception as e:
                    logger.error(
                        f"  ❌ Error en bloque {bloque.slug}: {e}", exc_info=True
                    )
                    warnings.append(f"Error en bloque {bloque.slug}: {str(e)}")
                    content_nodes.append(
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"⚠️ Error procesando bloque: {str(e)}",
                                }
                            ],
                        }
                    )

            # Espacio después de la sección
            content_nodes.append({"type": "paragraph", "content": []})

    finally:
        sync_session.close()
        sync_engine.dispose()

    logger.info(f"✓ Contenido generado: {len(content_nodes)} nodos")
    return {"type": "doc", "content": content_nodes}, warnings


def _render_resultado_como_tiptap(resultado: Any) -> list[dict[str, Any]]:
    """
    Renderiza un BloqueResultado como nodos TipTap.

    Genera charts (dynamicChart) o tablas según tipo_visualizacion:
    - area_chart, stacked_bar, grouped_bar, line_chart -> dynamicChart
    - table -> tabla TipTap nativa
    """
    from app.domains.boletines.services.adapter import BloqueResultado

    if not isinstance(resultado, BloqueResultado):
        return []

    tipo_viz = resultado.tipo_visualizacion

    # Tipos de visualización que son charts (uppercase)
    chart_types = {"AREA_CHART", "STACKED_BAR", "GROUPED_BAR", "LINE_CHART"}

    if tipo_viz in chart_types:
        # Renderizar como dynamicChart
        return _render_chart_resultado(resultado)
    else:
        # Renderizar como tabla
        return _render_table_resultado(resultado)


def _render_chart_resultado(resultado: Any) -> list[dict[str, Any]]:
    """
    Renderiza un BloqueResultado como nodo dynamicChart con UniversalChartSpec embebido.

    El frontend espera un spec en formato UniversalChartSpec:
    {
        id: string,
        title: string,
        type: 'line' | 'bar' | 'area' | 'pie',
        data: { type: 'bar', data: { labels: string[], datasets: Dataset[] } },
        config: { type: 'bar', config: BarChartConfig }
    }
    """
    from app.domains.boletines.services.adapter import BloqueResultado

    if not isinstance(resultado, BloqueResultado):
        return []

    logger.info(f"     🎨 Renderizando chart: {resultado.slug}")
    logger.info(f"        tipo_visualizacion: {resultado.tipo_visualizacion}")
    logger.info(f"        series: {len(resultado.series)}")
    for i, serie in enumerate(resultado.series):
        data_count = len(serie.get("data", []))
        logger.info(f"        Serie {i}: '{serie.get('serie')}' - {data_count} filas")
        if "error" in serie:
            logger.warning(f"        Serie {i} tiene error: {serie['error']}")

    nodes: list[dict[str, Any]] = []

    # Mapear tipo_visualizacion a ChartType del frontend (uppercase enum values)
    chart_type_map = {
        "AREA_CHART": "area",
        "STACKED_BAR": "bar",
        "GROUPED_BAR": "bar",
        "LINE_CHART": "line",
    }

    chart_type = chart_type_map.get(resultado.tipo_visualizacion, "bar")

    # Obtener la dimensión principal (eje X) de los metadata
    x_dimension = None
    if resultado.metadata.get("dimensiones"):
        dims = resultado.metadata["dimensiones"]
        if dims:
            x_dim = dims[0]
            x_dimension_map = {
                "SEMANA_EPIDEMIOLOGICA": "semana_epidemiologica",
                "GRUPO_ETARIO": "grupo_etario",
                "TIPO_EVENTO": "tipo_evento",
                "PROVINCIA": "provincia",
                "AGENTE_ETIOLOGICO": "agente_etiologico",
            }
            x_dimension = x_dimension_map.get(x_dim, x_dim.lower())

    # Recopilar todos los valores únicos del eje X (labels)
    all_x_values: list[Any] = []
    for serie in resultado.series:
        if "error" in serie:
            continue
        data = serie.get("data", [])
        for row in data:
            x_val = (
                row.get(x_dimension)
                if x_dimension
                else row.get("semana_epidemiologica")
            )
            if x_val is not None and x_val not in all_x_values:
                all_x_values.append(x_val)

    # Ordenar valores del eje X
    try:
        all_x_values.sort(
            key=lambda v: int(v)
            if isinstance(v, (int, str)) and str(v).isdigit()
            else 0
        )
    except (ValueError, TypeError):
        pass

    # Crear labels para el eje X
    labels = []
    for x_val in all_x_values:
        if x_dimension == "semana_epidemiologica":
            labels.append(f"SE {x_val}")
        else:
            labels.append(str(x_val))

    # Crear datasets (una por cada serie)
    datasets = []
    for serie in resultado.series:
        if "error" in serie:
            continue

        data = serie.get("data", [])
        if not data:
            continue

        serie_label = serie.get("serie", serie.get("slug", "Serie"))
        serie_color = serie.get("color", "#4CAF50")

        # Mapear datos de la serie a la posición correcta en el array
        data_map = {}
        for row in data:
            x_val = (
                row.get(x_dimension)
                if x_dimension
                else row.get("semana_epidemiologica")
            )
            if x_val is not None:
                data_map[x_val] = row.get("valor", 0)

        # Crear array de datos alineado con labels
        data_array = [data_map.get(x_val, 0) for x_val in all_x_values]

        datasets.append(
            {
                "label": serie_label,
                "data": data_array,
                "color": serie_color,
            }
        )

    # Construir UniversalChartSpec
    spec = {
        "id": resultado.slug,
        "title": resultado.titulo,
        "type": chart_type,
        "data": {
            "type": chart_type,
            "data": {
                "labels": labels,
                "datasets": datasets,
            },
        },
        "config": {
            "type": chart_type,
            "config": {
                "height": resultado.config_visual.get("height", 350),
                "showLegend": len(datasets) > 1,
                "showGrid": True,
                "stacked": resultado.tipo_visualizacion == "STACKED_BAR",
            },
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Crear nodo dynamicChart con spec embebido
    chart_node = {
        "type": "dynamicChart",
        "attrs": {
            "chartCode": resultado.slug,
            "title": resultado.titulo,
            "height": resultado.config_visual.get("height", 350),
            "spec": spec,
        },
    }

    nodes.append(chart_node)

    # Espacio después del chart
    nodes.append({"type": "paragraph", "content": []})

    return nodes


def _render_table_resultado(resultado: Any) -> list[dict[str, Any]]:
    """
    Renderiza un BloqueResultado como tabla TipTap nativa.
    """
    from app.domains.boletines.services.adapter import BloqueResultado

    if not isinstance(resultado, BloqueResultado):
        return []

    nodes: list[dict[str, Any]] = []

    for serie in resultado.series:
        # Si hay error en la serie, mostrar mensaje
        if "error" in serie:
            nodes.append(
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"⚠️ Error en {serie['serie']}: {serie['error']}",
                        }
                    ],
                }
            )
            continue

        data = serie.get("data", [])
        if not data:
            continue

        # Agregar nombre de la serie si hay más de una
        if len(resultado.series) > 1:
            nodes.append(
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "marks": [{"type": "bold"}],
                            "text": f"{serie['serie']}:",
                        }
                    ],
                }
            )

        # Crear tabla TipTap con los datos
        if isinstance(data, list) and len(data) > 0:
            # Obtener columnas del primer registro
            first_row = data[0]
            if isinstance(first_row, dict):
                columns = list(first_row.keys())

                # Header row
                header_cells = [
                    {
                        "type": "tableHeader",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": str(col)}],
                            }
                        ],
                    }
                    for col in columns
                ]

                # Data rows
                data_rows = []
                for row in data[:20]:  # Limitar a 20 filas
                    cells = [
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": str(row.get(col, ""))}
                                    ],
                                }
                            ],
                        }
                        for col in columns
                    ]
                    data_rows.append({"type": "tableRow", "content": cells})

                table_node = {
                    "type": "table",
                    "content": [
                        {"type": "tableRow", "content": header_cells},
                        *data_rows,
                    ],
                }
                nodes.append(table_node)

                if len(data) > 20:
                    nodes.append(
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "marks": [{"type": "italic"}],
                                    "text": f"... y {len(data) - 20} filas más",
                                }
                            ],
                        }
                    )

    return nodes


def build_context(request: GenerateDraftRequest) -> dict[str, Any]:
    """
    Construye el contexto con variables para templates.

    Args:
        request: Parámetros de generación

    Returns:
        Dict con todas las variables disponibles para reemplazo.

        Variables generadas (con ejemplos):
        - anio_epidemiologico: "2025"
        - semana_epidemiologica_actual: "45"
        - semana_epidemiologica_inicio: "1"
        - fecha_inicio_semana_epidemiologica: "04/11/2025"
        - fecha_fin_semana_epidemiologica: "10/11/2025"
        - num_semanas_analizadas: 4
    """
    # Calcular período de análisis
    semana_inicio = request.semana - request.num_semanas + 1
    anio_inicio = request.anio

    if semana_inicio < 1:
        semana_inicio += 52
        anio_inicio -= 1

    fecha_inicio, _ = get_epi_week_dates(semana_inicio, anio_inicio)
    _, fecha_fin = get_epi_week_dates(request.semana, request.anio)

    # Formato de fecha legible (DD/MM/YYYY)
    fecha_inicio_str = fecha_inicio.strftime("%d/%m/%Y")
    fecha_fin_str = fecha_fin.strftime("%d/%m/%Y")

    return {
        # Variables con nombres explícitos (nuevas)
        "anio_epidemiologico": request.anio,
        "semana_epidemiologica_actual": request.semana,
        "semana_epidemiologica_inicio": semana_inicio,
        "fecha_inicio_semana_epidemiologica": fecha_inicio_str,
        "fecha_fin_semana_epidemiologica": fecha_fin_str,
        "num_semanas_analizadas": request.num_semanas,
        # Variables internas (para queries, no para templates)
        "semana": request.semana,  # Mantener para compatibilidad con queries
        "anio": request.anio,
        "semana_inicio": semana_inicio,
        "anio_inicio": anio_inicio,
        "num_semanas": request.num_semanas,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "fecha_inicio_obj": fecha_inicio,
        "fecha_fin_obj": fecha_fin,
        "titulo_custom": request.titulo_custom,
        "eventos_seleccionados": request.eventos_seleccionados,
    }


async def resolve_tipo_eno_codigos(db: AsyncSession, codigos: list[str]) -> list[int]:
    """
    Resuelve códigos kebab-case de tipo_eno a IDs numéricos.

    Args:
        db: Sesión de base de datos
        codigos: Lista de códigos (ej: ["dengue", "fiebre-chikungunya"])

    Returns:
        Lista de IDs correspondientes
    """
    from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad

    if not codigos:
        return []

    stmt = select(col(Enfermedad.id), col(Enfermedad.slug)).where(
        col(Enfermedad.slug).in_(codigos)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    # Mapear código → id
    codigo_to_id = {row.slug: row.id for row in rows}

    # Mantener orden original y advertir sobre códigos no encontrados
    ids = []
    for codigo in codigos:
        if codigo in codigo_to_id:
            ids.append(codigo_to_id[codigo])
        else:
            logger.warning(f"Código tipo_eno no encontrado: '{codigo}'")

    return ids


async def resolve_series_config(
    db: AsyncSession,
    series_config: list[dict[str, Any]],
    agrupar_por: Optional[str],
) -> list[dict[str, Any]]:
    """
    Resuelve la configuración de series con estructura "valores".

    Estructura de serie:
    {
        "label": "Influenza A",
        "color": "#F44336",
        "valores": ["influenza-a-h1n1", "influenza-a-h3n2"]  # Se suman estos
    }

    Args:
        db: Sesión de base de datos
        series_config: Configuración de series del seed
        agrupar_por: "evento" | "agente" | None

    Returns:
        Lista de series resueltas con IDs numéricos (tipo_eno_ids) o códigos (agente_codigos)
    """
    resolved_series = []

    if not series_config:
        return resolved_series

    for serie in series_config:
        valores = serie.get("valores", [])
        label = serie.get("label", "Serie")
        color = serie.get("color", "#4CAF50")

        if not valores:
            continue

        if agrupar_por == "agente":
            # Para agentes, los valores son códigos de agente directamente
            resolved_series.append(
                {
                    "agente_codigos": valores,
                    "label": label,
                    "color": color,
                }
            )
        else:
            # Para eventos, resolver códigos a IDs
            tipo_eno_ids = await resolve_tipo_eno_codigos(db, valores)
            if tipo_eno_ids:
                resolved_series.append(
                    {
                        "tipo_eno_ids": tipo_eno_ids,
                        "label": label,
                        "color": color,
                    }
                )

    return resolved_series


async def execute_query(
    db: AsyncSession,
    query_service: BoletinQueryService,
    query_type: str,
    query_params: dict[str, Any],
    context: dict[str, Any],
    evento_id: Optional[int] = None,
) -> Any:
    """
    Ejecuta una query según el tipo configurado.

    Args:
        db: Sesión de base de datos
        query_service: Servicio de queries
        query_type: Tipo de query ("top_enos", "evento_detail", etc.)
        query_params: Parámetros adicionales de la query
        context: Contexto con variables
        evento_id: ID del evento (si aplica)

    Returns:
        Datos de la query
    """
    # ═══════════════════════════════════════════════════════════════════════════
    # Resolver códigos tipo_eno a IDs (permite usar códigos legibles en templates)
    # ═══════════════════════════════════════════════════════════════════════════
    if "tipo_eno_codigos" in query_params:
        codigos = query_params["tipo_eno_codigos"]
        if isinstance(codigos, str):
            codigos = [codigos]
        resolved_ids = await resolve_tipo_eno_codigos(db, codigos)
        query_params = query_params.copy()
        query_params["tipo_eno_ids"] = resolved_ids
        logger.info(f"Resueltos códigos {codigos} → IDs {resolved_ids}")
    if query_type == "top_enos":
        return await query_service.consultar_top_enos(
            db=db,
            limite=query_params.get("limit", 10),
            fecha_inicio=context["fecha_inicio_obj"],
            fecha_fin=context["fecha_fin_obj"],
        )

    elif query_type == "evento_detail":
        if not evento_id:
            raise ValueError("evento_id requerido para query_evento_detail")
        return await query_service.consultar_detalle_evento(
            db=db,
            evento_id=evento_id,
            fecha_inicio=context["fecha_inicio_obj"],
            fecha_fin=context["fecha_fin_obj"],
        )

    elif query_type == "capacidad_hospitalaria":
        return await query_service.consultar_capacidad_hospitalaria(
            db=db, semana=context["semana"], anio=context["anio"]
        )

    elif query_type == "virus_respiratorios":
        return await query_service.consultar_virus_respiratorios(
            db=db, semana=context["semana"], anio=context["anio"]
        )

    elif query_type == "eventos_agrupados":
        return await query_service.consultar_eventos_agrupados(
            db=db,
            tipo_evento=query_params.get("tipo_evento", "ETI"),
            semana=context["semana"],
            anio=context["anio"],
            num_semanas=query_params.get("num_semanas", 4),
        )

    elif query_type == "distribucion_edad":
        # ═══════════════════════════════════════════════════════════════════════
        # Distribución por edad (una o múltiples series, agrupado por evento o agente)
        # Usa series_config con estructura "valores" (array) para agrupar códigos
        # ═══════════════════════════════════════════════════════════════════════
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        agrupar_por = query_params.get("agrupar_por")  # "evento" | "agente" | None

        # Leer series desde config (render_config)
        render_config = query_params.get("config", {})
        series_config = (
            render_config.get("series", []) if isinstance(render_config, dict) else []
        )

        # Resolver series usando estructura con "valores"
        resolved_series = await resolve_series_config(
            db=db,
            series_config=series_config,
            agrupar_por=agrupar_por,
        )

        # Si no hay series resueltas y tenemos evento_id, crear serie simple
        if not resolved_series and evento_id:
            resolved_series = [
                {"tipo_eno_ids": [evento_id], "label": "Casos", "color": "#4CAF50"}
            ]

        logger.info(
            f"distribucion_edad: agrupar_por={agrupar_por}, {len(resolved_series)} series"
        )

        generator = ChartSpecGenerator(db)

        # Extraer todos los IDs de tipo_eno para el filtro (aplanar arrays)
        all_tipo_eno_ids = []
        for s in resolved_series:
            if s.get("tipo_eno_ids"):
                all_tipo_eno_ids.extend(s["tipo_eno_ids"])

        # Determinar fechas según periodo
        periodo = query_params.get("periodo", "semana")
        if periodo == "anual":
            anio = context.get("anio", 2024)
            fecha_desde = date(anio, 1, 1).isoformat()
            fecha_hasta = context.get("fecha_fin")
        else:
            fecha_desde = context.get("fecha_inicio")
            fecha_hasta = context.get("fecha_fin")

        filters = FiltrosGrafico(
            ids_tipo_eno=all_tipo_eno_ids
            if all_tipo_eno_ids
            else ([evento_id] if evento_id else None),
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        try:
            spec = await generator._generar_casos_por_edad(
                filtros=filters,
                configuracion=query_params.get("config"),
                configuracion_series=resolved_series if resolved_series else None,
                agrupar_por=agrupar_por,
            )
            return {"spec": spec.model_dump(by_alias=True), "chart_code": "casos_edad"}
        except Exception as e:
            logger.warning(f"Error generando spec distribucion_edad: {e}")
            return {}

    elif query_type == "distribucion_geografica":
        # Usa ChartSpecGenerator para obtener datos del mapa
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        generator = ChartSpecGenerator(db)
        filters = FiltrosGrafico(
            ids_tipo_eno=[evento_id] if evento_id else None,
            fecha_desde=context.get("fecha_inicio"),
            fecha_hasta=context.get("fecha_fin"),
        )
        try:
            spec = await generator.generar_spec(
                codigo_grafico="mapa_chubut", filtros=filters
            )
            return {"spec": spec.model_dump(by_alias=True), "chart_code": "mapa_chubut"}
        except Exception as e:
            logger.warning(f"Error generando spec distribucion_geografica: {e}")
            return {}

    elif query_type == "corredor_endemico_chart":
        # Genera spec para corredor endémico
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        generator = ChartSpecGenerator(db)
        # Para corredor anual, usar todo el año (SE 1-52)
        periodo = query_params.get("periodo", "anual")
        if periodo == "anual":
            # Corredor de todo el año - calcular fechas de SE 1 a SE actual
            anio = context.get("anio")
            if not isinstance(anio, int):
                anio = date.today().year
            semana_actual = context.get("semana", 52)
            fecha_inicio_anual, _ = get_epi_week_dates(1, anio)
            _, fecha_fin_anual = get_epi_week_dates(semana_actual, anio)
            filters = FiltrosGrafico(
                ids_tipo_eno=[evento_id] if evento_id else None,
                fecha_desde=fecha_inicio_anual.isoformat(),
                fecha_hasta=fecha_fin_anual.isoformat(),
            )
        else:
            # Corredor del período seleccionado
            filters = FiltrosGrafico(
                ids_tipo_eno=[evento_id] if evento_id else None,
                fecha_desde=context.get("fecha_inicio"),
                fecha_hasta=context.get("fecha_fin"),
            )
        try:
            spec = await generator.generar_spec(
                codigo_grafico="corredor_endemico", filtros=filters
            )
            return {
                "spec": spec.model_dump(by_alias=True),
                "chart_code": "corredor_endemico",
            }
        except Exception as e:
            logger.warning(f"Error generando spec corredor_endemico: {e}")
            return {}

    elif query_type == "comparacion_periodos":
        # Comparación del período actual vs período anterior
        if evento_id is None:
            logger.warning("comparacion_periodos: evento_id es None")
            return {}
        return await query_service.consultar_comparacion_periodos(
            db=db,
            evento_id=evento_id,
            periodo_actual=(context["fecha_inicio_obj"], context["fecha_fin_obj"]),
            periodo_anterior=_calculate_previous_period(
                context["fecha_inicio_obj"], context["fecha_fin_obj"]
            ),
        )

    elif query_type == "comparacion_anual":
        # Comparación año actual vs año anterior (acumulado hasta semana actual)
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        generator = ChartSpecGenerator(db)
        anio = context.get("anio", date.today().year)
        semana = context.get("semana", 1)

        # Generar spec de curva epidemiológica comparando años
        filters = FiltrosGrafico(
            ids_tipo_eno=[evento_id] if evento_id else None,
            anio=anio,
            semana_hasta=semana,
            comparar_anio_anterior=True,
        )
        try:
            spec = await generator.generar_spec(
                codigo_grafico="curva_epidemiologica", filtros=filters
            )
            return {
                "spec": spec.model_dump(by_alias=True),
                "chart_code": "curva_epidemiologica_comparada",
            }
        except Exception as e:
            logger.warning(f"Error generando spec comparacion_anual: {e}")
            # Fallback a datos de query service
            if evento_id is None:
                logger.warning("comparacion_anual fallback: evento_id es None")
                return {}
            return await query_service.consultar_comparacion_periodos(
                db=db,
                evento_id=evento_id,
                periodo_actual=(date(anio, 1, 1), context["fecha_fin_obj"]),
                periodo_anterior=(
                    date(anio - 1, 1, 1),
                    date(
                        anio - 1,
                        context["fecha_fin_obj"].month,
                        context["fecha_fin_obj"].day,
                    ),
                ),
            )

    elif query_type == "curva_epidemiologica":
        # ═══════════════════════════════════════════════════════════════════════
        # Curva epidemiológica (una o múltiples series, agrupado por evento o agente)
        # Usa series_config con estructura "valores" (array) para agrupar códigos
        # ═══════════════════════════════════════════════════════════════════════
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        agrupar_por = query_params.get("agrupar_por")  # "evento" | "agente" | None

        # Leer series desde config (render_config)
        render_config = query_params.get("config", {})
        series_config = (
            render_config.get("series", []) if isinstance(render_config, dict) else []
        )

        logger.info(
            f"curva_epidemiologica: render_config.series={series_config}, agrupar_por={agrupar_por}"
        )

        # Resolver series usando estructura con "valores"
        resolved_series = await resolve_series_config(
            db=db,
            series_config=series_config,
            agrupar_por=agrupar_por,
        )

        logger.info(f"curva_epidemiologica: resolved_series={resolved_series}")

        # Si no hay series resueltas y tenemos evento_id, crear serie simple
        if not resolved_series and evento_id:
            resolved_series = [
                {
                    "tipo_eno_ids": [evento_id],
                    "label": "Casos",
                    "color": "rgb(75, 192, 192)",
                }
            ]

        if not resolved_series:
            logger.warning(
                "curva_epidemiologica: No hay series válidas (series_config was empty or unresolved)"
            )
            return {}

        logger.info(
            f"curva_epidemiologica: agrupar_por={agrupar_por}, {len(resolved_series)} series"
        )
        logger.info(f"curva_epidemiologica: resolved_series={resolved_series}")

        # Extraer todos los IDs de tipo_eno para el filtro (aplanar arrays)
        all_tipo_eno_ids = []
        for s in resolved_series:
            if s.get("tipo_eno_ids"):
                all_tipo_eno_ids.extend(s["tipo_eno_ids"])

        # Determinar fechas según periodo
        periodo = query_params.get("periodo", "semana")
        if periodo == "anual":
            # Usar todo el año hasta la fecha actual del boletín
            anio = context.get("anio", 2024)
            fecha_desde = date(anio, 1, 1).isoformat()
            fecha_hasta = context.get("fecha_fin")
        else:
            # Usar las fechas del contexto (semana específica)
            fecha_desde = context.get("fecha_inicio")
            fecha_hasta = context.get("fecha_fin")

        generator = ChartSpecGenerator(db)
        filters = FiltrosGrafico(
            ids_tipo_eno=all_tipo_eno_ids
            if all_tipo_eno_ids
            else ([evento_id] if evento_id else None),
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            agrupacion_temporal=query_params.get("agrupacion_temporal", "semana"),
        )

        try:
            spec = await generator._generar_curva_epidemiologica(
                filtros=filters,
                configuracion=query_params.get("config"),
                configuracion_series=resolved_series,
                agrupar_por=agrupar_por,
            )
            return {
                "spec": spec.model_dump(by_alias=True),
                "chart_code": "curva_epidemiologica",
            }
        except Exception as e:
            logger.warning(f"Error generando spec curva_epidemiologica: {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════════════════
    # INSIGHTS AUTO-GENERADOS
    # Generan texto descriptivo basado en datos estadísticos
    # ═══════════════════════════════════════════════════════════════════════════
    elif query_type == "insight_distribucion_edad":
        from app.domains.boletines.services.insights import BoletinInsightsService

        if evento_id is None:
            logger.warning("insight_distribucion_edad: evento_id es None")
            return {"texto": ""}
        insights_service = BoletinInsightsService(db)
        return await insights_service.generar_insight_distribucion_edad(
            evento_id=evento_id,
            fecha_inicio=context["fecha_inicio_obj"],
            fecha_fin=context["fecha_fin_obj"],
            evento_nombre=context.get("nombre_evento_sanitario"),
        )

    elif query_type == "insight_distribucion_geografica":
        from app.domains.boletines.services.insights import BoletinInsightsService

        if evento_id is None:
            logger.warning("insight_distribucion_geografica: evento_id es None")
            return {"texto": ""}
        insights_service = BoletinInsightsService(db)
        return await insights_service.generar_insight_distribucion_geografica(
            evento_id=evento_id,
            fecha_inicio=context["fecha_inicio_obj"],
            fecha_fin=context["fecha_fin_obj"],
            evento_nombre=context.get("nombre_evento_sanitario"),
        )

    elif query_type == "insight_tendencia":
        from app.domains.boletines.services.insights import BoletinInsightsService

        if evento_id is None:
            logger.warning("insight_tendencia: evento_id es None")
            return {"texto": ""}
        insights_service = BoletinInsightsService(db)
        return await insights_service.generar_insight_tendencia(
            evento_id=evento_id,
            semana_actual=context["semana"],
            anio=context["anio"],
            num_semanas=query_params.get("num_semanas", context.get("num_semanas", 4)),
            evento_nombre=context.get("nombre_evento_sanitario"),
        )

    elif query_type == "insight_resumen":
        from app.domains.boletines.services.insights import BoletinInsightsService

        if evento_id is None:
            logger.warning("insight_resumen: evento_id es None")
            return {"texto": ""}
        insights_service = BoletinInsightsService(db)
        return await insights_service.generar_insight_resumen(
            evento_id=evento_id,
            fecha_inicio=context["fecha_inicio_obj"],
            fecha_fin=context["fecha_fin_obj"],
            evento_nombre=context.get("nombre_evento_sanitario"),
        )

    else:
        logger.warning(f"Query type desconocido: {query_type}")
        return {}


def render_chart_block(
    data: dict[str, Any], render_config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Renderiza un bloque de chart con el spec embebido.

    Args:
        data: Datos que incluyen {"spec": ..., "chart_code": ...}
        render_config: Configuración con título, altura, etc.
        context: Contexto con variables

    Returns:
        TipTap JSON con nodo dynamicChart
    """
    spec = data.get("spec")
    chart_code = data.get("chart_code", "unknown")
    titulo = render_config.get("titulo", f"Chart: {chart_code}")

    # Reemplazar variables Jinja2 en el título
    titulo = replace_template_variables_in_string(titulo, context)

    if not spec:
        return {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"ℹ️ {titulo}: Sin datos disponibles para generar el gráfico",
                        }
                    ],
                }
            ],
        }

    # Obtener evento_id del contexto para pasarlo al chart
    evento_id = context.get("evento_id")
    evento_ids_str = str(evento_id) if evento_id else ""

    # ═══════════════════════════════════════════════════════════════════════════
    # Caso especial: mapa_chubut genera imagen + tabla HTML nativa debajo
    # ═══════════════════════════════════════════════════════════════════════════
    if chart_code == "mapa_chubut":
        # Extraer datos de departamentos del spec
        # En el nuevo schema: spec.datos.datos.departamentos
        # Pero aquí spec es un dict porque se hizo model_dump()
        # spec["datos"]["datos"]["departamentos"]

        # Intentar acceder con la estructura nueva (datos -> datos -> departamentos)
        departamentos_data = (
            spec.get("datos", {}).get("datos", {}).get("departamentos", [])
        )
        total_casos = spec.get("datos", {}).get("datos", {}).get("total_casos", 0)

        # Ordenar por casos descendente
        departamentos_sorted = sorted(
            departamentos_data, key=lambda x: x.get("casos", 0), reverse=True
        )

        # Construir tabla TipTap nativa
        table_rows = [
            # Header row
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableHeader",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Departamento"}],
                            }
                        ],
                    },
                    {
                        "type": "tableHeader",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Casos"}],
                            }
                        ],
                    },
                    {
                        "type": "tableHeader",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Tasa/100k hab."}],
                            }
                        ],
                    },
                ],
            }
        ]

        # Data rows
        for dept in departamentos_sorted:
            table_rows.append(
                {
                    "type": "tableRow",
                    "content": [
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": dept.get("nombre", "")}
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": str(dept.get("casos", 0)),
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"{dept.get('tasa_incidencia', 0):.2f}",
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                }
            )

        content_nodes = [
            # Título del mapa
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": titulo}],
            },
            # Imagen del mapa
            {
                "type": "dynamicChart",
                "attrs": {
                    "chartCode": chart_code,
                    "eventoIds": evento_ids_str,
                    "title": titulo,
                    "spec": spec,
                    "height": render_config.get("height", 400),
                },
            },
            # Espacio
            {"type": "paragraph", "content": []},
            # Tabla HTML nativa con datos de departamentos
            {"type": "table", "content": table_rows},
            # Total de casos
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "marks": [{"type": "bold"}],
                        "text": f"Total de casos en la provincia: {total_casos}",
                    }
                ],
            },
            # Espacio después
            {"type": "paragraph", "content": []},
        ]

        logger.info("✓ Mapa + Tabla departamentos (HTML nativo) renderizados")

        return {"type": "doc", "content": content_nodes}

    # ═══════════════════════════════════════════════════════════════════════════
    # Caso normal: un solo chart
    # ═══════════════════════════════════════════════════════════════════════════
    content_nodes = [
        # Título del chart
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": titulo}],
        },
        # Chart embebido con spec y eventoIds
        {
            "type": "dynamicChart",
            "attrs": {
                "chartCode": chart_code,
                "eventoIds": evento_ids_str,
                "title": titulo,
                "spec": spec,
                "height": render_config.get("height", 400),
            },
        },
        # Espacio después
        {"type": "paragraph", "content": []},
    ]

    logger.info(f"✓ Chart renderizado: {chart_code}")

    return {"type": "doc", "content": content_nodes}


def render_block(
    renderer: BoletinBlockRenderer,
    render_type: str,
    data: Any,
    render_config: dict[str, Any],
    context: dict[str, Any],
    evento_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Renderiza un bloque según el tipo configurado.

    Args:
        renderer: Servicio de renderizado
        render_type: Tipo de render ("table", "evento_section", etc.)
        data: Datos a renderizar
        render_config: Configuración de renderizado
        context: Contexto con variables (semana, anio, num_semanas, etc.)
        evento_id: ID del evento (si aplica)

    Returns:
        TipTap JSON del bloque renderizado
    """
    if render_type == "table":
        # Determinar qué tipo de tabla
        if "top_enos" in render_config.get("titulo", "").lower():
            return renderer.render_top_enos_table(data, render_config, context)
        else:
            # Tabla genérica
            return renderer.render_top_enos_table(data, render_config, context)

    elif render_type == "evento_section":
        return renderer.render_evento_section(data, render_config, context)

    elif render_type == "capacidad_table":
        return renderer.render_capacidad_table(data, render_config, context)

    elif render_type == "virus_table":
        return renderer.render_virus_table(data, render_config, context)

    elif render_type == "eventos_agrupados_table":
        return renderer.render_eventos_agrupados_table(data, render_config, context)

    elif render_type == "corredor_endemico":
        # Alias para eventos_agrupados_table
        return renderer.render_eventos_agrupados_table(data, render_config, context)

    elif render_type == "chart":
        # Renderiza un chart embebido con el spec
        return render_chart_block(data, render_config, context)

    elif render_type == "insight_text":
        # Renderiza un insight como párrafo de texto
        return render_insight_text(data, render_config, context)

    else:
        logger.warning(f"Render type desconocido: {render_type}")
        return {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": f"⚠️ Bloque no renderizado: {render_type}"}
            ],
        }


def render_insight_text(
    data: dict[str, Any], render_config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Renderiza un insight como párrafo de texto TipTap.

    Args:
        data: Datos del insight con campo "texto"
        render_config: Configuración con título opcional
        context: Contexto con variables

    Returns:
        TipTap JSON con párrafo de texto
    """
    texto = data.get("texto", "")

    if not texto:
        return {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "ℹ️ Sin datos disponibles para generar insight.",
                        }
                    ],
                }
            ],
        }

    content_nodes = []

    # Agregar título si está configurado
    titulo = render_config.get("titulo")
    if titulo:
        titulo = replace_template_variables_in_string(titulo, context)
        content_nodes.append(
            {
                "type": "heading",
                "attrs": {"level": render_config.get("nivel_titulo", 4)},
                "content": [{"type": "text", "text": titulo}],
            }
        )

    # Agregar el texto del insight como párrafo
    content_nodes.append(
        {"type": "paragraph", "content": [{"type": "text", "text": texto}]}
    )

    logger.info(f"✓ Insight renderizado: {texto[:50]}...")

    return {"type": "doc", "content": content_nodes}


async def save_boletin_instance(
    db: AsyncSession,
    request: GenerateDraftRequest,
    content: dict[str, Any],
    context: dict[str, Any],
    current_user: Optional[User],
) -> BoletinInstance:
    """
    Guarda la instancia del boletín en DB.

    Args:
        db: Sesión de base de datos
        request: Parámetros de generación
        content: TipTap JSON generado
        context: Contexto con variables
        current_user: Usuario actual

    Returns:
        BoletinInstance guardado
    """
    titulo = (
        request.titulo_custom
        or f"Boletín Epidemiológico SE {request.semana}/{request.anio}"
    )

    boletin = BoletinInstance(
        name=titulo,
        template_id=None,  # None para boletines generados automáticamente
        parameters={
            "semana": request.semana,
            "anio": request.anio,
            "num_semanas": request.num_semanas,
            "eventos_seleccionados": [
                e.tipo_eno_id for e in request.eventos_seleccionados
            ],
            "generado_automaticamente": True,
            "version": "2.0",  # Nueva versión con sistema configurable
        },
        template_snapshot={
            "tipo": "generacion_configurable_v2",
            "periodo": {
                "semana_inicio": context["semana_inicio"],
                "semana_fin": context["semana"],
                "anio": context["anio"],
                "fecha_inicio": context["fecha_inicio"],
                "fecha_fin": context["fecha_fin"],
            },
        },
        content=json.dumps(content),  # Guardar como JSON string
    )

    if current_user:
        boletin.generated_by = current_user.id

    db.add(boletin)
    await db.commit()
    await db.refresh(boletin)

    return boletin
