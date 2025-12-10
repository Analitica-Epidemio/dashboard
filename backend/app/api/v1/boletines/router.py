"""
Router para endpoints de boletines epidemiológicos
"""

from typing import List

from fastapi import APIRouter

from app.api.v1.boletines import config, instances_crud, preview, templates_crud
from app.api.v1.boletines.charts_disponibles import (
    ChartsDisponiblesResponse,
    get_charts_disponibles,
)
from app.api.v1.boletines.generate_draft import generate_draft
from app.api.v1.boletines.preview import (
    AgenteDisponible,
    CasoEpidemiologicoDisponible,
    SectionPreviewResponse,
)
from app.api.v1.boletines.schemas import (
    BoletinInstanceResponse,
    BoletinTemplateConfigResponse,
    BoletinTemplateResponse,
    GenerateDraftResponse,
    SeccionesConfigResponse,
)
from app.api.v1.boletines.secciones_config import get_secciones_config
from app.core.schemas.response import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/boletines", tags=["Boletines"])


# ============================================================================
# Templates Endpoints
# ============================================================================

router.add_api_route(
    "/templates",
    templates_crud.create_template,
    methods=["POST"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="create_boletin_template",
    summary="Crear template de boletín",
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates",
    templates_crud.list_templates,
    methods=["GET"],
    response_model=SuccessResponse[List[BoletinTemplateResponse]],
    name="list_boletin_templates",
    summary="Listar templates de boletines",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.get_template,
    methods=["GET"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="get_boletin_template",
    summary="Obtener template por ID",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.update_template,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="update_boletin_template",
    summary="Actualizar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.delete_template,
    methods=["DELETE"],
    response_model=SuccessResponse[dict],
    name="delete_boletin_template",
    summary="Eliminar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}/duplicate",
    templates_crud.duplicate_template,
    methods=["POST"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="duplicate_boletin_template",
    summary="Duplicar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Instances Endpoints
# ============================================================================

router.add_api_route(
    "/instances",
    instances_crud.create_instance,
    methods=["POST"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="create_boletin_instance",
    summary="Crear instancia de boletín",
    description="Crea una instancia pendiente. El PDF se genera en un paso posterior.",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances",
    instances_crud.list_instances,
    methods=["GET"],
    response_model=SuccessResponse[List[BoletinInstanceResponse]],
    name="list_boletin_instances",
    summary="Listar instancias de boletines",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}",
    instances_crud.get_instance,
    methods=["GET"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="get_boletin_instance",
    summary="Obtener instancia por ID",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}",
    instances_crud.delete_instance,
    methods=["DELETE"],
    response_model=SuccessResponse[dict],
    name="delete_boletin_instance",
    summary="Eliminar instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}/content",
    instances_crud.update_instance_content,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="update_boletin_instance_content",
    summary="Actualizar contenido de instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}/export-pdf",
    instances_crud.generate_instance_pdf,
    methods=["POST"],
    name="generate_boletin_instance_pdf",
    summary="Generar y descargar PDF de instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        400: {"model": ErrorResponse, "description": "Sin contenido para generar"},
        500: {"model": ErrorResponse, "description": "Error generando PDF"},
    },
)


# ============================================================================
# New automatic generation endpoint
# ============================================================================

router.add_api_route(
    "/generate-draft",
    generate_draft,
    methods=["POST"],
    response_model=SuccessResponse[GenerateDraftResponse],
    name="generate_draft_boletin",
    summary="Generar borrador de boletín automático basado en analytics",
    description="Genera un boletín epidemiológico automático usando datos de analytics y snippets",
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Template Configuration Endpoints (Singleton - BoletinTemplateConfig)
# ============================================================================

router.add_api_route(
    "/config",
    config.get_template_config,
    methods=["GET"],
    response_model=SuccessResponse[BoletinTemplateConfigResponse],
    name="get_boletin_template_config",
    summary="Obtener configuración del template de boletines",
    description="Obtiene la configuración singleton (id=1) del template de boletines",
    responses={
        404: {"model": ErrorResponse, "description": "Configuración no encontrada"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/config/static-content",
    config.update_static_content,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinTemplateConfigResponse],
    name="update_static_content",
    summary="Actualizar contenido estático del template",
    description="Actualiza el campo static_content_template (TipTap JSON)",
    responses={
        404: {"model": ErrorResponse, "description": "Configuración no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos (requiere admin)"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/config/event-section-template",
    config.update_event_section_template,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinTemplateConfigResponse],
    name="update_event_section_template",
    summary="Actualizar template de sección de evento",
    description="Actualiza el campo event_section_template (TipTap JSON que se repite por cada evento)",
    responses={
        404: {"model": ErrorResponse, "description": "Configuración no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos (requiere admin)"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Preview Endpoints (for section data preview in the generator UI)
# ============================================================================

router.add_api_route(
    "/preview/evento",
    preview.get_evento_preview,
    methods=["GET"],
    response_model=SuccessResponse[SectionPreviewResponse],
    name="preview_evento",
    summary="Preview genérico de datos para cualquier evento",
    description="Recibe el código de un Enfermedad o GrupoDeEnfermedades y genera un resumen de datos",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "CasoEpidemiologico no encontrado",
        },
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/preview/eventos-disponibles",
    preview.list_available_eventos,
    methods=["GET"],
    response_model=SuccessResponse[List[CasoEpidemiologicoDisponible]],
    name="list_available_eventos",
    summary="Listar eventos disponibles para preview",
    description="Retorna todos los Enfermedad y GrupoDeEnfermedades con código para usar en el selector",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/preview/agentes-disponibles",
    preview.list_available_agentes,
    methods=["GET"],
    response_model=SuccessResponse[List[AgenteDisponible]],
    name="list_available_agentes",
    summary="Listar agentes etiológicos disponibles",
    description="Retorna todos los agentes etiológicos activos para usar en selectores de bloques dinámicos",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Secciones y Bloques Configuration Endpoints
# ============================================================================

router.add_api_route(
    "/secciones-config",
    get_secciones_config,
    methods=["GET"],
    response_model=SuccessResponse[SeccionesConfigResponse],
    name="get_secciones_config",
    summary="Obtener configuración de secciones y bloques",
    description="""
    Retorna la configuración de todas las secciones y bloques activos del boletín.

    Incluye información detallada sobre:
    - Qué métricas se consultan
    - Qué rangos temporales se usan (con ejemplos concretos)
    - Tipo de visualización de cada bloque

    Usar los parámetros `semana` y `anio` para ver ejemplos de rangos
    para una semana de referencia específica.
    """,
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Charts Disponibles (migrado de api/v1/charts)
# ============================================================================

router.add_api_route(
    "/charts-disponibles",
    get_charts_disponibles,
    methods=["GET"],
    response_model=SuccessResponse[ChartsDisponiblesResponse],
    name="get_charts_disponibles",
    summary="Obtener charts disponibles para boletines",
    description="Retorna lista de charts que pueden insertarse en boletines",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# TODO: Agregar endpoints para:
# - POST /instances/{instance_id}/generate-pdf (generar PDF de instancia)
# - GET /instances/{instance_id}/download (descargar PDF)
# - GET /instances/{instance_id}/preview (preview HTML)
